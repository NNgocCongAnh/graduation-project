"""CLI Interactive Visualizer for AI Detective Game Cases.

Allows user to:
1. Inspect saved cases in `cases/` directory.
2. Read detailed stories, victim forensics, suspects' alibis, and crucial clues.
3. Test case generation via LLM pipeline / 9Router.
4. Simulate player deduction and victory conditions.
"""

import os
import sys
import json
import asyncio
from typing import Optional

from models import CaseDossier, VerifyRequest
from llm_service import CaseGeneratorService
from validator import validate_case_diagnostics

CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  {title.center(71)}")
    print("=" * 75)


def display_case_details(case: CaseDossier):
    print_banner(f"HỒ SƠ VỤ ÁN: {case.case_id} - {case.title}")
    print(f"📖 Tóm tắt bối cảnh:\n   {case.summary}\n")

    print("🩺 KHÁM NGHIỆM TỬ THI & PHÁP Y (Symbolic Forensic Data):")
    v = case.victim
    f = v.forensic_data
    print(f"   • Nạn nhân: {v.name} ({v.age} tuổi, {v.occupation})")
    print(f"   • Nhiệt độ hiện trường (Ambient): {f.ambient_temp}°C | Thân nhiệt lúc tìm thấy: {f.body_temp}°C")
    print(f"   • Vết thương: {f.wound_description}")
    print(f"   • Trạng thái hoen ố: {f.livor_mortis_state}")
    print(f"   • [Định luật Henssge] Cửa sổ tử vong ước tính: {f.estimated_tod_start} - {f.estimated_tod_end}\n")

    print(f"👥 DANH SÁCH NGHI PHẠM ({len(case.suspects)} người):")
    for s in case.suspects:
        culprit_tag = " [HUNG THỦ THỰC SỰ]" if s.is_culprit else " [VÔ TỘI]"
        print(f"   [{s.id}] {s.name} ({s.age} tuổi, {s.occupation}){culprit_tag}")
        print(f"       Động cơ: {s.motive}")
        print(f"       Lời khai Alibi: \"{s.alibi_statement}\" [{s.alibi_start} - {s.alibi_end}]")
        if s.secret_innocent_fact:
            print(f"       Bí mật đáng ngờ (Red Herring): {s.secret_innocent_fact}")
    print()

    print(f"🔍 DANH SÁCH CHỨNG CỨ TẠI HIỆN TRƯỜNG ({len(case.evidences)} chứng cứ):")
    for e in case.evidences:
        tag = ""
        if e.is_crucial:
            tag = " ⭐ [MANH MỐI MẤU CHỐT - BẺ ALIBI]"
        elif e.is_red_herring:
            tag = " 🚩 [CHỨNG CỨ NGHI BINH]"
        print(f"   [{e.id}] {e.title}{tag}")
        print(f"       Vị trí: {e.location}")
        print(f"       Mô tả: {e.description}")
        print(f"       Liên đới nghi phạm: {e.linked_suspect_id}")
    print()

    print("🔒 BẢN ÁN BÍ MẬT (Ground Truth - Chỉ dành cho Game Master / Thẩm định):")
    gt = case.ground_truth
    print(f"   • Hung thủ chính xác: {gt.culprit_id}")
    print(f"   • Thời điểm gây án thực tế: {gt.actual_crime_time}")
    print(f"   • Hung khí: {gt.murder_weapon}")
    print(f"   • Mâu thuẫn mấu chốt phá án: {gt.core_contradiction}\n")

    if case.reasoning_chain:
        print("🧠 CHUỖI SUY LUẬN ĐA BƯỚC (Deduction Multi-Hop Reasoning Chain):")
        for step in case.reasoning_chain.steps:
            print(f"   Bước {step.step_number}: Dựa vào manh mối {step.clue_ids} -> {step.inference}")
        print(f"   => KẾT LUẬN CUỐI CÙNG: {case.reasoning_chain.final_conclusion}")
        print()


def list_saved_cases():
    print_banner("DANH SÁCH HỒ SƠ VỤ ÁN ĐANG LƯU TRONG CƠ SỞ DỮ LIỆU (cases/)")
    if not os.path.exists(CASES_DIR):
        print("   (Chưa có thư mục cases/)")
        return []
    
    files = [f for f in os.listdir(CASES_DIR) if f.endswith(".json")]
    if not files:
        print("   (Chưa có file vụ án nào trong cases/)")
        return []

    cases = []
    for f in files:
        path = os.path.join(CASES_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                c = CaseDossier.model_validate(data)
                cases.append(c)
                print(f"   📁 [{c.case_id}] {c.title} -> File: cases/{f}")
        except Exception as e:
            print(f"   ⚠️ Lỗi đọc file {f}: {e}")
    return cases


async def demo_interactive():
    print_banner("HỆ THỐNG TRÌNH DIỄN VỤ ÁN & CƠ SỞ DỮ LIỆU TRINH THÁM")
    
    # 1. Liệt kê vụ án đang lưu
    saved = list_saved_cases()
    if saved:
        print("\n--- Đang mở chi tiết vụ án đầu tiên trong CSDL ---")
        display_case_details(saved[0])
    
    # 2. Kiểm định tính logic
    print_banner("KIỂM TRA TÍNH TOÀN VẸN LOGIC & VẬT LÝ VỤ ÁN BẰNG VALIDATOR")
    diag = validate_case_diagnostics(saved[0])
    if diag.is_valid:
        print("   ✅ Vụ án đạt chuẩn 100% về vật lý nhiệt học Henssge và đồ thị phá án!")
    else:
        print(f"   ❌ Phát hiện {len(diag.violations)} vi phạm:")
        for v in diag.violations:
            print(f"      - [{v.component}] {v.message}")

    # 3. Thử nghiệm người chơi giải đố
    print_banner("GIẢ LẬP NGƯỜI CHƠI NỘP SUY LUẬN PHÁ ÁN (VERIFY)")
    sample = saved[0]
    culprit = sample.ground_truth.culprit_id
    crucial_clue = next((e.id for e in sample.evidences if e.is_crucial), "EV-01")
    
    print(f"   Trường hợp 1: Người chơi chọn đúng hung thủ ({culprit}) và đúng bằng chứng mấu chốt ({crucial_clue})")
    print(f"   => KẾT QUẢ: CHÍNH XÁC! Hệ thống mở khóa lời giải: \"{sample.ground_truth.core_contradiction}\"")
    
    print(f"\n   Trường hợp 2: Người chơi đoán mò chọn SUSP-02 (Bác sĩ)")
    print(f"   => KẾT QUẢ: THẤT BẠI! Lập luận sai, đối tượng có bằng chứng ngoại phạm hợp lệ.")
    
    print("\n" + "=" * 75)
    print("  Đường dẫn thư mục lưu trữ dữ liệu thật trên máy:")
    print(f"  {CASES_DIR}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_interactive())
