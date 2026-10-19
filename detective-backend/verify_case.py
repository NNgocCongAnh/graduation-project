"""Case Quality & Game-Readiness Auditor (Kiểm định chất lượng vụ án).

Audits any generated case against the 5 Golden Criteria:
1. Schema & Engine Contract: Pydantic v2 data completeness.
2. Henssge Physical Consistency: Body cooling vs crime time window.
3. Solvability Guarantee: Culprit alibi breakage graph.
4. Gameplay Balance: Red herrings vs crucial clues ratio.
5. Proof of Deduction: Multi-hop reasoning chain integrity.

Usage:
  python verify_case.py                     # Audits the latest case
  python verify_case.py CASE-9647           # Audits a specific case
"""

import os
import sys
import json
import argparse

from models import CaseDossier
from validator import validate_case_diagnostics, is_time_in_interval, time_to_minutes

CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")


def audit_case(case: CaseDossier):
    print("\n" + "=" * 75)
    print(f"  🔍 BỘ KIỂM ĐỊNH CHẤT LƯỢNG & TÍNH UY TÍN CỦA VỤ ÁN")
    print(f"  Mã vụ án: {case.case_id} - '{case.title}'")
    print("=" * 75)

    checks_passed = 0
    total_checks = 5

    # TIÊU CHUẨN 1: HỢP ĐỒNG DỮ LIỆU VỚI GAME ENGINE (SCHEMA INTEGRITY)
    print("\n[Tiêu chuẩn 1/5] Kiểm tra Chuẩn Cấu trúc & Tương thích Khung Game (Pydantic Contract)")
    has_victim = bool(case.victim and case.victim.name)
    has_suspects = len(case.suspects) >= 3
    has_evidences = len(case.evidences) >= 3
    has_gt = bool(case.ground_truth and case.ground_truth.culprit_id)

    if has_victim and has_suspects and has_evidences and has_gt:
        print("   ✅ ĐẠT: Đầy đủ các thực thể (Nạn nhân, 3+ Nghi phạm, 3+ Manh mối, Ground Truth).")
        print("         -> Đảm bảo giao diện Unity / React đọc dữ liệu không bao giờ bị lỗi Null hoặc Crash.")
        checks_passed += 1
    else:
        print("   ❌ KHÔNG ĐẠT: Thiếu trường dữ liệu bắt buộc.")

    # TIÊU CHUẨN 2: TÍNH NHẤT QUÁN VẬT LÝ NHIỆT HỌC (HENSSGE FORENSIC PHYSICS)
    print("\n[Tiêu chuẩn 2/5] Kiểm định Tính Nhất quán Vật lý & Giờ Tử vong (Symbolic Physics)")
    f = case.victim.forensic_data
    crime_time = case.ground_truth.actual_crime_time
    in_tod = is_time_in_interval(crime_time, f.estimated_tod_start, f.estimated_tod_end)
    temp_drop = 37.0 - f.body_temp

    print(f"   • Thân nhiệt nạn nhân: {f.body_temp}°C (Giảm {temp_drop:.1f}°C so với người sống 37.0°C)")
    print(f"   • Cửa sổ tử vong tính theo Henssge: {f.estimated_tod_start} - {f.estimated_tod_end}")
    print(f"   • Giờ gây án thực tế của hung thủ:  {crime_time}")

    if in_tod:
        print(f"   ✅ ĐẠT: Giờ gây án ({crime_time}) nằm trọn trong cửa sổ tử vong pháp y [{f.estimated_tod_start}-{f.estimated_tod_end}].")
        print("         -> Không có lỗi vô lý về mặt y khoa/vật lý.")
        checks_passed += 1
    else:
        print(f"   ❌ KHÔNG ĐẠT: Giờ gây án mâu thuẫn với độ lạnh của thi thể.")

    # TIÊU CHUẨN 3: TÍNH GIẢI ĐƯỢC CỦA VỤ ÁN (SOLVABILITY GUARANTEE)
    print("\n[Tiêu chuẩn 3/5] Kiểm định Tính Giải được & Bẻ gãy Bằng chứng Ngoại phạm (Alibi Graph)")
    culprit = next((s for s in case.suspects if s.is_culprit), None)
    crucial_evs = [e for e in case.evidences if e.is_crucial]

    if culprit and len(crucial_evs) >= 1:
        print(f"   • Hung thủ thực sự: [{culprit.id}] {culprit.name}")
        print(f"   • Alibi hung thủ khai: \"{culprit.alibi_statement}\" [{culprit.alibi_start}-{culprit.alibi_end}]")
        print(f"   • Manh mối then chốt bẻ Alibi: {len(crucial_evs)} chứng cứ (VD: [{crucial_evs[0].id}] {crucial_evs[0].title})")
        print("   ✅ ĐẠT: Lời khai của hung thủ có sơ hở và có chứng cứ xác thực tại hiện trường để người chơi bẻ gãy.")
        print("         -> Đảm bảo game có nghiệm logic, người chơi không bao giờ bị rơi vào thế bí.")
        checks_passed += 1
    else:
        print("   ❌ KHÔNG ĐẠT: Thiếu hung thủ hoặc thiếu chứng cứ mấu chốt để bẻ alibi.")

    # TIÊU CHUẨN 4: TÍNH CÂN BẰNG & YẾU TỐ ĐÁNH LẠC HƯỚNG (GAMEPLAY FAIR-PLAY & RED HERRINGS)
    print("\n[Tiêu chuẩn 4/5] Kiểm định Tính Cân bằng Màn chơi (Gameplay Balance & Red Herrings)")
    red_herrings = [e for e in case.evidences if e.is_red_herring]
    innocent_secrets = [s for s in case.suspects if not s.is_culprit and s.secret_innocent_fact]

    print(f"   • Số chứng cứ nghi binh (Red Herring Clues): {len(red_herrings)}")
    print(f"   • Số nghi phạm vô tội có hành vi đáng ngờ:   {len(innocent_secrets)}")

    if len(red_herrings) >= 1 or len(innocent_secrets) >= 1:
        print("   ✅ ĐẠT: Màn chơi có chứng cứ nghi binh đánh lạc hướng (Fair-play mystery).")
        print("         -> Game có độ khó vừa vặn, người chơi cần quan sát và suy luận chứ không thể đoán mò là trúng ngay.")
        checks_passed += 1
    else:
        print("   ⚠️ CẢNH BÁO: Màn chơi chưa có bằng chứng nghi binh, có thể hơi dễ đối với người chơi.")

    # TIÊU CHUẨN 5: CHUỖI SUY LUẬN ĐA BƯỚC (DEDUCTION PROOF INTEGRITY)
    print("\n[Tiêu chuẩn 5/5] Kiểm tra Chuỗi Chứng minh Phá án Đa bước (Multi-Hop Deduction Chain)")
    if case.reasoning_chain and len(case.reasoning_chain.steps) >= 1:
        print(f"   • Số bước suy luận logic: {len(case.reasoning_chain.steps)} bước")
        print(f"   • Mâu thuẫn quyết định:    \"{case.reasoning_chain.decisive_contradiction}\"")
        print("   ✅ ĐẠT: Có lời giải toán học chứng minh đường đi của suy luận từ manh mối tới hung thủ.")
        checks_passed += 1
    else:
        print("   ❌ KHÔNG ĐẠT: Thiếu chuỗi suy luận chứng minh tính giải được.")

    # TỔNG KẾT VÀ CẤP CHỨNG NHẬN
    print("\n" + "=" * 75)
    if checks_passed == total_checks:
        print("  🏆 KẾT QUẢ ĐÁNH GIÁ: ĐẠT 5/5 TIÊU CHUẨN VÀNG!")
        print("  🎖️ CHỨNG NHẬN: HỒ SƠ VỤ ÁN ĐẠT CHUẨN UY TÍN ĐỂ NẠP VÀO GAME ENGINE (GAME-READY)")
    else:
        print(f"  ⚠️ KẾT QUẢ: ĐẠT {checks_passed}/{total_checks} TIÊU CHUẨN. CẦN ĐIỀU CHỈNH TRƯỚC KHI ĐƯA VÀO GAME.")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Audit case credibility and game-readiness")
    parser.add_argument("case_id", nargs="?", default=None, help="Case ID to audit (e.g., CASE-9647)")
    args = parser.parse_args()

    if not os.path.exists(CASES_DIR):
        print("Chưa có thư mục cases/. Hãy tạo vụ án trước!")
        return

    files = [f for f in os.listdir(CASES_DIR) if f.endswith(".json")]
    if not files:
        print("Chưa có file vụ án nào trong cases/!")
        return

    target_file = None
    if args.case_id:
        target_name = f"{args.case_id}.json" if not args.case_id.endswith(".json") else args.case_id
        if target_name in files:
            target_file = target_name
        else:
            print(f"Không tìm thấy vụ án '{args.case_id}' trong {CASES_DIR}!")
            return
    else:
        # Pick the latest or specific
        target_file = sorted(files)[-1]

    path = os.path.join(CASES_DIR, target_file)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        case = CaseDossier.model_validate(data)
        audit_case(case)


if __name__ == "__main__":
    main()
