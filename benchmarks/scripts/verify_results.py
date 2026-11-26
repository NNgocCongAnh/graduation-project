"""Recompute every headline number of thesis Chapter 4 from benchmarks/results/.

Run from the repository root:
    python benchmarks/scripts/verify_results.py

Any mismatch with EXPECTED exits with code 1.
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

# Values written in the thesis, slides, notebook, and README (keep 100% in sync).
EXPECTED = {
    "mini.n": 30, "mini.logic": 30, "mini.p50": 22.34, "mini.p95": 28.05, "mini.tokens": 19380,
    "mini.patched": 7, "mini.culprit_1": 11, "mini.culprit_2": 8, "mini.culprit_3": 11,
    "gpt4o.n": 30, "gpt4o.logic": 30, "gpt4o.p50": 47.82, "gpt4o.p95": 53.97, "gpt4o.tokens": 19999,
    "gpt4o.patched": 7, "gpt4o.culprit_1": 11, "gpt4o.culprit_2": 10, "gpt4o.culprit_3": 9,
    "cloud.p50": 34.55, "cloud.p95": 52.22,
    "gemma_pure.n": 30, "gemma_pure.llm_logic": 0, "gemma_pure.p50": 694.30, "gemma_pure.p95": 1053.75,
    "gemma_hyb.n": 23, "gemma_hyb.logic": 23, "gemma_hyb.p50": 1180.47, "gemma_hyb.p95": 1489.89, "gemma_hyb.fallback_runs": 23,
    "ablation.config1_valid": 0, "ablation.config2_valid": 3, "ablation.config3_valid": 3, "ablation.config4_valid": 3,
    "e2e.n": 9, "e2e.schema": 5, "e2e.logic": 1,
    "fault.n": 80, "fault.success": 51, "fault.tokens": 4227.6, "fault.p50": 7.21,
    "solver_base.n": 20, "solver_base.culprit_correct": 19,
    "solver_new.n": 20, "solver_new.perfect": 17, "solver_new.crucial": 20, "solver_new.herring_ok": 20, "solver_new.p50": 12.64,
}
TOL = 0.015


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * min(1.0, c + h), 1)


def load(name: str):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def bench(name: str) -> dict:
    d = load(name)
    lat = [r["latency_sec"] for r in d]
    tok_vals = [r["token_usage"]["total_tokens"] for r in d if r.get("token_usage") and r["token_usage"].get("total_tokens")]
    return {
        "n": len(d),
        "logic": sum(bool(r["logic_valid"]) for r in d),
        "llm_logic": sum(bool(r["logic_valid"]) and not bool(r.get("used_fallback_sample")) for r in d),
        "p50": round(float(np.percentile(lat, 50)), 2),
        "p95": round(float(np.percentile(lat, 95)), 2),
        "tokens": round(float(np.mean(tok_vals))) if tok_vals else 0,
        "patched": sum(1 for r in d if r.get("patch_retries", 0) > 0),
        "culprits": Counter(r["culprit_id"] for r in d),
        "times": Counter(r["crime_time"] for r in d),
        "models": Counter(tuple(sorted(set(r["agent_models"].values()))) for r in d),
        "fallback_runs": sum(bool(r.get("fallback_triggered")) for r in d),
        "lat": lat,
    }


got: dict[str, float] = {}
mini = bench("benchmark_gpt-4o-mini.json")
g4o = bench("benchmark_gpt-4o.json")
gem_pure = bench("benchmark_gemma4.json")
gem_hyb = bench("benchmark_gemma4_hybrid.json")

for key, b in (("mini", mini), ("gpt4o", g4o)):
    for f in ("n", "logic", "p50", "p95", "tokens", "patched"):
        got[f"{key}.{f}"] = b[f]
    got[f"{key}.culprit_1"] = b["culprits"]["SUSP-01"]
    got[f"{key}.culprit_2"] = b["culprits"]["SUSP-02"]
    got[f"{key}.culprit_3"] = b["culprits"]["SUSP-03"]

cloud = mini["lat"] + g4o["lat"]
got["cloud.p50"] = round(float(np.percentile(cloud, 50)), 2)
got["cloud.p95"] = round(float(np.percentile(cloud, 95)), 2)

got["gemma_pure.n"] = gem_pure["n"]
got["gemma_pure.llm_logic"] = gem_pure["llm_logic"]
got["gemma_pure.p50"] = gem_pure["p50"]
got["gemma_pure.p95"] = gem_pure["p95"]

got["gemma_hyb.n"] = gem_hyb["n"]
got["gemma_hyb.logic"] = gem_hyb["logic"]
got["gemma_hyb.p50"] = gem_hyb["p50"]
got["gemma_hyb.p95"] = gem_hyb["p95"]
got["gemma_hyb.fallback_runs"] = gem_hyb["fallback_runs"]

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

solver_base = load("solver_benchmark_baseline.json")
got["solver_base.n"] = solver_base["total_cases_evaluated"]
got["solver_base.culprit_correct"] = sum(bool(c.get("culprit_identified")) for c in solver_base.get("cases", []))

solver_new = load("solver_benchmark.json")
got["solver_new.n"] = solver_new["total_cases_evaluated"]
got["solver_new.perfect"] = sum(bool(c.get("culprit_identified") and c.get("score") == 100) for c in solver_new.get("cases", []))
got["solver_new.crucial"] = sum(bool(c.get("crucial_evidences_identified")) for c in solver_new.get("cases", []))
got["solver_new.herring_ok"] = sum(1 for c in solver_new.get("cases", []) if c.get("red_herrings_selected_count", 1) == 0)
got["solver_new.p50"] = solver_new["latency_p50_sec"]

failed = 0
for k, exp in EXPECTED.items():
    val = got.get(k)
    ok = val is not None and (abs(val - exp) <= TOL if isinstance(exp, float) else val == exp)
    failed += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {k:<28} data={val!s:<10} report={exp}")

print("\n--- derived values ---")
print(f"mini Wilson={wilson(mini['logic'], mini['n'])}; gpt4o Wilson={wilson(g4o['logic'], g4o['n'])}; cloud Wilson={wilson(mini['logic'] + g4o['logic'], mini['n'] + g4o['n'])}")
print(f"gemma_pure Wilson={wilson(gem_pure['llm_logic'], gem_pure['n'])}; gemma_hyb Wilson={wilson(gem_hyb['logic'], gem_hyb['n'])}")
print(f"solver_new Wilson={wilson(int(got['solver_new.perfect']), int(got['solver_new.n']))}")
print(f"patch savings vs mini full regen: tokens {100 * (1 - fault['overall_mean_tokens'] / mini['tokens']):.1f}%, latency {100 * (1 - fault['overall_latency_p50_sec'] / mini['p50']):.1f}%")
print(f"mini agent_models: {dict(mini['models'])}")
print(f"gpt4o agent_models: {dict(g4o['models'])}")
print(f"gemma_hyb agent_models: {dict(gem_hyb['models'])}")
sys.exit(1 if failed else 0)
