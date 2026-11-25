"""Run the single-call E2E-plan baseline (see e2e_baseline.py) with the benchmark's own metrics.

Usage (from repository root):
    python detective-backend/run_e2e_baseline.py --model gh/gpt-4o-mini --trials-per-theme 3
"""

import argparse
import asyncio
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(__file__))

from benchmark_runner import BENCHMARK_THEMES, calc_wilson_ci, evaluate_single_trial  # noqa: E402
from llm_service import CaseGeneratorService  # noqa: E402

CONFIG_NAME = "Config 1b: E2E-plan Single Call (Huot et al., 2025)"


async def run(model: str, trials_per_theme: int, output: str, delay: float) -> None:
    service = CaseGeneratorService(model=model)
    results = []
    for theme in BENCHMARK_THEMES:
        for i in range(trials_per_theme):
            res = await evaluate_single_trial(service=service, theme=theme, enable_post_processing=False,
                                              enable_patch_repair=False, mode="monolithic_plan", max_retries=0)
            res["config_name"] = CONFIG_NAME
            res["model"] = model
            results.append(res)
            err = (res.get("error") or "").split("\n")[0]
            print(f"[{theme}] #{i + 1}: json={res['json_valid']} logic={res['logic_valid']} "
                  f"viol={res['violation_types']} {res['latency_sec']}s {err}", flush=True)
            with open(output, "w", encoding="utf-8") as fh:
                json.dump(results, fh, ensure_ascii=False, indent=2)
            if delay:
                await asyncio.sleep(delay)

    n = len(results)
    k_json = sum(r["json_valid"] for r in results)
    k_logic = sum(r["logic_valid"] for r in results)
    lat = [r["latency_sec"] for r in results]
    print(f"\n{CONFIG_NAME}: N={n} schema {k_json}/{n} {calc_wilson_ci(k_json, n)} "
          f"logic {k_logic}/{n} {calc_wilson_ci(k_logic, n)} P50 {statistics.median(lat):.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gh/gpt-4o-mini")
    parser.add_argument("--trials-per-theme", type=int, default=3)
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "e2e_plan_baseline_results.json"))
    args = parser.parse_args()
    asyncio.run(run(args.model, args.trials_per_theme, args.output, args.delay))


if __name__ == "__main__":
    main()
