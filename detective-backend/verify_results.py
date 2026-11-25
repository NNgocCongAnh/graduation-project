"""Recompute every headline number of thesis Chapter 4 from the raw result files.

Run from the repository root:
    python detective-backend/verify_results.py

Each line prints the value recomputed from data and the value currently written in the
report (EXPECTED). Any mismatch is reported as FAIL and the script exits with code 1.
If you rerun an experiment, update EXPECTED here AND every place in the report/slides.
NEVER edit a number in the report that this script cannot reproduce.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

BE = Path(__file__).resolve().parent

# Values currently written in the thesis / slides / README (keep in sync).
EXPECTED = {
    "mini.n": 30, "mini.logic": 30, "mini.p50": 23.23, "mini.p95": 30.90, "mini.tokens": 18396,
    "mini.culprit_SUSP-02": 28, "mini.crime_21:30": 23,
    "gpt4o.n": 30, "gpt4o.logic": 30, "gpt4o.p50": 41.95, "gpt4o.p95": 49.51,
    "gpt4o_v2.n": 18, "gpt4o_v2.logic": 18, "gpt4o_v2.p50": 40.98, "gpt4o_v2.p95": 44.04,
    "cloud.p50": 38.41, "cloud.p95": 46.76,
    "gemma.n": 23, "gemma.logic": 23, "gemma.p50": 1180.47, "gemma.fallback_runs": 23,
    "ablation.config1_valid": 0, "ablation.config2_valid": 3, "ablation.config3_valid": 3, "ablation.config4_valid": 3,
    "e2e.n": 9, "e2e.schema": 5, "e2e.logic": 1,
    "fault.n": 80, "fault.success": 51, "fault.tokens": 4227.6, "fault.p50": 7.21,
    "solver.n": 20, "solver.culprit_correct": 19,
}
TOL = 0.015  # tolerance for floats (2-decimal rounding)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * min(1.0, c + h), 1)


def load(name: str):
    return json.loads((BE / name).read_text(encoding="utf-8"))


def bench(name: str) -> dict:
    d = load(name)
    lat = [r["latency_sec"] for r in d]
    return {
        "n": len(d),
        "logic": sum(bool(r["logic_valid"]) for r in d),
        "p50": round(float(np.percentile(lat, 50)), 2),
        "p95": round(float(np.percentile(lat, 95)), 2),
        "tokens": round(float(np.mean([r["token_usage"]["total_tokens"] for r in d if r.get("token_usage")]))),
        "culprits": Counter(r["culprit_id"] for r in d),
        "times": Counter(r["crime_time"] for r in d),
        "models": Counter(tuple(sorted(set(r["agent_models"].values()))) for r in d),
        "fallback_runs": sum(bool(r.get("fallback_triggered")) for r in d),
        "lat": lat,
    }


got: dict[str, float] = {}
mini = bench("benchmark_results_gpt4o_mini.json")
g4o = bench("benchmark_results_gpt4o.json")
g4o2 = bench("benchmark_results_gpt4o_v2.json")
gem = bench("benchmark_results_gemma4_local.json")
for key, b in (("mini", mini), ("gpt4o", g4o), ("gpt4o_v2", g4o2), ("gemma", gem)):
    for f in ("n", "logic", "p50", "p95"):
        got[f"{key}.{f}"] = b[f]
got["mini.tokens"] = mini["tokens"]
got["mini.culprit_SUSP-02"] = mini["culprits"]["SUSP-02"]
got["mini.crime_21:30"] = mini["times"]["21:30"]
got["gemma.fallback_runs"] = gem["fallback_runs"]
cloud = mini["lat"] + g4o["lat"]
got["cloud.p50"] = round(float(np.percentile(cloud, 50)), 2)
got["cloud.p95"] = round(float(np.percentile(cloud, 95)), 2)

abl = load("ablation_results.json")
for i in (1, 2, 3, 4):
    runs = [r for r in abl if r["config_name"].startswith(f"Config {i}:")]
    got[f"ablation.config{i}_valid"] = sum(bool(r["logic_valid"]) for r in runs)

e2e = load("e2e_plan_baseline_results.json")
got["e2e.n"] = len(e2e)
got["e2e.schema"] = sum(bool(r["json_valid"]) for r in e2e)
got["e2e.logic"] = sum(bool(r["logic_valid"]) for r in e2e)

fault = load("fault_injection_results.json")
got["fault.n"] = fault["total_trials"]
got["fault.success"] = fault["total_successes"]
got["fault.tokens"] = fault["overall_mean_tokens"]
got["fault.p50"] = fault["overall_latency_p50_sec"]

solver = load("solver_benchmark_results.json")
got["solver.n"] = solver["total_cases_evaluated"]
got["solver.culprit_correct"] = sum(bool(c.get("culprit_identified")) for c in solver.get("cases", []))

failed = 0
for k, exp in EXPECTED.items():
    val = got.get(k)
    ok = val is not None and (abs(val - exp) <= TOL if isinstance(exp, float) else val == exp)
    failed += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {k:<26} data={val!s:<10} report={exp}")

print("\n--- derived values (copy into report if you change data) ---")
print(f"mini Wilson logic: {wilson(mini['logic'], mini['n'])}; cloud Wilson: {wilson(mini['logic'] + g4o['logic'], mini['n'] + g4o['n'])}")
print(f"patch savings vs mini full regen: tokens {100 * (1 - fault['overall_mean_tokens'] / mini['tokens']):.1f}%, "
      f"latency {100 * (1 - fault['overall_latency_p50_sec'] / mini['p50']):.1f}%")
print(f"gemma agent_models: {dict(gem['models'])}")
print(f"gpt4o_v2 agent_models: {dict(g4o2['models'])}  (must be only gh/gpt-4o)")
print(f"mini culprit distribution (raw LLM output): {dict(mini['culprits'])}")
sys.exit(1 if failed else 0)
