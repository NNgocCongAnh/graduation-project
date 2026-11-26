"""Automated rate-limit & timestamp-aware runner for remaining thesis benchmarks.

Completes the two remaining partial runs cleanly without fallback pollution:
  1. benchmarks/results/benchmark_gpt-4o.json -> 30/30 (10 runs per theme, --no-fallback)
  2. benchmarks/results/solver_benchmark.json -> 20/20 (blind ClientCaseDossier solving)

When HTTP 429 / quota exhaustion is hit (either immediately on an explicit rate-limit
response or after `--max-consecutive-errors` consecutive failures), this script:
  - Parses exact reset timestamps or relative durations (`reset after Xm Ys`,
    `retry in Xs`, ISO-8601 UTC timestamps, or daily Gemini RPD reset at
    00:05 America/Los_Angeles) when available.
  - Otherwise waits the configured cooldown (1-2 hours, e.g. 75 min for gpt-4o
    or 90 min / Pacific midnight for Gemini Free Tier), printing the exact local
    wall-clock wake-up timestamp before sleeping and resuming from checkpoints.
  - Refuses to save fallback-sample or wrong-model runs into target JSON files.
  - Runs build_benchmark_summary() and verify_results.py when complete.

Usage:
    python benchmarks/scripts/auto_complete_benchmarks.py --dry-run
    python benchmarks/scripts/auto_complete_benchmarks.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "detective-backend"
SCRIPTS_DIR = ROOT_DIR / "benchmarks" / "scripts"
RESULTS_DIR = ROOT_DIR / "benchmarks" / "results"
LOG_PATH = ROOT_DIR / "benchmarks" / "auto_complete.log"

for _p in (str(BACKEND_DIR), str(SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_env_file = BACKEND_DIR / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file, override=False)
    except Exception:
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _s = _line.strip()
            if _s and not _s.startswith("#") and "=" in _s:
                _k, _v = _s.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

from llm_service import CaseGeneratorService  # noqa: E402
from benchmark_runner import (  # noqa: E402
    BENCHMARK_THEMES,
    build_benchmark_summary,
    evaluate_single_trial,
)
from solver_agent import run_solver_benchmark  # noqa: E402


RATE_LIMIT_KEYWORDS = (
    "429",
    "rate limit",
    "rate_limit",
    "too many requests",
    "quota",
    "resource_exhausted",
    "exceeded your current quota",
)
DAILY_QUOTA_KEYWORDS = ("rpd", "per day", "per_day", "daily", "requests per day")


def setup_logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("auto_complete")
    log.setLevel(logging.INFO)
    if not log.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(fh)
        log.addHandler(sh)
    return log


def is_rate_limit_error(msg: str) -> bool:
    low = (msg or "").lower()
    return any(k in low for k in RATE_LIMIT_KEYWORDS)


def seconds_until_pacific_midnight(now_local: Optional[datetime] = None, buffer_sec: int = 300) -> float:
    """Return seconds until next 00:05 America/Los_Angeles (Gemini Free Tier RPD reset)."""
    pt = ZoneInfo("America/Los_Angeles")
    now_pt = (now_local or datetime.now().astimezone()).astimezone(pt)
    next_midnight_pt = (now_pt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    target_pt = next_midnight_pt + timedelta(seconds=buffer_sec)
    return max(60.0, (target_pt - now_pt).total_seconds())


def parse_wait_seconds(
    err_msg: str,
    default_wait_mins: int,
    prefer_pacific_midnight: bool = False,
    now_local: Optional[datetime] = None,
) -> tuple[float, str]:
    """Determine exact sleep seconds from error timestamps/durations or fallback cooldown."""
    now = now_local or datetime.now().astimezone()
    low = (err_msg or "").lower()

    # 1. Explicit ISO-8601 UTC timestamp (e.g. 2026-11-25T18:00:00Z)
    m_iso = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)", err_msg or "")
    if m_iso:
        try:
            iso_str = m_iso.group(1).replace("Z", "+00:00")
            reset_utc = datetime.fromisoformat(iso_str).astimezone(timezone.utc)
            delta = (reset_utc - now.astimezone(timezone.utc)).total_seconds() + 15.0
            if 60.0 <= delta <= 86400.0:
                return delta, f"ISO timestamp ({m_iso.group(1)})"
        except Exception:
            pass

    # 2. Explicit relative H/M/S durations (e.g. "reset after 1h 12m 5s", "retry in 58m", "Retry-After: 3600")
    m_hms = re.search(r"(?:reset after|try again in|retry in|wait)\s+(?:(\d+)\s*h\s*)?(?:(\d+)\s*m(?:in(?:ute)?s?)?\s*)?(?:(\d+(?:\.\d+)?)\s*s)?", low)
    if m_hms and any(m_hms.groups()):
        hrs = int(m_hms.group(1) or 0)
        mins = int(m_hms.group(2) or 0)
        secs = float(m_hms.group(3) or 0)
        total = hrs * 3600 + mins * 60 + secs
        if total >= 30.0:
            wait_s = min(max(total + 15.0, 60.0), 86400.0)
            return wait_s, f"API reset window ({hrs}h {mins}m {secs:.0f}s)"

    m_ra = re.search(r"retry[-_\s]?after[:=\s]+(\d+)", low)
    if m_ra:
        val = float(m_ra.group(1))
        if val >= 30.0:
            return min(val + 15.0, 86400.0), f"Retry-After header ({val:.0f}s)"

    # 3. Daily RPD reset detection (Gemini Free Tier)
    if prefer_pacific_midnight and any(k in low for k in DAILY_QUOTA_KEYWORDS):
        wait_s = seconds_until_pacific_midnight(now)
        return wait_s, "Gemini daily quota reset (00:05 America/Los_Angeles)"

    # 4. Default configurable cooldown (1-2 hours)
    wait_s = max(60.0, default_wait_mins * 60.0)
    return wait_s, f"cooldown mặc định ({default_wait_mins} phút)"


async def sleep_until_next_window(wait_secs: float, reason: str, log: logging.Logger) -> None:
    now = datetime.now().astimezone()
    wake_dt = now + timedelta(seconds=wait_secs)
    log.warning(
        "[WAIT] %s | Nghỉ %.1f phút | Dự kiến chạy tiếp lúc: %s",
        reason,
        wait_secs / 60.0,
        wake_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
    )
    remaining = wait_secs
    heartbeat = 900.0  # log progress every 15 minutes
    while remaining > 0:
        chunk = min(remaining, heartbeat)
        await asyncio.sleep(chunk)
        remaining -= chunk
        if remaining > 30:
            log.info(
                "[WAIT] Còn %.1f phút (chạy lại lúc %s)...",
                remaining / 60.0,
                wake_dt.strftime("%H:%M:%S"),
            )


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def count_gpt4o_progress(path: Path, model: str, trials_per_theme: int) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    runs: List[Dict[str, Any]] = []
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            runs = [
                r for r in loaded
                if r.get("model") == model
                and not r.get("used_fallback_sample")
                and not r.get("fallback_triggered")
                and set(r.get("agent_models", {}).values()).issubset({model})
            ]
    missing: Dict[str, int] = {}
    for theme in BENCHMARK_THEMES:
        have = sum(1 for r in runs if r.get("theme") == theme)
        need = max(0, trials_per_theme - have)
        if need > 0:
            missing[theme] = need
    return runs, missing


async def complete_gpt4o(args: argparse.Namespace, log: logging.Logger) -> None:
    out_path = RESULTS_DIR / "benchmark_gpt-4o.json"
    model = args.gpt4o_model
    os.environ["DISABLE_AGENT_FALLBACK"] = "1"
    os.environ["AGENT_MAX_429_ATTEMPTS"] = str(args.agent_max_429_attempts)

    consecutive_errors = 0
    while True:
        runs, missing = count_gpt4o_progress(out_path, model, args.gpt4o_trials_per_theme)
        total_target = args.gpt4o_trials_per_theme * len(BENCHMARK_THEMES)
        if not missing:
            log.info("[GPT-4o] Đã đủ %d/%d lượt sạch tại %s.", len(runs), total_target, out_path.name)
            build_benchmark_summary()
            return

        log.info("[GPT-4o] Hiện có %d/%d lượt sạch. Còn thiếu: %s", len(runs), total_target, missing)
        service = CaseGeneratorService(model=model)
        hit_cooldown = False

        for theme, need_count in missing.items():
            for _ in range(need_count):
                next_idx = len(runs) + 1
                log.info("[GPT-4o] Đang chạy lượt %02d/%02d (%s)...", next_idx, total_target, theme)
                res = await evaluate_single_trial(
                    service=service,
                    theme=theme,
                    enable_post_processing=True,
                    enable_patch_repair=True,
                    mode="pipeline",
                    max_retries=2,
                )
                res["model"] = model
                res["trial"] = next_idx

                err_str = res.get("error") or ""
                used_fb = bool(res.get("used_fallback_sample")) or bool(res.get("fallback_triggered"))
                used_models = set(res.get("agent_models", {}).values())
                valid_primary = not used_fb and used_models == {model} and bool(res.get("json_valid"))

                if valid_primary:
                    consecutive_errors = 0
                    runs.append(res)
                    atomic_write_json(out_path, runs)
                    log.info(
                        "[GPT-4o] -> OK lượt %02d/%02d | logic=%s | patch=%d | %.2fs",
                        next_idx,
                        total_target,
                        res.get("logic_valid"),
                        res.get("patch_retries", 0),
                        res.get("latency_sec", 0.0),
                    )
                    await asyncio.sleep(args.gpt4o_delay)
                else:
                    consecutive_errors += 1
                    log.warning(
                        "[GPT-4o] Lượt lỗi (%d/%d liên tiếp, không lưu): fallback=%s models=%s err=%s",
                        consecutive_errors,
                        args.max_consecutive_errors,
                        used_fb,
                        list(used_models),
                        err_str[:220],
                    )
                    if is_rate_limit_error(err_str) or consecutive_errors >= args.max_consecutive_errors:
                        wait_s, reason = parse_wait_seconds(
                            err_str,
                            default_wait_mins=args.gpt4o_wait_mins,
                            prefer_pacific_midnight=False,
                        )
                        await sleep_until_next_window(wait_s, f"GPT-4o: {reason}", log)
                        consecutive_errors = 0
                        hit_cooldown = True
                        break
                    await asyncio.sleep(10.0)
            if hit_cooldown:
                break


def count_solver_progress(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return len(data.get("cases", []))
    except Exception:
        return 0


async def complete_solver(args: argparse.Namespace, log: logging.Logger) -> None:
    out_path = RESULTS_DIR / "solver_benchmark.json"
    os.environ["DISABLE_AGENT_FALLBACK"] = "1"
    os.environ["AGENT_MAX_429_ATTEMPTS"] = str(args.agent_max_429_attempts)

    consecutive_errors = 0
    while True:
        done_n = count_solver_progress(out_path)
        if done_n >= args.solver_target:
            log.info("[Solver] Đã đủ %d/%d ca tại %s.", done_n, args.solver_target, out_path.name)
            return

        log.info("[Solver] Hiện có %d/%d ca. Tiếp tục chạy với solver=%s, generator=%s...", done_n, args.solver_target, args.solver_model, args.solver_generator_model)
        try:
            await run_solver_benchmark(
                api_base=args.api_base,
                api_key=os.getenv("LLM_API_KEY", ""),
                model=args.solver_model,
                target_cases_count=args.solver_target,
                output_path=str(out_path),
                use_db=False,
                delay=args.solver_delay,
                generator_model=args.solver_generator_model,
                raise_on_rate_limit=True,
            )
            consecutive_errors = 0
        except Exception as exc:
            after_n = count_solver_progress(out_path)
            if after_n > done_n:
                consecutive_errors = 0
            consecutive_errors += 1
            err_str = str(exc)
            log.warning(
                "[Solver] Dừng ở %d/%d ca (lỗi liên tiếp %d/%d): %s",
                after_n,
                args.solver_target,
                consecutive_errors,
                args.max_consecutive_errors,
                err_str[:250],
            )
            if is_rate_limit_error(err_str) or consecutive_errors >= args.max_consecutive_errors:
                wait_s, reason = parse_wait_seconds(
                    err_str,
                    default_wait_mins=args.solver_wait_mins,
                    prefer_pacific_midnight=args.wait_pacific_midnight,
                )
                await sleep_until_next_window(wait_s, f"Solver: {reason}", log)
                consecutive_errors = 0
            else:
                await asyncio.sleep(15.0)


async def async_main(args: argparse.Namespace, log: logging.Logger) -> int:
    gpt4o_path = RESULTS_DIR / "benchmark_gpt-4o.json"
    solver_path = RESULTS_DIR / "solver_benchmark.json"

    runs, missing = count_gpt4o_progress(gpt4o_path, args.gpt4o_model, args.gpt4o_trials_per_theme)
    solver_n = count_solver_progress(solver_path)

    log.info("=== TRẠNG THÁI HIỆN TẠI ===")
    log.info("  1. %s: %d/%d lượt sạch (thiếu: %s)", gpt4o_path.name, len(runs), args.gpt4o_trials_per_theme * len(BENCHMARK_THEMES), missing or "Không")
    log.info("  2. %s: %d/%d ca", solver_path.name, solver_n, args.solver_target)
    log.info(
        "  Cấu hình chờ: max_consecutive_errors=%d | gpt4o_wait=%dm | solver_wait=%dm | pacific_midnight=%s",
        args.max_consecutive_errors,
        args.gpt4o_wait_mins,
        args.solver_wait_mins,
        args.wait_pacific_midnight,
    )

    if args.dry_run:
        log.info("[DRY-RUN] Thoát không gọi API.")
        return 0

    if not os.getenv("LLM_API_KEY", "").strip():
        log.warning("Biến môi trường LLM_API_KEY đang trống; giả định gateway cục bộ không yêu cầu key.")

    if args.only in ("all", "gpt4o"):
        await complete_gpt4o(args, log)
    if args.only in ("all", "solver"):
        await complete_solver(args, log)

    build_benchmark_summary()
    log.info("[VERIFY] Chạy benchmarks/scripts/verify_results.py...")
    proc = subprocess.run([sys.executable, str(SCRIPTS_DIR / "verify_results.py")], cwd=str(ROOT_DIR))
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-complete remaining thesis benchmarks with smart rate-limit waits")
    parser.add_argument("--only", choices=["all", "gpt4o", "solver"], default="all")
    parser.add_argument("--api-base", default=os.getenv("LLM_API_BASE", "http://localhost:20128/v1"))
    parser.add_argument("--gpt4o-model", default="gh/gpt-4o")
    parser.add_argument("--gpt4o-trials-per-theme", type=int, default=10)
    parser.add_argument("--gpt4o-delay", type=float, default=15.0)
    parser.add_argument("--gpt4o-wait-mins", type=int, default=75, help="Fallback wait minutes when gpt-4o hits 429 without explicit reset timestamp")
    parser.add_argument("--solver-model", default="gemini/gemini-3-flash-preview")
    parser.add_argument("--solver-generator-model", default="gh/gpt-4o-mini", help="Model used to generate cases for Solver (preserves Gemini RPD quota)")
    parser.add_argument("--solver-target", type=int, default=20)
    parser.add_argument("--solver-delay", type=float, default=6.0)
    parser.add_argument("--solver-wait-mins", type=int, default=90, help="Fallback wait minutes when Solver hits 429/quota")
    parser.add_argument("--wait-pacific-midnight", action="store_true", help="Wait until 00:05 America/Los_Angeles when daily RPD quota error is detected")
    parser.add_argument("--max-consecutive-errors", type=int, default=2, help="Sleep after N consecutive non-429 errors")
    parser.add_argument("--agent-max-429-attempts", type=int, default=2, help="Inner 429 retries per agent call before handing back to outer cooldown")
    parser.add_argument("--dry-run", action="store_true", help="Inspect remaining counts and exit")
    args = parser.parse_args()

    log = setup_logger()
    rc = asyncio.run(async_main(args, log))
    sys.exit(rc)


if __name__ == "__main__":
    main()
