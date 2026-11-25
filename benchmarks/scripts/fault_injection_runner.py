"""Controlled Fault Injection Experiment Runner (RQ3: Local Patch Repair Evaluation).

Evaluates the neuro-symbolic localized repair mechanism under adversarial conditions:
1. Injects 4 archetypal violation categories into validated baseline dossiers:
   - Cat 1: Forensic TOD Physics / Crime Time Out-of-Window (ViolationType.CRIME_TIME_OUTSIDE_TOD / TOD_PHYSICS)
   - Cat 2: Duplicate Suspect Identifier / Culprit Mismatch (ViolationType.DUPLICATE_ID / MULTIPLE_CULPRITS)
   - Cat 3: Missing Crucial Clue / Unbroken Alibi (ViolationType.NO_CRUCIAL_CLUE / ALIBI_UNBROKEN)
   - Cat 4: Referential Integrity / Foreign Key Schema Error (ViolationType.SCHEMA_ERROR)
2. Evaluates Local Patch Repair vs Full Regeneration across 3 empirical metrics:
   - Repair Success Rate (% cases returning to valid state) with 95% Wilson CI
   - Real API Token Footprint (Prompt, Completion, Total) vs Full Regeneration (~18,250 tokens)
   - Repair Latency (P50, P95 via linear interpolation, Mean) vs Full Regeneration (~20.45s)
"""

import os
import sys
import copy
import json
import time
import math
import random
import asyncio
import sqlite3
import argparse
from typing import List, Dict, Any, Tuple, Optional
from openai import AsyncOpenAI

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add detective-backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "detective-backend"))

from models import CaseDossier, Suspect, Evidence, ForensicData, GroundTruth, ViolationType
from validator import (
    validate_case_diagnostics,
    apply_henssge_tod_window,
    robust_time_to_minutes,
    minutes_to_hhmm,
)
from agents import OutlineAgent, CharacterAgent, ClueAgent


# Full Regeneration baseline metrics (from empirical N=30 benchmark of gh/gpt-4o-mini)
FULL_REGEN_TOKENS = 18250.0
FULL_REGEN_LATENCY_P50 = 20.45


def calc_wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% Wilson score confidence interval."""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    z = 1.96
    denom = 1.0 + (z ** 2) / n
    center = p + (z ** 2) / (2.0 * n)
    radicand = (p * (1.0 - p) / n) + ((z ** 2) / (4.0 * (n ** 2)))
    spread = z * math.sqrt(max(0.0, radicand))
    low = max(0.0, (center - spread) / denom)
    high = min(1.0, (center + spread) / denom)
    return (round(low * 100.0, 2), round(high * 100.0, 2))


def calc_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile using linear interpolation."""
    if not data:
        return 0.0
    sorted_d = sorted(data)
    n = len(sorted_d)
    if n == 1:
        return sorted_d[0]
    idx = (n - 1) * percentile
    low = int(idx)
    high = min(low + 1, n - 1)
    weight = idx - low
    return round(sorted_d[low] * (1.0 - weight) + sorted_d[high] * weight, 2)


def load_valid_baseline_dossiers() -> List[CaseDossier]:
    """Load valid dossiers from SQLite database and cases/ directory."""
    db_path = os.path.join(os.path.dirname(__file__), "detective.db")
    valid_dossiers: List[CaseDossier] = []

    if os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        rows = cur.execute("SELECT case_id, dossier_json FROM cases").fetchall()
        for cid, djson in rows:
            try:
                data = json.loads(djson)
                case = CaseDossier.model_validate(data)
                diag = validate_case_diagnostics(case)
                if diag.is_valid:
                    valid_dossiers.append(case)
            except Exception:
                pass
        con.close()

    if not valid_dossiers:
        # Fallback to cases/ directory
        cases_dir = os.path.join(os.path.dirname(__file__), "cases")
        for fn in os.listdir(cases_dir):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(cases_dir, fn), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    case = CaseDossier.model_validate(data)
                    if validate_case_diagnostics(case).is_valid:
                        valid_dossiers.append(case)
                except Exception:
                    pass

    print(f"[DataLoader] Loaded {len(valid_dossiers)} verified clean baseline dossiers.")
    return valid_dossiers


# ---------------------------------------------------------------------------
# Controlled Fault Injection Functions
# ---------------------------------------------------------------------------

def inject_tod_fault(case: CaseDossier, trial_idx: int) -> Tuple[CaseDossier, str]:
    """Cat 1: Injects Henssge TOD physics / crime time violation."""
    corrupted = copy.deepcopy(case)
    if trial_idx % 2 == 0:
        # Shift actual crime time 5 hours into the future (outside Henssge window)
        orig_time = corrupted.ground_truth.actual_crime_time or "21:30"
        m = robust_time_to_minutes(orig_time) or 1290
        bad_m = (m + 300) % 1440
        corrupted.ground_truth.actual_crime_time = f"{bad_m // 60:02d}:{bad_m % 60:02d}"
        desc = f"Shifted crime time from {orig_time} to {corrupted.ground_truth.actual_crime_time} (+5h outside TOD)"
    else:
        # Invalidate body temperature (unphysical cooling: feverish corpse or equal to ambient)
        corrupted.victim.forensic_data.body_temp = 38.6
        desc = "Set body temperature to 38.6C (warmer than living body, violating Henssge model)"
    return corrupted, desc


def inject_duplicate_id_fault(case: CaseDossier, trial_idx: int) -> Tuple[CaseDossier, str]:
    """Cat 2: Injects duplicate suspect ID or culprit mismatch."""
    corrupted = copy.deepcopy(case)
    if trial_idx % 2 == 0:
        # Duplicate suspect ID: set suspect 1's ID to suspect 0's ID
        if len(corrupted.suspects) >= 2:
            orig_id = corrupted.suspects[1].id
            corrupted.suspects[1].id = corrupted.suspects[0].id
            desc = f"Corrupted suspect[1] id from '{orig_id}' to duplicate '{corrupted.suspects[0].id}'"
        else:
            corrupted.suspects[0].id = "SUSP-DUP"
            desc = "Corrupted suspect ID to duplicate"
    else:
        # Multiple culprits: flag an innocent suspect as culprit too
        innocents = [s for s in corrupted.suspects if not s.is_culprit]
        if innocents:
            innocents[0].is_culprit = True
            desc = f"Flagged innocent suspect '{innocents[0].id}' as second culprit (multiple culprits)"
        else:
            corrupted.suspects[1].id = corrupted.suspects[0].id
            desc = "Duplicate suspect ID"
    return corrupted, desc


def inject_crucial_clue_fault(case: CaseDossier, trial_idx: int) -> Tuple[CaseDossier, str]:
    """Cat 3: Injects missing crucial clue or unbroken alibi."""
    corrupted = copy.deepcopy(case)
    if trial_idx % 2 == 0:
        # Remove crucial flag from all evidences
        for ev in corrupted.evidences:
            ev.is_crucial = False
        desc = "Disabled is_crucial flag on all evidences (no crucial clue exists)"
    else:
        # Remove crucial clues linked to culprit, leaving culprit alibi unbroken
        culprit_id = corrupted.ground_truth.culprit_id
        for ev in corrupted.evidences:
            if ev.linked_suspect_id == culprit_id or ev.is_crucial:
                ev.is_crucial = False
                ev.linked_suspect_id = None
        desc = f"Unlinked all crucial clues from culprit '{culprit_id}' (alibi unbroken)"
    return corrupted, desc


def inject_foreign_key_fault(case: CaseDossier, trial_idx: int) -> Tuple[CaseDossier, str]:
    """Cat 4: Injects foreign key / referential integrity schema error."""
    corrupted = copy.deepcopy(case)
    if trial_idx % 2 == 0:
        # Link an evidence to a non-existent suspect
        corrupted.evidences[0].linked_suspect_id = "SUSP-GHOST-99"
        desc = "Set evidence[0].linked_suspect_id to non-existent 'SUSP-GHOST-99'"
    else:
        # Link a crucial evidence to an innocent suspect (violating innocent protection)
        culprit_id = corrupted.ground_truth.culprit_id
        innocents = [s for s in corrupted.suspects if s.id != culprit_id]
        if innocents:
            corrupted.evidences[0].is_crucial = True
            corrupted.evidences[0].is_red_herring = False
            corrupted.evidences[0].linked_suspect_id = innocents[0].id
            desc = f"Linked crucial evidence[0] to innocent suspect '{innocents[0].id}' (innocent incrimination)"
        else:
            corrupted.evidences[0].linked_suspect_id = "SUSP-INVALID"
            desc = "Set evidence linked_suspect_id to invalid foreign key"
    return corrupted, desc


# ---------------------------------------------------------------------------
# Experiment Runner
# ---------------------------------------------------------------------------

async def run_fault_injection_experiment(
    api_base: str = "http://localhost:20128/v1",
    api_key: str = "",
    model: str = "gh/gpt-4o-mini",
    trials_per_cat: int = 20,
    output_path: str = "detective-backend/fault_injection_results.json"
):
    print("=" * 80)
    print("CONTROLLED FAULT INJECTION BENCHMARK (RQ3: Local Patch Repair Evaluation)")
    print(f"Target Model: {model} | API Base: {api_base}")
    print(f"Trials per category: {trials_per_cat} | Total trials: {trials_per_cat * 4}")
    print("=" * 80)

    # Initialize Client and Specialized Repair Agents
    client = AsyncOpenAI(base_url=api_base, api_key=api_key)
    outline_agent = OutlineAgent(client, model)
    character_agent = CharacterAgent(client, model)
    clue_agent = ClueAgent(client, model)

    baselines = load_valid_baseline_dossiers()
    if not baselines:
        raise RuntimeError("No valid baseline dossiers available for fault injection!")

    categories = [
        {
            "category": "cat1_tod_physics",
            "name": "Henssge Forensic TOD Physics / Crime Time Out-of-Window",
            "component": "outline",
            "injector": inject_tod_fault,
            "agent": outline_agent,
        },
        {
            "category": "cat2_duplicate_id",
            "name": "Duplicate Suspect Identifier / Culprit Mismatch",
            "component": "character",
            "injector": inject_duplicate_id_fault,
            "agent": character_agent,
        },
        {
            "category": "cat3_unbroken_alibi",
            "name": "Missing Crucial Clue / Unbroken Culprit Alibi",
            "component": "clue",
            "injector": inject_crucial_clue_fault,
            "agent": clue_agent,
        },
        {
            "category": "cat4_foreign_key_error",
            "name": "Referential Schema Error / Foreign Key Mismatch",
            "component": "clue",
            "injector": inject_foreign_key_fault,
            "agent": clue_agent,
        },
    ]

    all_trial_results: List[Dict[str, Any]] = []
    category_summaries: Dict[str, Any] = {}

    total_runs = len(categories) * trials_per_cat
    current_run = 0

    for cat_spec in categories:
        cat_id = cat_spec["category"]
        cat_name = cat_spec["name"]
        comp = cat_spec["component"]
        injector = cat_spec["injector"]
        agent = cat_spec["agent"]

        print(f"\n---> Starting Category: {cat_name} ({trials_per_cat} trials)")

        cat_successes = 0
        cat_tokens: List[int] = []
        cat_latencies: List[float] = []
        cat_prompt_tokens: List[int] = []
        cat_completion_tokens: List[int] = []

        for i in range(trials_per_cat):
            current_run += 1
            # Select baseline case round-robin
            baseline_case = baselines[i % len(baselines)]

            # 1. Inject Controlled Fault
            corrupted_case, inject_desc = injector(baseline_case, i)

            # 2. Verify Pre-Repair Violation Detection
            pre_diag = validate_case_diagnostics(corrupted_case)
            if pre_diag.is_valid:
                print(f"  [Trial {i+1:02d}/{trials_per_cat}] WARNING: Fault injection did not trigger violation: {inject_desc}")

            pre_violations = [f"[{v.component}:{v.violation_type.value}] {v.message}" for v in pre_diag.violations]
            diagnostic_msg = pre_diag.diagnostic_feedback

            # 3. Execute Localized Patch Repair
            t0 = time.perf_counter()
            repaired_case = copy.deepcopy(corrupted_case)
            try:
                if comp == "outline":
                    victim, ground_truth = await outline_agent.repair_tod(
                        repaired_case.victim, repaired_case.ground_truth, diagnostic_msg
                    )
                    apply_henssge_tod_window(victim.forensic_data)
                    repaired_case.victim = victim
                    repaired_case.ground_truth = ground_truth
                elif comp == "character":
                    suspects = await character_agent.repair_suspects(
                        repaired_case.suspects, repaired_case.ground_truth, diagnostic_msg
                    )
                    repaired_case.suspects = suspects
                elif comp == "clue":
                    evidences = await clue_agent.repair_clues(
                        repaired_case.evidences, repaired_case.suspects, repaired_case.ground_truth, diagnostic_msg
                    )
                    repaired_case.evidences = evidences
            except Exception as e:
                print(f"  [Trial {i+1:02d}/{trials_per_cat}] EXCEPTION during repair: {e}")

            latency_sec = round(time.perf_counter() - t0, 2)

            # Extract Token Usage
            usage = agent.last_usage
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            t_tok = usage.get("total_tokens", 0)

            # 4. Post-Repair Neuro-Symbolic Verification
            post_diag = validate_case_diagnostics(repaired_case)
            repair_success = post_diag.is_valid
            post_violations = [f"[{v.component}:{v.violation_type.value}] {v.message}" for v in post_diag.violations]

            if repair_success:
                cat_successes += 1

            cat_tokens.append(t_tok)
            cat_prompt_tokens.append(p_tok)
            cat_completion_tokens.append(c_tok)
            cat_latencies.append(latency_sec)

            trial_record = {
                "run_id": current_run,
                "category": cat_id,
                "category_name": cat_name,
                "trial": i + 1,
                "baseline_case_id": baseline_case.case_id,
                "injection_description": inject_desc,
                "pre_repair_valid": pre_diag.is_valid,
                "pre_repair_violations_count": len(pre_diag.violations),
                "pre_repair_violations": pre_violations,
                "post_repair_valid": post_diag.is_valid,
                "post_repair_violations_count": len(post_diag.violations),
                "post_repair_violations": post_violations,
                "repair_success": repair_success,
                "latency_sec": latency_sec,
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": t_tok,
                "token_savings_pct": round((1.0 - t_tok / FULL_REGEN_TOKENS) * 100.0, 2),
                "latency_savings_pct": round((1.0 - latency_sec / FULL_REGEN_LATENCY_P50) * 100.0, 2),
            }
            all_trial_results.append(trial_record)

            status_str = "SUCCESS" if repair_success else "FAILED"
            print(f"  [{current_run:02d}/{total_runs}] Trial {i+1:02d}: {status_str} in {latency_sec:.2f}s | Tokens: {t_tok} (Prompt: {p_tok}, Comp: {c_tok})")
            await asyncio.sleep(1.0)

        # Category Summary
        success_rate = round((cat_successes / trials_per_cat) * 100.0, 2)
        ci_low, ci_high = calc_wilson_ci(cat_successes, trials_per_cat)
        mean_tok = round(sum(cat_tokens) / len(cat_tokens), 1)
        mean_p_tok = round(sum(cat_prompt_tokens) / len(cat_prompt_tokens), 1)
        mean_c_tok = round(sum(cat_completion_tokens) / len(cat_completion_tokens), 1)
        p50_lat = calc_percentile(cat_latencies, 0.50)
        p95_lat = calc_percentile(cat_latencies, 0.95)
        mean_lat = round(sum(cat_latencies) / len(cat_latencies), 2)
        token_saving = round((1.0 - mean_tok / FULL_REGEN_TOKENS) * 100.0, 2)
        lat_saving = round((1.0 - p50_lat / FULL_REGEN_LATENCY_P50) * 100.0, 2)

        category_summaries[cat_id] = {
            "category_name": cat_name,
            "responsible_agent": comp.capitalize() + "Agent",
            "trials_count": trials_per_cat,
            "success_count": cat_successes,
            "success_rate_pct": success_rate,
            "wilson_ci_95": [ci_low, ci_high],
            "mean_prompt_tokens": mean_p_tok,
            "mean_completion_tokens": mean_c_tok,
            "mean_total_tokens": mean_tok,
            "latency_p50_sec": p50_lat,
            "latency_p95_sec": p95_lat,
            "latency_mean_sec": mean_lat,
            "token_savings_pct": token_saving,
            "latency_savings_pct": lat_saving,
        }

        print(f"--> Category '{cat_name}' Done: Success = {success_rate}% [{ci_low} - {ci_high}] | Mean Tokens = {mean_tok} | Latency P50 = {p50_lat}s")

    # Overall Summary
    total_trials = len(all_trial_results)
    total_successes = sum(1 for t in all_trial_results if t["repair_success"])
    overall_success_rate = round((total_successes / total_trials) * 100.0, 2)
    overall_ci_low, overall_ci_high = calc_wilson_ci(total_successes, total_trials)
    all_tokens = [t["total_tokens"] for t in all_trial_results]
    all_latencies = [t["latency_sec"] for t in all_trial_results]
    overall_mean_tokens = round(sum(all_tokens) / len(all_tokens), 1)
    overall_p50_lat = calc_percentile(all_latencies, 0.50)
    overall_p95_lat = calc_percentile(all_latencies, 0.95)
    overall_token_savings = round((1.0 - overall_mean_tokens / FULL_REGEN_TOKENS) * 100.0, 2)
    overall_lat_savings = round((1.0 - overall_p50_lat / FULL_REGEN_LATENCY_P50) * 100.0, 2)

    final_payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "api_base": api_base,
        "total_trials": total_trials,
        "total_successes": total_successes,
        "overall_success_rate_pct": overall_success_rate,
        "overall_wilson_ci_95": [overall_ci_low, overall_ci_high],
        "overall_mean_tokens": overall_mean_tokens,
        "overall_latency_p50_sec": overall_p50_lat,
        "overall_latency_p95_sec": overall_p95_lat,
        "overall_token_savings_pct": overall_token_savings,
        "overall_latency_savings_pct": overall_lat_savings,
        "full_regeneration_baseline": {
            "tokens": FULL_REGEN_TOKENS,
            "latency_p50_sec": FULL_REGEN_LATENCY_P50,
        },
        "category_summaries": category_summaries,
        "trials": all_trial_results,
    }

    # Save to disk
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("FAULT INJECTION EXPERIMENT COMPLETED SUCCESSFULLY!")
    print(f"Results saved to: {output_path}")
    print(f"Overall Repair Success: {overall_success_rate}% [{overall_ci_low} - {overall_ci_high}] ({total_successes}/{total_trials})")
    print(f"Overall Mean Tokens: {overall_mean_tokens} tokens (Savings vs Full Regen: {overall_token_savings}%)")
    print(f"Overall Latency P50: {overall_p50_lat}s (Savings vs Full Regen: {overall_lat_savings}%)")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Controlled Fault Injection Experiment")
    parser.add_argument("--model", type=str, default="gh/gpt-4o-mini", help="LLM model identifier")
    parser.add_argument("--api-base", type=str, default="http://localhost:20128/v1", help="API base URL")
    parser.add_argument("--api-key", type=str, default=os.getenv("LLM_API_KEY", ""), help="API key (defaults to LLM_API_KEY env var)")
    parser.add_argument("--trials", type=int, default=20, help="Number of trials per fault category")
    parser.add_argument("--output", type=str, default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "fault_injection_results.json"), help="Output JSON path")
    args = parser.parse_args()

    asyncio.run(
        run_fault_injection_experiment(
            api_base=args.api_base,
            api_key=args.api_key,
            model=args.model,
            trials_per_cat=args.trials,
            output_path=args.output
        )
    )
