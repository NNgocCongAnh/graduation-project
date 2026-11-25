"""Recompute benchmark metrics from raw JSON files in benchmarks/results/.

Run from the repository root:
    python benchmarks/scripts/verify_results.py

Checks all published raw files in benchmarks/results/ and (when present locally
under _ban_cu/report_snapshots/) also reconciles the locked thesis Table 4.1
snapshot datasets. Exits with code 1 on any mismatch.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS = ROOT / "benchmarks" / "results"
SNAPSHOTS = ROOT / "_ban_cu" / "report_snapshots"

# Expected values for published benchmarks/results/ datasets
EXPECTED_PUBLISHED = {
    "pub.mini.n": 30, "pub.mini.logic": 30, "pub.mini.p50": 22.34, "pub.mini.p95": 28.05,
    "pub.gpt4o.n": 24, "pub.gpt4o.logic": 24, "pub.gpt4o.p50": 45.51, "pub.gpt4o.p95": 54.78,
    "pub.gemma_hyb.n": 23, "pub.gemma_hyb.logic": 23, "pub.gemma_hyb.p50": 1180.47, "pub.gemma_hyb.fallback_runs": 23,
    "pub.gemma_pure.n": 3, "pub.gemma_pure.llm_logic": 0,
    "ablation.config1_valid": 0, "ablation.config2_valid": 3, "ablation.config3_valid": 3, "ablation.config4_valid": 3,
    "e2e.n": 9, "e2e.schema": 5, "e2e.logic": 1,
    "fault.n": 80, "fault.success": 51, "fault.tokens": 4227.6, "fault.p50": 7.21,
    "solver_base.n": 20, "solver_base.culprit_correct": 19,
    "solver_new.n": 3, "solver_new.perfect": 3,
}

# Locked thesis Table 4.1 local snapshot checks (when _ban_cu/report_snapshots exists)
EXPECTED_REPORT = {
    "mini.n": 30, "mini.logic": 30, "mini.p50": 23.23, "mini.p95": 30.90, "mini.tokens": 18396,
    "mini.culprit_SUSP-02": 28, "mini.crime_21:30": 23,
    "gpt4o.n": 30, "gpt4o.logic": 30, "gpt4o.p50": 46.81, "gpt4o.p95": 59.77,
    "cloud.p50": 39.50, "cloud.p95": 54.33,
}
TOL = 0.015


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * min(1.0, c + h), 1)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def bench(path: Path) -> dict:
    d = load(path)
    lat = [r["latency_sec"] for r in d]
    tok_vals = [r["token_usage"]["total_tokens"] for r in d if r.get("token_usage") and r["token_usage"].get("total_tokens")]
    return {
        "n": len(d),
        "logic": sum(bool(r["logic_valid"]) for r in d),
        "llm_logic": sum(bool(r["logic_valid"]) and not bool(r.get("used_fallback_sample")) for r in d),
        "p50": round(float(np.percentile(lat, 50)), 2),
        "p95": round(float(np.percentile(lat, 95)), 2),
        "tokens": round(float(np.mean(tok_vals))) if tok_vals else 0,
        "culprits": Counter(r["culprit_id"] for r in d),
        "times": Counter(r["crime_time"] for r in d),
        "models": Counter(tuple(sorted(set(r["agent_models"].values()))) for r in d),
        "fallback_runs": sum(bool(r.get("fallback_triggered")) for r in d),
        "lat": lat,
    }


got: dict[str, float] = {}
pub_mini = bench(RESULTS / "benchmark_gpt-4o-mini.json")
pub_4o = bench(RESULTS / "benchmark_gpt-4o.json")
pub_gem = bench(RESULTS / "benchmark_gemma4_hybrid.json")
pub_gem_pure = bench(RESULTS / "benchmark_gemma4.json")

for key, b in (("pub.mini", pub_mini), ("pub.gpt4o", pub_4o), ("pub.gemma_hyb", pub_gem)):
    for f in ("n", "logic", "p50", "p95"):
        if f"{key}.{f}" in EXPECTED_PUBLISHED:
            got[f"{key}.{f}"] = b[f]
got["pub.gemma_hyb.fallback_runs"] = pub_gem["fallback_runs"]
got["pub.gemma_pure.n"] = pub_gem_pure["n"]
got["pub.gemma_pure.llm_logic"] = pub_gem_pure["llm_logic"]

abl = load(RESULTS / "ablation_results.json")
for i in (1, 2, 3, 4):
    runs = [r for r in abl if r["config_name"].startswith(f"Config {i}:")]
    got[f"ablation.config{i}_valid"] = sum(bool(r["logic_valid"]) for r in runs)

e2e = load(RESULTS / "e2e_plan_baseline_results.json")
got["e2e.n"] = len(e2e)
got["e2e.schema"] = sum(bool(r["json_valid"]) for r in e2e)
got["e2e.logic"] = sum(bool(r["logic_valid"]) for r in e2e)

fault = load(RESULTS / "fault_injection_results.json")
got["fault.n"] = fault["total_trials"]
got["fault.success"] = fault["total_successes"]
got["fault.tokens"] = fault["overall_mean_tokens"]
got["fault.p50"] = fault["overall_latency_p50_sec"]

solver_base = load(RESULTS / "solver_benchmark_baseline.json")
got["solver_base.n"] = solver_base["total_cases_evaluated"]
got["solver_base.culprit_correct"] = sum(bool(c.get("culprit_identified")) for c in solver_base.get("cases", []))

solver_new = load(RESULTS / "solver_benchmark.json")
got["solver_new.n"] = solver_new["total_cases_evaluated"]
got["solver_new.perfect"] = sum(
    bool(c.get("culprit_identified") and c.get("score") == 100) for c in solver_new.get("cases", [])
)

checks = dict(EXPECTED_PUBLISHED)
if (SNAPSHOTS / "benchmark_results_gpt4o_mini.json").exists() and (SNAPSHOTS / "benchmark_results_gpt4o_v2.json").exists():
    rep_mini = bench(SNAPSHOTS / "benchmark_results_gpt4o_mini.json")
    rep_4o = bench(SNAPSHOTS / "benchmark_results_gpt4o_v2.json")
    for key, b in (("mini", rep_mini), ("gpt4o", rep_4o)):
        for f in ("n", "logic", "p50", "p95"):
            got[f"{key}.{f}"] = b[f]
    got["mini.tokens"] = rep_mini["tokens"]
    got["mini.culprit_SUSP-02"] = rep_mini["culprits"]["SUSP-02"]
    got["mini.crime_21:30"] = rep_mini["times"]["21:30"]
    cloud = rep_mini["lat"] + rep_4o["lat"]
    got["cloud.p50"] = round(float(np.percentile(cloud, 50)), 2)
    got["cloud.p95"] = round(float(np.percentile(cloud, 95)), 2)
    checks.update(EXPECTED_REPORT)

failed = 0
for k, exp in checks.items():
    val = got.get(k)
    ok = val is not None and (abs(val - exp) <= TOL if isinstance(exp, float) else val == exp)
    failed += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {k:<28} data={val!s:<10} expected={exp}")

print(f"\nPublished Wilson CI: mini={wilson(pub_mini['logic'], pub_mini['n'])}, gpt-4o={wilson(pub_4o['logic'], pub_4o['n'])}")
print(f"gemma_hyb agent_models: {dict(pub_gem['models'])}")
print(f"pub gpt-4o agent_models: {dict(pub_4o['models'])}")
sys.exit(1 if failed else 0)
