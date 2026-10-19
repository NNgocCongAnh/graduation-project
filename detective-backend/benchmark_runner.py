"""Cross-Model Benchmark Evaluation Runner.

Compares generation quality, JSON validity, logic consistency pass rate,
localized patch repair effectiveness, and latency across multiple LLM backbones
(e.g., Gemma 3, Qwen 2.5, DeepSeek, GPT-4o-mini).

Usage:
  python benchmark_runner.py --models gpt-4o-mini google/gemma-3-27b-it --trials 3
"""

import os
import sys
import time
import json
import asyncio
import argparse
from typing import List, Dict, Any

from models import CaseDossier
from llm_service import CaseGeneratorService
from validator import validate_case_diagnostics


async def evaluate_single_trial(service: CaseGeneratorService, theme: str) -> Dict[str, Any]:
    """Execute one case generation trial and collect fine-grained telemetry."""
    start_t = time.time()
    try:
        dossier = await service.generate_case(theme=theme, max_retries=2)
        total_lat = round(time.time() - start_t, 2)
        diag = validate_case_diagnostics(dossier)

        return {
            "success": True,
            "json_valid": True,
            "logic_valid": diag.is_valid,
            "violations_count": len(diag.violations),
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
            "patch_retries": 0,
            "latency_sec": total_lat,
            "title": "Failed",
            "reasoning_steps": 0,
            "error": str(e)
        }


async def run_benchmark(models: List[str], trials: int = 3, theme: str = "Bí ẩn Biệt thự Blackwood") -> List[Dict[str, Any]]:
    """Run benchmark across specified models and print comparative summary."""
    all_results: List[Dict[str, Any]] = []

    print("=" * 70)
    print(f"BẮT ĐẦU THỰC NGHIỆM ĐÁNH GIÁ ĐA MÔ HÌNH (Trials={trials}/model)")
    print(f"Chủ đề: '{theme}'")
    print("=" * 70)

    for model in models:
        print(f"\n--- Đang kiểm thử Mô hình: {model} ---")
        service = CaseGeneratorService(model=model)

        for i in range(1, trials + 1):
            print(f"  [Lượt {i:02d}/{trials:02d}] Đang sinh kịch bản...", end="", flush=True)
            res = await evaluate_single_trial(service, theme)
            res["model"] = model
            res["trial"] = i
            all_results.append(res)

            status_mark = "✅ PASS" if res["logic_valid"] else "❌ FAIL"
            print(f" -> {status_mark} (JSON={res['json_valid']}, Sửa lỗi={res['patch_retries']}, Thời gian={res['latency_sec']}s)")

    # Generate Summary Table
    print("\n" + "=" * 70)
    print("BẢNG TỔNG HỢP KẾT QUẢ SO SÁNH CÁC MÔ HÌNH (BENCHMARK SUMMARY)")
    print("=" * 70)
    print(f"{'Mô hình':<28} | {'JSON Đúng':<10} | {'Logic Pass':<10} | {'Sửa TB':<8} | {'Độ trễ TB':<10}")
    print("-" * 74)

    for model in models:
        m_runs = [r for r in all_results if r["model"] == model]
        if not m_runs:
            continue
        json_rate = sum(1 for r in m_runs if r["json_valid"]) / len(m_runs) * 100
        logic_rate = sum(1 for r in m_runs if r["logic_valid"]) / len(m_runs) * 100
        avg_retries = sum(r["patch_retries"] for r in m_runs) / len(m_runs)
        avg_lat = sum(r["latency_sec"] for r in m_runs) / len(m_runs)

        print(f"{model:<28} | {json_rate:>9.1f}% | {logic_rate:>9.1f}% | {avg_retries:>8.1f} | {avg_lat:>8.2f}s")

    print("=" * 70)

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu kết quả chi tiết vào: {output_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="AI Detective Case Engine Multi-Model Benchmark")
    parser.add_argument(
        "--models",
        nargs="+",
        default=[os.getenv("LLM_MODEL", "gpt-4o-mini")],
        help="Danh sách các mô hình cần đánh giá (ví dụ: gpt-4o-mini google/gemma-3-27b-it)"
    )
    parser.add_argument("--trials", type=int, default=2, help="Số lượt thử nghiệm cho mỗi mô hình")
    parser.add_argument("--theme", type=str, default="Bí ẩn Biệt thự Blackwood", help="Chủ đề vụ án")

    args = parser.parse_args()
    asyncio.run(run_benchmark(models=args.models, trials=args.trials, theme=args.theme))


if __name__ == "__main__":
    main()
