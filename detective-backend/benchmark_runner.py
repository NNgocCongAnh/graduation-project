"""Cross-Model Benchmark Evaluation Runner.

Compares generation quality, JSON validity, logic consistency pass rate,
localized patch repair effectiveness, and latency across multiple LLM backbones
(e.g., gh/gpt-4o, gh/gpt-4o-mini, ollama/gemma4:31b-cloud).

Usage:
  python benchmark_runner.py --models gh/gpt-4o-mini gh/gpt-4o --trials 10
"""

import os
import sys
import time
import json
import asyncio
import argparse
import statistics
from typing import List, Dict, Any

from models import CaseDossier
from llm_service import CaseGeneratorService
from validator import validate_case_diagnostics


async def evaluate_single_trial(service: CaseGeneratorService, theme: str) -> Dict[str, Any]:
    """Execute one case generation trial and collect fine-grained scientific telemetry."""
    start_t = time.time()
    try:
        dossier = await service.generate_case(theme=theme, max_retries=2)
        total_lat = round(time.time() - start_t, 2)
        diag = validate_case_diagnostics(dossier)

        culprit = next((s for s in dossier.suspects if s.is_culprit), None)
        crucial_clues = [e for e in dossier.evidences if e.is_crucial]
        red_herrings = [e for e in dossier.evidences if e.is_red_herring]

        return {
            "success": True,
            "json_valid": True,
            "logic_valid": diag.is_valid,
            "violations_count": len(diag.violations),
            "violation_types": [v.violation_type.value for v in diag.violations],
            "crucial_clues_count": len(crucial_clues),
            "red_herrings_count": len(red_herrings),
            "culprit_alibi_window": f"{culprit.alibi_start}-{culprit.alibi_end}" if culprit else "N/A",
            "crime_time": dossier.ground_truth.actual_crime_time if dossier.ground_truth else "N/A",
            "patch_retries": dossier.metadata.patch_retries if dossier.metadata else 0,
            "latency_sec": total_lat,
            "title": dossier.title,
            "reasoning_steps": len(dossier.reasoning_chain.steps) if dossier.reasoning_chain else 0,
            "error": "None" if diag.is_valid else diag.diagnostic_feedback
        }
    except Exception as e:
        total_lat = round(time.time() - start_t, 2)
        return {
            "success": False,
            "json_valid": False,
            "logic_valid": False,
            "violations_count": -1,
            "violation_types": ["RUNTIME_ERROR"],
            "crucial_clues_count": 0,
            "red_herrings_count": 0,
            "culprit_alibi_window": "N/A",
            "crime_time": "N/A",
            "patch_retries": 0,
            "latency_sec": total_lat,
            "title": "Failed",
            "reasoning_steps": 0,
            "error": str(e)
        }


def calc_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile without external numpy dependency."""
    if not data:
        return 0.0
    sorted_d = sorted(data)
    idx = int(len(sorted_d) * percentile)
    idx = min(idx, len(sorted_d) - 1)
    return sorted_d[idx]


async def run_benchmark(models: List[str], trials: int = 10, theme: str = "Bí ẩn Biệt thự Blackwood") -> List[Dict[str, Any]]:
    """Run benchmark across specified models and print comparative summary with P50/P95 latency."""
    all_results: List[Dict[str, Any]] = []

    print("=" * 80)
    print(f"BẮT ĐẦU THỰC NGHIỆM ĐÁNH GIÁ ĐA MÔ HÌNH (Trials={trials}/model)")
    print(f"Chủ đề gốc: '{theme}'")
    print("=" * 80)

    for model in models:
        print(f"\n--- Đang kiểm thử Mô hình: {model} ({trials} trials) ---")
        service = CaseGeneratorService(model=model)

        for i in range(1, trials + 1):
            print(f"  [Lượt {i:02d}/{trials:02d}] Đang sinh kịch bản...", end="", flush=True)
            res = await evaluate_single_trial(service, theme)
            res["model"] = model
            res["trial"] = i
            all_results.append(res)

            status_mark = "✅ PASS" if res["logic_valid"] else "❌ FAIL"
            v_info = f"Vi phạm: {res['violation_types']}" if not res["logic_valid"] else "5/5 Hợp lệ"
            print(f" -> {status_mark} | Sửa lỗi: {res['patch_retries']} | {res['latency_sec']}s | {v_info}")

    # Generate Academic Telemetry Summary Table
    print("\n" + "=" * 88)
    print("BẢNG TỔNG HỢP KẾT QUẢ ĐỐI SÁNH THỰC NGHIỆM ĐA MÔ HÌNH (BẢNG 4.1 TRONG BÁO CÁO)")
    print("=" * 88)
    header = f"{'Mô hình':<24} | {'JSON (%)':<9} | {'Logic (%)':<10} | {'Sửa TB':<7} | {'P50 (s)':<8} | {'P95 (s)':<8} | {'Clues/Herrings':<14}"
    print(header)
    print("-" * 88)

    model_summaries = {}
    error_taxonomy = {}

    for model in models:
        m_runs = [r for r in all_results if r["model"] == model]
        if not m_runs:
            continue
        json_rate = sum(1 for r in m_runs if r["json_valid"]) / len(m_runs) * 100
        logic_rate = sum(1 for r in m_runs if r["logic_valid"]) / len(m_runs) * 100
        avg_retries = sum(r["patch_retries"] for r in m_runs) / len(m_runs)
        
        latencies = [r["latency_sec"] for r in m_runs]
        p50_lat = round(statistics.median(latencies), 2)
        p95_lat = round(calc_percentile(latencies, 0.95), 2)

        avg_crucial = round(sum(r["crucial_clues_count"] for r in m_runs) / len(m_runs), 1)
        avg_herrings = round(sum(r["red_herrings_count"] for r in m_runs) / len(m_runs), 1)
        ratio_str = f"{avg_crucial}/{avg_herrings}"

        print(f"{model:<24} | {json_rate:>8.1f}% | {logic_rate:>9.1f}% | {avg_retries:>7.2f} | {p50_lat:>7.2f}s | {p95_lat:>7.2f}s | {ratio_str:>14}")

        model_summaries[model] = {
            "json_valid_rate": json_rate,
            "logic_pass_rate": logic_rate,
            "avg_patch_retries": avg_retries,
            "latency_p50": p50_lat,
            "latency_p95": p95_lat,
            "avg_crucial_clues": avg_crucial,
            "avg_red_herrings": avg_herrings
        }

        # Track error taxonomy
        for r in m_runs:
            for vt in r.get("violation_types", []):
                error_taxonomy[vt] = error_taxonomy.get(vt, 0) + 1

    print("=" * 88)

    # Print Error Taxonomy Breakdown (for Figure 4.2 Pie Chart)
    print("\n--- PHÂN LOẠI LỖI LOGIC & TẦN SUẤT XUẤT HIỆN (CHO HÌNH 4.2 BÁO CÁO) ---")
    if error_taxonomy:
        total_errors = sum(error_taxonomy.values())
        for err, count in sorted(error_taxonomy.items(), key=lambda x: x[1], reverse=True):
            pct = count / total_errors * 100
            print(f"  • {err:<28}: {count:>2} lần ({pct:>5.1f}%)")
    else:
        print("  • Không ghi nhận vi phạm logic nào. Toàn bộ kịch bản đạt chuẩn 100%!")

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu toàn bộ telemetry thực nghiệm vào: {output_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="AI Detective Case Engine Multi-Model Benchmark")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["gh/gpt-4o-mini", "gh/gpt-4o", "ollama/gemma4:31b-cloud"],
        help="Danh sách các mô hình cần đánh giá"
    )
    parser.add_argument("--trials", type=int, default=10, help="Số lượt thử nghiệm cho mỗi mô hình")
    parser.add_argument("--theme", type=str, default="Bí ẩn Biệt thự Blackwood", help="Chủ đề vụ án")

    args = parser.parse_args()
    asyncio.run(run_benchmark(models=args.models, trials=args.trials, theme=args.theme))


if __name__ == "__main__":
    main()
