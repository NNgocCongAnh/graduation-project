"""Independent Solver Agent & Solvability Evaluation Benchmark (Mục III.A4).

Simulates an autonomous human player / detective analyzing the case purely from
the player-facing client dossier (ClientCaseDossier):
- Ground Truth is stripped (no culprit flag, no crucial/red-herring labels, no solution).
- The Solver Agent must independently:
  1. Deduce the true Henssge Time of Death (TOD) window from forensic data.
  2. Cross-examine suspects' alibis against the estimated TOD.
  3. Filter out red herrings and identify crucial decisive physical evidences.
  4. Formulate formal accusation: accused_id, selected_evidence_ids, and reasoning rationale.
- The accusation is evaluated deterministically by evaluate_player_deduction().
- Measures:
  - Culprit Identification Accuracy (%)
  - Crucial Evidence Recall & Precision (%)
  - Red-Herring Trap Rate (%)
  - Solvability Score (0 - 100)
  - Solving Latency and Token Footprint
"""

import os
import sys
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import CaseDossier, ClientCaseDossier, VerifyResponse, DeductionVerdict
from validator import evaluate_player_deduction, validate_case_diagnostics
from llm_service import CaseGeneratorService


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


class IndependentSolverAgent:
    """Autonomous Detective Agent analyzing locked-room mysteries purely from player perspective."""

    def __init__(self, client: AsyncOpenAI, model: str = "gh/gpt-4o-mini"):
        self.client = client
        self.model = model
        self.last_usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    async def solve_case(self, client_dossier: ClientCaseDossier) -> Dict[str, Any]:
        """Examine client case dossier and generate structured deduction accusation."""
        suspects_info = []
        for s in client_dossier.suspects:
            suspects_info.append(
                f"- ID: {s.id} | Tên: {s.name} | Tuổi: {s.age} | Nghề nghiệp: {s.occupation}\n"
                f"  Quan hệ nạn nhân: {s.relationship_to_victim} | Nơi ở/Khoang: {s.residence}\n"
                f"  Động cơ tiềm ẩn: {s.motive}\n"
                f"  Khung giờ ngoại phạm khai báo: {s.alibi_start} - {s.alibi_end}\n"
                f"  Lời khai tóm tắt: {s.alibi_statement}\n"
                f"  Biên bản thẩm vấn chi tiết: {s.statement or 'Không có'}\n"
                f"  Ghi chú điều tra: {s.interview_notes or 'Bình thường'}"
            )
        suspects_text = "\n\n".join(suspects_info)

        evidences_info = []
        for ev in client_dossier.evidences:
            evidences_info.append(
                f"- ID: {ev.id} | Tên: {ev.title} | Vị trí tìm thấy: {ev.location}\n"
                f"  Miêu tả vật thể: {ev.description}\n"
                f"  Giám định vân tay: {ev.fingerprint_analysis or 'Không có'}\n"
                f"  Giám định máu & ADN: {ev.blood_dna_analysis or 'Không có'}\n"
                f"  Hiện trạng cơ học/vật lý: {ev.physical_condition or 'Bình thường'}"
            )
        evidences_text = "\n\n".join(evidences_info)

        v = client_dossier.victim
        fd = v.forensic_data
        forensic_text = (
            f"Nạn nhân: {v.name} ({v.age} tuổi, {v.occupation})\n"
            f"Thời điểm phát hiện thi thể: {fd.discovery_time}\n"
            f"Khung giờ tử vong ước tính trong Báo cáo Giám định Y pháp (Henssge TOD): [{fd.estimated_tod_start} - {fd.estimated_tod_end}]\n"
            f"Nhiệt độ trực tràng đo được: {fd.body_temp}°C (Nhiệt độ phòng/môi trường: {fd.ambient_temp}°C)\n"
            f"Thể trọng: {fd.body_weight_kg} kg | Hệ số làm lạnh môi trường (C): {fd.cooling_factor}\n"
            f"Tình trạng hoen tử thi (Livor Mortis): {fd.livor_mortis_state}\n"
            f"Tình trạng co cứng (Rigor Mortis): {fd.rigor_mortis_state}\n"
            f"Nguyên nhân tử vong: {fd.cause_of_death}\n"
            f"Mô tả vết thương: {fd.wound_description}"
        )

        system_prompt = (
            "Bạn là Đại Thám tử Điều tra Độc lập (Independent Detective Solver Agent). "
            "Nhiệm vụ của bạn là phá án vụ án mạng phòng kín dựa trên hồ sơ vụ án dành cho người chơi. "
            "TUYỆT ĐỐI CÔNG BẰNG (FAIR-PLAY): Bạn KHÔNG BIẾT TRƯỚC đáp án ngầm, không có cờ gian lận. "
            "Hãy tiến hành suy luận trinh thám cổ điển theo các bước: "
            "1. Xác định khung giờ tử vong thực tế: Đọc kỹ Khung giờ tử vong ước tính [estimated_tod_start - estimated_tod_end] do bác sĩ pháp y kết luận trong Báo cáo Giám định. "
            "2. Kiểm tra ngoại phạm và lật tẩy mâu thuẫn: Đối chiếu khung giờ tử vong thực tế này với lời khai ngoại phạm của từng nghi phạm. "
            "Hung thủ thực sự là người khẳng định mình có bằng chứng ngoại phạm che phủ khung giờ tử vong này, nhưng lời khai đó mâu thuẫn với một hiện trạng vật lý khách quan trong danh sách vật chứng (ví dụ thiết bị lạnh ngắt, sổ điều độ ghi nhận không có mặt, mất điện, máy móc không hoạt động). "
            "3. Loại trừ nghi phạm vô tội (Red Herrings): Các nghi phạm vô tội có thể có hành vi lén lút hoặc động cơ mờ ám, nhưng họ không có mặt tại hiện trường lúc án mạng xảy ra, hoặc manh mối liên quan đến họ chỉ là sai phạm thứ yếu (không phải án mạng). "
            "4. Chọn vật chứng then chốt: Chọn ra 1 đến 2 vật chứng quyết định (is_crucial) gồm: vật chứng vật lý/tài liệu vạch trần mâu thuẫn trong lời khai hung thủ, và/hoặc hung khí thật sự dính máu nạn nhân có dấu vết kỹ thuật độc quyền của hung thủ. "
            "5. Ra phán quyết: Chọn chính xác mã nghi phạm (accused_id), danh sách vật chứng then chốt (selected_evidence_ids), và trình bày lập luận chặt chẽ (reasoning)."
        )

        user_prompt = f"""
TIÊU ĐỀ VỤ ÁN: {client_dossier.title}
TÓM TẮT HIỆN TRƯỜNG: {client_dossier.summary}

=== BÁO CÁO PHÁP Y TỬ THI ===
{forensic_text}

=== DANH SÁCH NGHI PHẠM & LỜI KHAI ===
{suspects_text}

=== DANH SÁCH VẬT CHỨNG HIỆN TRƯỜNG ===
{evidences_text}

YÊU CẦU ĐẦU RA JSON CHUẨN:
{{
  "estimated_tod_analysis": "<Phân tích tính toán khung giờ tử vong thực tế theo Henssge>",
  "suspects_alibi_analysis": "<Phân tích đối chiếu lời khai và loại trừ nghi phạm vô tội>",
  "accused_id": "<Mã nghi phạm hung thủ: SUSP-01, SUSP-02, hoặc SUSP-03>",
  "selected_evidence_ids": ["<Mã vật chứng then chốt 1>", "<Mã vật chứng then chốt 2>"],
  "reasoning": "<Lập luận phân tích mâu thuẫn thời gian tử vong và vật chứng kết tội>"
}}
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,  # Low temperature for analytical deduction rigor
        )

        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if getattr(response, "usage", None):
            usage["prompt_tokens"] = getattr(response.usage, "prompt_tokens", 0) or 0
            usage["completion_tokens"] = getattr(response.usage, "completion_tokens", 0) or 0
            usage["total_tokens"] = getattr(response.usage, "total_tokens", 0) or 0
        self.last_usage = usage

        raw_text = response.choices[0].message.content or "{}"
        try:
            return json.loads(raw_text)
        except Exception:
            # Fallback extraction
            import re
            m = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            return {"accused_id": "SUSP-01", "selected_evidence_ids": [], "reasoning": "Parse failed"}


async def run_solver_benchmark(
    api_base: str = "http://localhost:20128/v1",
    api_key: str = "",
    model: str = "gh/gpt-4o-mini",
    target_cases_count: int = 20,
    output_path: str = "detective-backend/solver_benchmark_results.json"
):
    print("=" * 80)
    print("INDEPENDENT SOLVER AGENT BENCHMARK (Mục III.A4: Solvability Evaluation)")
    print(f"Solver Model: {model} | API Base: {api_base}")
    print(f"Target test cases: {target_cases_count}")
    print("=" * 80)

    client = AsyncOpenAI(base_url=api_base, api_key=api_key)
    solver = IndependentSolverAgent(client, model)
    case_gen = CaseGeneratorService(api_base=api_base, api_key=api_key, model=model)

    # 1. Collect Valid Benchmark Cases
    cases: List[CaseDossier] = []
    db_path = os.path.join(os.path.dirname(__file__), "detective.db")
    if os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        rows = cur.execute("SELECT case_id, dossier_json FROM cases").fetchall()
        for cid, djson in rows:
            try:
                data = json.loads(djson)
                c = CaseDossier.model_validate(data)
                if validate_case_diagnostics(c).is_valid:
                    cases.append(c)
            except Exception:
                pass
        con.close()
    print(f"[SolverBenchmark] Loaded {len(cases)} valid cases from database.")

    # If we need more cases to reach target_cases_count, generate fresh valid cases
    themes = [
        "Bí ẩn Biệt thự Cổ Blackwood",
        "Chuyến tàu đêm Thống Nhất",
        "Phòng Thí nghiệm Công nghệ cao CyberTech"
    ]
    theme_idx = 0
    while len(cases) < target_cases_count:
        th = themes[theme_idx % len(themes)]
        theme_idx += 1
        print(f"[SolverBenchmark] Generating fresh case {len(cases)+1}/{target_cases_count} with theme '{th}'...")
        try:
            new_case = await case_gen.generate_case(theme=th)
            diag = validate_case_diagnostics(new_case)
            if diag.is_valid:
                cases.append(new_case)
                print(f"  -> Generated valid case: '{new_case.title}' ({new_case.case_id})")
            else:
                print(f"  -> Case invalid ({len(diag.violations)} violations), retrying...")
        except Exception as ex:
            print(f"  -> Error generating case: {ex}")

    cases = cases[:target_cases_count]
    print(f"\n[SolverBenchmark] Benchmark dataset ready: {len(cases)} fully verified locked-room mystery cases.")

    # 2. Run Independent Solver Agent on Each Case
    results: List[Dict[str, Any]] = []
    correct_culprit_count = 0
    crucial_evidence_found_count = 0
    red_herrings_avoided_count = 0
    perfect_verdict_count = 0
    scores: List[float] = []
    latencies: List[float] = []
    total_tokens: List[int] = []

    for idx, case in enumerate(cases):
        print(f"\n---> [Case {idx+1:02d}/{len(cases)}] Solving '{case.title}' ({case.case_id})...")

        # Step 1: Strip ground truth to produce ClientCaseDossier
        client_dossier = case.to_client_dossier()

        # Step 2: Solver Agent deduces solution independently
        t0 = time.perf_counter()
        solver_output = await solver.solve_case(client_dossier)
        lat = round(time.perf_counter() - t0, 2)

        accused_id = solver_output.get("accused_id", "").strip()
        selected_evidence_ids = solver_output.get("selected_evidence_ids", [])
        reasoning = solver_output.get("reasoning", "")
        tod_analysis = solver_output.get("estimated_tod_analysis", "")

        # Step 3: Neuro-Symbolic Verification of the Accusation
        verdict_resp: VerifyResponse = evaluate_player_deduction(
            case=case,
            accused_id=accused_id,
            selected_clue_ids=selected_evidence_ids,
            reasoning=reasoning
        )

        is_culprit_ok = verdict_resp.culprit_identified
        is_crucial_ok = verdict_resp.crucial_evidences_identified
        herrings_count = verdict_resp.red_herrings_selected_count
        score = verdict_resp.score
        verdict_str = verdict_resp.verdict.value if hasattr(verdict_resp.verdict, "value") else str(verdict_resp.verdict)

        if is_culprit_ok:
            correct_culprit_count += 1
        if is_crucial_ok:
            crucial_evidence_found_count += 1
        if herrings_count == 0:
            red_herrings_avoided_count += 1
        if verdict_str == "solved_perfect":
            perfect_verdict_count += 1

        scores.append(score)
        latencies.append(lat)
        tokens = solver.last_usage.get("total_tokens", 0)
        total_tokens.append(tokens)

        # Log to deduction_logs in SQLite database for persistent telemetry
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("""
                INSERT INTO deduction_logs (
                    case_id, session_id, accused_id, selected_evidence_ids_json,
                    is_correct, verdict, culprit_identified, crucial_evidences_identified,
                    found_crucial_count, total_crucial_count, red_herrings_selected_count,
                    irrelevant_clues_count, score, feedback, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                case.case_id,
                f"SOLVER-AGENT-{model}",
                accused_id,
                json.dumps(selected_evidence_ids),
                1 if verdict_resp.is_correct else 0,
                verdict_str,
                1 if is_culprit_ok else 0,
                1 if is_crucial_ok else 0,
                verdict_resp.found_crucial_count,
                verdict_resp.total_crucial_count,
                herrings_count,
                verdict_resp.irrelevant_clues_count,
                score,
                verdict_resp.feedback
            ))
            con.commit()
            con.close()
        except Exception as db_err:
            print(f"  [DB Log Warning] Could not log to deduction_logs: {db_err}")

        case_record = {
            "trial": idx + 1,
            "case_id": case.case_id,
            "title": case.title,
            "ground_truth_culprit_id": case.ground_truth.culprit_id,
            "accused_id": accused_id,
            "culprit_identified": is_culprit_ok,
            "ground_truth_crucial_clues": [e.id for e in case.evidences if e.is_crucial],
            "ground_truth_red_herrings": [e.id for e in case.evidences if e.is_red_herring],
            "selected_evidence_ids": selected_evidence_ids,
            "crucial_evidences_identified": is_crucial_ok,
            "red_herrings_selected_count": herrings_count,
            "verdict": verdict_str,
            "score": score,
            "latency_sec": lat,
            "tokens": solver.last_usage,
            "solver_tod_analysis": tod_analysis,
            "solver_reasoning": reasoning,
            "verifier_feedback": verdict_resp.feedback
        }
        results.append(case_record)

        print(f"  Result: Accused: '{accused_id}' (True: '{case.ground_truth.culprit_id}') -> {'CORRECT' if is_culprit_ok else 'WRONG'}")
        print(f"  Verdict: {verdict_str} | Score: {score:.1f} | Crucial Found: {verdict_resp.found_crucial_count}/{verdict_resp.total_crucial_count} | Herrings: {herrings_count}")
        print(f"  Time: {lat:.2f}s | Tokens: {tokens}")

        await asyncio.sleep(1.0)

    # 3. Aggregate Statistical Summary
    n = len(results)
    culprit_acc = round((correct_culprit_count / n) * 100.0, 2)
    culprit_ci = calc_wilson_ci(correct_culprit_count, n)
    crucial_acc = round((crucial_evidence_found_count / n) * 100.0, 2)
    crucial_ci = calc_wilson_ci(crucial_evidence_found_count, n)
    herring_avoidance = round((red_herrings_avoided_count / n) * 100.0, 2)
    herring_ci = calc_wilson_ci(red_herrings_avoided_count, n)
    perfect_rate = round((perfect_verdict_count / n) * 100.0, 2)
    mean_score = round(sum(scores) / n, 2)
    p50_lat = calc_percentile(latencies, 0.50)
    p95_lat = calc_percentile(latencies, 0.95)
    mean_tokens = round(sum(total_tokens) / n, 1)

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "solver_model": model,
        "api_base": api_base,
        "total_cases_evaluated": n,
        "culprit_identification_rate_pct": culprit_acc,
        "culprit_identification_wilson_ci_95": culprit_ci,
        "crucial_evidence_identification_rate_pct": crucial_acc,
        "crucial_evidence_wilson_ci_95": crucial_ci,
        "red_herring_avoidance_rate_pct": herring_avoidance,
        "red_herring_trap_rate_pct": round(100.0 - herring_avoidance, 2),
        "perfect_verdict_rate_pct": perfect_rate,
        "mean_score": mean_score,
        "latency_p50_sec": p50_lat,
        "latency_p95_sec": p95_lat,
        "mean_tokens": mean_tokens,
        "cases": results
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("SOLVER AGENT BENCHMARK COMPLETED SUCCESSFULLY!")
    print(f"Results saved to: {output_path}")
    print(f"Culprit Identification Accuracy: {culprit_acc}% [{culprit_ci[0]} - {culprit_ci[1]}] ({correct_culprit_count}/{n})")
    print(f"Crucial Clue Identification: {crucial_acc}% [{crucial_ci[0]} - {crucial_ci[1]}] ({crucial_evidence_found_count}/{n})")
    print(f"Red-Herring Avoidance Rate: {herring_avoidance}% ({red_herrings_avoided_count}/{n})")
    print(f"Mean Deduction Score: {mean_score}/100 | Perfect Solved Rate: {perfect_rate}%")
    print(f"Latency P50: {p50_lat}s (P95: {p95_lat}s) | Mean Tokens: {mean_tokens}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Independent Solver Agent Solvability Benchmark")
    parser.add_argument("--model", type=str, default="gh/gpt-4o-mini", help="Solver model identifier")
    parser.add_argument("--api-base", type=str, default="http://localhost:20128/v1", help="API base URL")
    parser.add_argument("--api-key", type=str, default=os.getenv("LLM_API_KEY", ""), help="API key (defaults to LLM_API_KEY env var)")
    parser.add_argument("--cases", type=int, default=20, help="Number of cases to evaluate")
    parser.add_argument("--output", type=str, default="detective-backend/solver_benchmark_results.json", help="Output JSON path")
    args = parser.parse_args()

    asyncio.run(
        run_solver_benchmark(
            api_base=args.api_base,
            api_key=args.api_key,
            model=args.model,
            target_cases_count=args.cases,
            output_path=args.output
        )
    )
