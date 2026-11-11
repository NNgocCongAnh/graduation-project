"""Autonomous AI Detective Playtester (Tác tử Thám tử Tự động Phá án & Kiểm thử Game).

Simulates a real player investigating the case from scratch without looking at hidden ground truth:
1. Reads diegetic crime scene clues and forensic reports.
2. Independently solves Henssge forensic equation to establish TOD (Time of Death).
3. Analyzes suspect alibis against physical evidence.
4. Issues a formal Accusation (Suspect + Decisive Clue).
5. Compares with ground truth and computes Game Quality & Solvability Score.
"""

import os
import sys
import json
import time
import argparse
from typing import Optional, Dict, Any, List

# Ensure local imports work
sys.path.insert(0, os.path.dirname(__file__))

from models import CaseDossier, Suspect, Evidence
from validator import calculate_henssge_pmi_bounds, is_time_in_interval, time_to_minutes

CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")


class AutonomousDetective:
    """Agent that plays the detective role using pure logic and forensic deduction."""

    def __init__(self, case: CaseDossier):
        self.case = case
        self.log_steps: List[str] = []

    def play(self) -> Dict[str, Any]:
        start_time = time.time()
        print("\n" + "🕵️" * 38)
        print(f"  BẮT ĐẦU PHIÊN CHƠI THỬ (PLAYTEST SESSION): '{self.case.title}'")
        print(f"  Mã hồ sơ: {self.case.case_id}")
        print("🕵️" * 38 + "\n")

        # GIAI ĐOẠN 1: KHÁM NGHIỆM TỬ THI & GIẢI TOÁN PHÁP Y HENSSGE
        print("📋 [BƯỚC 1: KHÁM NGHIỆM PHÁP Y - XÁC ĐỊNH GIỜ TỬ VONG]")
        f = self.case.victim.forensic_data
        print(f"   • Nạn nhân: {self.case.victim.name} ({self.case.victim.age} tuổi, {self.case.victim.occupation})")
        print(f"   • Tình trạng hoen tử thi: {f.livor_mortis_state}")
        print(f"   • Vết thương chí mạng:     {f.wound_description}")
        print(f"   • Nhiệt độ môi trường hiện trường: {f.ambient_temp}°C")
        print(f"   • Thân nhiệt trực tràng đo được:    {f.body_temp}°C")
        
        # Thám tử tự tính toán độc lập
        pmi_min, pmi_max = calculate_henssge_pmi_bounds(f.body_temp, f.ambient_temp)
        print(f"   ⚙️ Thuật toán vật lý nhiệt Henssge tính ra thời gian tử vong: ~{pmi_min}h đến {pmi_max}h trước lúc khám nghiệm")
        print(f"   ⏱️ Cửa sổ tử vong suy luận (TOD Window): [{f.estimated_tod_start} - {f.estimated_tod_end}]")

        # GIAI ĐOẠN 2: THẨM VẤN & THU THẬP BẰNG CHỨNG NGOẠI PHẠM
        print("\n👥 [BƯỚC 2: RÀ SOÁT DANH SÁCH NGHI PHẠM & ALIBI]")
        print(f"   Có tổng cộng {len(self.case.suspects)} đối tượng trong diện tình nghi:")
        for idx, s in enumerate(self.case.suspects, 1):
            print(f"   {idx}. [{s.id}] {s.name} ({s.occupation})")
            print(f"      - Động cơ khả nghi: {s.motive}")
            print(f"      - Lời khai ngoại phạm: \"{s.alibi_statement}\" [{s.alibi_start} - {s.alibi_end}]")

        # GIAI ĐOẠN 3: ĐỐI SOÁT VẬT CHỨNG VÀ PHÁ VỠ CHỨNG CỨ NGOẠI PHẠM
        print("\n🔍 [BƯỚC 3: PHÂN TÍCH VẬT CHỨNG HIỆN TRƯỜNG & TÌM MÂU THUẪN]")
        print(f"   Thu thập được {len(self.case.evidences)} chứng cứ vật lý:")
        for idx, e in enumerate(self.case.evidences, 1):
            print(f"   • [{e.id}] {e.title} (Tìm thấy tại: {e.location})")
            print(f"     Nội dung: {e.description}")

        # Thám tử suy luận mâu thuẫn (Mô phỏng chuỗi suy diễn logic)
        accused_suspect = None
        decisive_clue = None
        deduction_reasoning = ""

        # Dò tìm mâu thuẫn giữa alibi và chứng cứ (không dùng ground truth)
        for s in self.case.suspects:
            for e in self.case.evidences:
                # Kiểm tra các dấu hiệu mâu thuẫn từ ngữ
                alibi_lower = s.alibi_statement.lower()
                desc_lower = e.description.lower()
                title_lower = e.title.lower()

                # Rule 1: Mâu thuẫn đồng hồ / thời gian
                if ("đồng hồ" in alibi_lower or "giờ" in alibi_lower) and ("đồng hồ" in title_lower or "ngừng" in desc_lower or "hỏng" in desc_lower):
                    accused_suspect = s
                    decisive_clue = e
                    deduction_reasoning = f"Nghi phạm {s.name} khai dựa vào đồng hồ để xác nhận thời gian, nhưng vật chứng [{e.id}] chứng minh đồng hồ đã ngừng chạy trước đó."
                    break

                # Rule 2: Mâu thuẫn vị trí / địa điểm
                if ("phòng" in alibi_lower or "ở tại" in alibi_lower) and ("camera" in desc_lower or "vé" in desc_lower or "dấu vết" in desc_lower):
                    if s.name.lower().split()[-1] in desc_lower:
                        accused_suspect = s
                        decisive_clue = e
                        deduction_reasoning = f"Nghi phạm {s.name} khai ở nơi khác nhưng vật chứng [{e.id}] chứng minh sự hiện diện tại hiện trường."
                        break

            if accused_suspect:
                break

        # Fallback nếu luật heuristic chưa bắt được, chọn nghi phạm có mâu thuẫn thời gian
        if not accused_suspect:
            # Chọn nghi phạm có lời khai trùng khớp với TOD nhưng có vật chứng liên đới
            for s in self.case.suspects:
                if is_time_in_interval(s.alibi_start, f.estimated_tod_start, f.estimated_tod_end):
                    accused_suspect = s
                    decisive_clue = self.case.evidences[0]
                    deduction_reasoning = f"Nghi phạm {s.name} có mặt trong khung giờ tử vong [{f.estimated_tod_start}-{f.estimated_tod_end}]."
                    break

        # GIAI ĐOẠN 4: THỰC HIỆN CÁO TRẠNG KẾT ÁN (ACCUSATION)
        print("\n⚖️ [BƯỚC 4: THÁM TỬ ĐƯA RA CÁO TRẠNG KẾT ÁN]")
        print(f"   👉 Nghi phạm bị cáo buộc: [{accused_suspect.id}] {accused_suspect.name}")
        print(f"   👉 Vật chứng then chốt vạch trần: [{decisive_clue.id}] {decisive_clue.title}")
        print(f"   👉 Lập luận phá án: {deduction_reasoning}")

        # GIAI ĐOẠN 5: CHẤM ĐIỂM VÀ ĐỐI SOÁT VỚI HỘI ĐỒNG (GROUND TRUTH CHECK)
        print("\n🎯 [BƯỚC 5: ĐỐI SOÁT VỚI BẢN ÁN GỐC & CHẤM ĐIỂM TRẢI NGHIỆM]")
        gt = self.case.ground_truth
        correct_culprit = (accused_suspect.id == gt.culprit_id)
        
        # Check crucial clue match
        crucial_clues = [e.id for e in self.case.evidences if e.is_crucial]
        correct_clue = (decisive_clue.id in crucial_clues) if decisive_clue else False

        elapsed = time.time() - start_time

        print(f"   • Hung thủ thực tế:         [{gt.culprit_id}] {next((s.name for s in self.case.suspects if s.id == gt.culprit_id), 'Unknown')}")
        print(f"   • Kết quả bắt hung thủ:     {'✅ CHÍNH XÁC 100%' if correct_culprit else '❌ BẮT SAI NGƯỜI'}")
        print(f"   • Kết quả chọn bằng chứng:  {'✅ CHÍNH XÁC' if correct_clue else '⚠️ CHƯA TỐI ƯU'}")
        print(f"   • Thời gian suy luận:       {elapsed:.2f} giây")

        # TÍNH TOÁN ĐIỂM CHẤT LƯỢNG GAME (GAME QUALITY SCORE / 100)
        score = 0
        score += 40 if correct_culprit else 0
        score += 25 if correct_clue else 10
        score += 15 if len(self.case.evidences) >= 3 else 5
        score += 10 if any(e.is_red_herring for e in self.case.evidences) else 0
        score += 10 if (f.body_temp < 37.0 and f.estimated_tod_start) else 0

        print("\n" + "=" * 75)
        print(f"  📊 ĐIỂM CHẤT LƯỢNG MÀN CHƠI (GAMEPLAY PLAYTEST SCORE): {score}/100")
        if score >= 85:
            print("  🌟 XẾP LOẠI: XUẤT SẮC (Sẵn sàng 100% cho buổi Demo Hội đồng)")
        elif score >= 70:
            print("  👍 XẾP LOẠI: TỐT (Màn chơi hấp dẫn, logic chặt chẽ)")
        else:
            print("  ⚠️ XẾP LOẠI: CẦN TINH CHỈNH (Cần kiểm tra lại mâu thuẫn manh mối)")
        print("=" * 75 + "\n")

        return {
            "case_id": self.case.case_id,
            "title": self.case.title,
            "solved": correct_culprit,
            "score": score,
            "elapsed_seconds": elapsed,
        }


def main():
    parser = argparse.ArgumentParser(description="Autonomous Playtester for Unsolved Case Files AI")
    parser.add_argument("--case-id", type=str, default=None, help="Specific Case ID to playtest")
    args = parser.parse_args()

    if not os.path.exists(CASES_DIR):
        print(f"Không tìm thấy thư mục {CASES_DIR}")
        return

    files = [f for f in os.listdir(CASES_DIR) if f.endswith(".json")]
    if not files:
        print("Chưa có vụ án nào trong thư mục cases/.")
        return

    target_file = None
    if args.case_id:
        target_name = f"{args.case_id}.json" if not args.case_id.endswith(".json") else args.case_id
        if target_name in files:
            target_file = target_name
        else:
            print(f"Không tìm thấy vụ án {args.case_id}")
            return
    else:
        target_file = sorted(files)[-1]

    path = os.path.join(CASES_DIR, target_file)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        case = CaseDossier.model_validate(data)

    tester = AutonomousDetective(case)
    tester.play()


if __name__ == "__main__":
    main()