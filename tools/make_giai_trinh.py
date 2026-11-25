"""Generate the response-to-advisor document (.docx) from raw result files,
matching the layout and section structure of TS. Nguyen Van Thanh's review."""
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
BE = ROOT / "detective-backend"
OUT = ROOT / "GIAI_TRINH_GOP_Y_GVHD_22010201.docx"


def detect_git_ref() -> str:
    if len(sys.argv) > 2:
        return sys.argv[2]
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip()
        if dirty:
            return f"{head} (kèm bản cập nhật đang hoàn thiện trên nhánh làm việc)"
        return head
    except Exception:
        return "(đang cập nhật)"


COMMIT = detect_git_ref()


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * min(1.0, c + h)


def vn(x: float, nd: int = 2) -> str:
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def stats(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    n = len(d)
    lat = [r["latency_sec"] for r in d]
    k_logic = sum(bool(r["logic_valid"]) for r in d)
    k_llm_logic = sum(bool(r["logic_valid"]) and not bool(r.get("used_fallback_sample")) for r in d)
    k_json = sum(bool(r["json_valid"]) for r in d)
    tok = [r["token_usage"]["total_tokens"] for r in d if r.get("token_usage")]
    return {
        "n": n,
        "k_logic": k_logic,
        "k_llm_logic": k_llm_logic,
        "k_json": k_json,
        "ci": wilson(k_logic, n),
        "p50": float(np.percentile(lat, 50)),
        "p95": float(np.percentile(lat, 95)),
        "min": min(lat),
        "max": max(lat),
        "tok": float(np.mean(tok)) if tok else 0.0,
        "culprit": Counter(r.get("culprit_id") for r in d),
        "times": Counter(r.get("crime_time") for r in d),
        "fallback": sum(bool(r.get("used_fallback_sample")) for r in d),
        "patched": sum(1 for r in d if r.get("patch_retries", 0) > 0),
        "avg_patch": sum(r.get("patch_retries", 0) for r in d) / n if n else 0.0,
    }


def solver_stats(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = raw.get("cases", []) if isinstance(raw, dict) else raw
    n = len(cases)
    perfect = sum(1 for r in cases if r.get("culprit_identified") and r.get("score") == 100)
    culprit_ok = sum(1 for r in cases if r.get("culprit_identified"))
    return {"n": n, "perfect": perfect, "culprit_ok": culprit_ok, "ci": wilson(culprit_ok, n)}


def dist(c: Counter, n: int) -> str:
    return "; ".join(f"{k}: {v}/{n}" for k, v in sorted(c.items()))


mini = stats(BE / "benchmark_results_gpt4o_mini.json")
g4o = stats(BE / "benchmark_results_gpt4o_v2.json")
gemma_hyb = stats(BE / "benchmark_results_gemma4_local.json")
g4o_clean = stats(BE / "benchmarks" / "benchmark_gpt-4o.json")
gemma_pure = stats(BE / "benchmarks" / "benchmark_gemma4.json")
solver_old = solver_stats(BE / "solver_benchmark_results.json")
solver_new = solver_stats(BE / "benchmarks" / "solver_benchmark.json")

# Combined cloud N = mini + g4o
cloud_raw = json.loads((BE / "benchmark_results_gpt4o_mini.json").read_text(encoding="utf-8")) + json.loads(
    (BE / "benchmark_results_gpt4o_v2.json").read_text(encoding="utf-8")
)
cloud_lat = [r["latency_sec"] for r in cloud_raw]
cloud_p50 = float(np.percentile(cloud_lat, 50))
cloud_p95 = float(np.percentile(cloud_lat, 95))
cloud_ci = wilson(sum(bool(r["logic_valid"]) for r in cloud_raw), len(cloud_raw))

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.font.size = Pt(13)
for s in doc.sections:
    s.left_margin, s.right_margin = Cm(2.5), Cm(2.0)
    s.top_margin, s.bottom_margin = Cm(2.0), Cm(2.0)


def set_cell_shading(cell, fill_hex: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def para(text: str = "", bold=False, italic=False, align=None, size=None, space_before=0, space_after=4, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    if align:
        p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    return p


def rich(parts, align=None, space_before=0, space_after=4):
    """parts: list of (text, bold, italic)."""
    p = doc.add_paragraph()
    for t, b, i in parts:
        r = p.add_run(t)
        r.bold, r.italic = b, i
    if align:
        p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    return p


def bullet(text: str):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.15
    p.add_run("–\t" + text)
    return p


def make_table(rows, widths=None, header=True):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            set_cell_margins(cell, top=70, bottom=70, left=110, right=110)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(str(val))
            r.font.size = Pt(11.5)
            if header and i == 0:
                r.bold = True
                set_cell_shading(cell, "E8EEF5")
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif not header and j == 0:
                r.bold = True
                set_cell_shading(cell, "F5F7FA")
            if widths:
                cell.width = Cm(widths[j])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def item(code, title, level, opinion, done, where, files, pending=None):
    rich([(f"{code}. {title} ", True, False), (f"[{level}]", True, True)], space_before=6, space_after=3)
    rich([("Căn cứ / Ý kiến của GVHD:", False, True)], space_after=2)
    bullet(opinion)
    rich([("Nội dung đã tiếp thu và chỉnh sửa:", False, True)], space_after=2)
    for d in done:
        bullet(d)
    if pending:
        rich([("Phần tiếp tục hoàn thiện trước hạn nộp 02/12/2026:", False, True)], space_after=2)
        for pk in pending:
            bullet(pk)
    rich([("Vị trí đã sửa trong báo cáo: ", False, True), (where, False, False)], space_after=2)
    rich([("Mã nguồn / Dữ liệu đối chiếu: ", False, True), (f"{files}.", False, False)], space_after=5)


# ---------------- Header (Matching GVHD PDF layout) ----------------
para("ĐẠI HỌC PHENIKAA", size=13, space_after=1)
para("TRƯỜNG CÔNG NGHỆ THÔNG TIN", bold=True, size=13, space_after=4)
para("Hà Nội, ngày 25 tháng 11 năm 2026", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, size=12, space_after=6)
para(
    "BẢN GIẢI TRÌNH TIẾP THU Ý KIẾN GÓP Ý CỦA GIẢNG VIÊN HƯỚNG DẪN",
    bold=True,
    align=WD_ALIGN_PARAGRAPH.CENTER,
    size=14,
    space_after=2,
)
para(
    "Đối với bản sửa báo cáo và sản phẩm Đồ án tốt nghiệp",
    bold=True,
    align=WD_ALIGN_PARAGRAPH.CENTER,
    size=13,
    space_after=3,
)
rich(
    [("Kính gửi: ", False, True), ("TS. Nguyễn Văn Tánh – Giảng viên hướng dẫn", True, False)],
    align=WD_ALIGN_PARAGRAPH.CENTER,
    space_after=8,
)

# ---------------- Section I ----------------
para("I. THÔNG TIN CHUNG", bold=True, space_before=4, space_after=4)
make_table(
    [
        ["Sinh viên thực hiện", "Nguyễn Ngọc Công Anh – MSSV: 22010201 – Lớp K16-KHMT"],
        ["Ngành đào tạo", "Khoa học máy tính – Chuyên ngành Trí tuệ nhân tạo"],
        [
            "Tên đề tài (theo bìa)",
            "Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán",
        ],
        ["Giảng viên hướng dẫn", "TS. Nguyễn Văn Tánh"],
        [
            "Căn cứ góp ý",
            "Phiếu nhận xét và góp ý của Giảng viên hướng dẫn ngày 19/11/2026 (Mục I–VI)",
        ],
        [
            "Tài liệu nộp kèm",
            f"(1) Báo cáo ĐATN bản sửa (BAO_CAO_DO_AN_TOT_NGHIEP_22010201.pdf, 104 trang); (2) Slide bảo vệ (BAO_VE_DO_AN_TOT_NGHIEP.pptx); (3) Notebook đối chứng (benchmark_evaluation.ipynb); (4) Kho mã nguồn github.com/NNgocCongAnh/graduation-project, nhánh v1-clean, tham chiếu commit {COMMIT}.",
        ],
        [
            "Phương pháp kiểm chứng",
            "Toàn bộ bộ kiểm thử (89 ca pytest), script thực nghiệm (benchmark_runner.py, fault_injection_runner.py, solver_agent.py, e2e_baseline.py), script kiểm tra nhất quán (verify_results.py) và các tệp kết quả thô (*_results*.json, benchmarks/*.json) đều nằm trong kho mã nguồn để tái lập và tính lại mọi số liệu trong báo cáo.",
        ],
    ],
    widths=[4.6, 11.9],
    header=False,
)

# ---------------- Section II ----------------
para("II. BẢNG TỔNG HỢP ĐỐI CHIẾU TỪNG MỤC GÓP Ý", bold=True, space_before=4, space_after=4)
para(
    "Ghi chú về 4 điều kiện tiên quyết xem xét cho phép bảo vệ (Mục VI của Phiếu góp ý): III.A1, III.A2, III.B2 và III.C1 đã được ưu tiên xử lý triệt để ở mức mã nguồn, dữ liệu thực nghiệm và văn bản báo cáo; các lượt chạy bổ sung mở rộng trước hạn nộp chính thức ngày 02/12/2026 được ghi nhận rõ trạng thái bên dưới."
)
make_table(
    [
        ["Mục", "Nội dung góp ý", "Mức độ", "Trạng thái", "Vị trí sửa & Tệp / Commit đối chiếu"],
        [
            "A1*",
            "Đối chứng, ablation, đa dạng chủ đề, bỏ neo cứng",
            "Bắt buộc",
            "Đã hoàn thành phần lõi; còn 6 lượt gpt-4o bản hợp nhất cuối trước 02/12",
            "Mục 4.3.3, 4.4 (Bảng 4.2), 5.3; agents.py, id_shuffle.py, ablation_results.json",
        ],
        [
            "A2*",
            "Cỡ mẫu N≥30, Wilson CI, P95, token thực, cờ dự phòng",
            "Bắt buộc",
            "Đã hoàn thành (Cloud N=60; Gemma4 N=23 lai + 3 probe offline)",
            "Mục 4.2, 4.3 (Bảng 4.1), 4.5 (Bảng 4.3); benchmark_results_*.json, verify_results.py",
        ],
        [
            "A3",
            "RQ3 – tiêm lỗi có kiểm soát, bỏ ký hiệu O(1)/O(N)",
            "Bắt buộc",
            "Đã hoàn thành (80 ca tiêm lỗi; ghi nhận C1 chưa đạt)",
            "Mục 3.9, 4.4, 4.5, 4.7 (Bảng 4.5, Hình 4.4); fault_injection_runner.py",
        ],
        [
            "A4",
            "Đánh giá tính khả giải & nguồn Hình 4.3",
            "Bắt buộc",
            "Đã xử lý (Solver 19/20 cũ + 3/3 bộ mới; còn 17 ca bộ mới trước 02/12)",
            "Mục 4.8 (Bảng 4.6), Hình 4.3, Mục 5.3; solver_agent.py, benchmarks/solver_benchmark.json",
        ],
        [
            "B1",
            "Phạm vi kiểm định đồ thị hai phía & bảng Knox",
            "Bắt buộc",
            "Đã hoàn thành",
            "Mục 2.4, 2.5 (Bảng 2.1), 3.1, 3.8; validator.py, case_graph.py, test_validator.py",
        ],
        [
            "B2*",
            "Tách chân lý gốc khỏi client, chặn hồ sơ không hợp lệ",
            "Bắt buộc",
            "Đã hoàn thành (ClientCaseDossier, HTTP 422, 6 ca kiểm thử)",
            "Mục 3.4, 3.6, 3.11, 4.3.1; models.py, main.py, CaseData.cs, test_client_isolation.py",
        ],
        [
            "B3",
            "Trích dẫn Henssge, kiểm thử đối chiếu, tên/cấu hình LLM",
            "Khuyến nghị",
            "Đã hoàn thành",
            "Mục 2.3.5, 4.1, Phụ lục A.3; test_henssge.py, llm_service.py",
        ],
        [
            "C1*",
            "Thu hồi token HF, dọn lịch sử git, bỏ secret mặc định",
            "Bắt buộc – ngay",
            "Đã hoàn thành (revoke + filter-repo + bỏ mặc định backend & Unity)",
            "Mục 3.11.4, Phụ lục A.4; security.py, llm_service.py, ServerConfig.cs, SettingsModal.cs",
        ],
        [
            "C2",
            "Giới hạn HMAC, mô hình đe dọa, rate-limit, 89/89 pytest",
            "Bắt buộc",
            "Đã hoàn thành",
            "Mục 3.11 (Bảng 3.3), 4.3.1; security.py, main.py, test_*.py",
        ],
        [
            "D1",
            "Bổ sung tổng quan sinh có ràng buộc & tự sửa lỗi",
            "Khuyến nghị",
            "Đã hoàn thành",
            "Mục 2.1, Mục 2.6.1–2.6.3, Danh mục tài liệu tham khảo",
        ],
        [
            "E",
            "Chuẩn hóa tên đơn vị, thuật ngữ, dấu thập phân, UI",
            "Bắt buộc / Khuyến nghị",
            "Đã hoàn thành",
            "Bìa, Lời cảm ơn, Mục 1.6, 5.1, toàn văn LaTeX, PPTX, SettingsModal.cs",
        ],
    ],
    widths=[1.1, 4.2, 2.2, 4.5, 4.5],
)
para("(*) Bốn mục điều kiện tiên quyết xem xét cho phép bảo vệ theo Mục VI của Phiếu nhận xét.", italic=True, size=11, space_after=6)

# ---------------- Section III ----------------
para("III. GIẢI TRÌNH CHI TIẾT TỪNG MỤC GÓP Ý", bold=True, space_before=4, space_after=4)
para("A. Thiết kế và tính hợp lệ của thực nghiệm", bold=True, italic=True)

item(
    "A1",
    "Mô hình đối chứng, ablation và ràng buộc cứng trong prompt",
    "Bắt buộc",
    "Chưa có thực nghiệm đối chứng; prompt ấn định culprit_id = \"SUSP-01\" và mốc 21:40; cả 30 phiên dùng một chủ đề Biệt thự Blackwood.",
    [
        "Loại bỏ ràng buộc cứng và điểm neo ví dụ trong agents.py: bỏ culprit_id = \"SUSP-01\", bỏ toàn bộ các mốc giờ ví dụ (21:40, 21:30, 20:45, 22:30...) và bỏ dòng ghép sẵn \"SUSP-02 và SUSP-03\" trong DeductionAgent; yêu cầu LLM tự phân bổ thủ phạm trong SUSP-01..03 và tính khung thời gian từ dữ liệu vụ án.",
        "Mở rộng 3 chủ đề độc lập (10 lượt/chủ đề/mô hình đám mây): Biệt thự Cổ Blackwood, Chuyến tàu đêm Thống Nhất, Phòng thí nghiệm Công nghệ cao CyberTech; tính chỉ số phân bố giờ gây án, hung khí và độ tương đồng từ vựng Jaccard.",
        "Bổ sung nghiên cứu loại trừ 4 cấu hình (ablation_results.json): (1) Prompt nguyên khối thất bại 3/3 lượt (35–43 lỗi Pydantic/lượt); (2–4) Ba cấu hình đa tác tử đều đạt 3/3. Với N = 3/cấu hình, báo cáo nêu rõ chưa tách được đóng góp riêng giữa hậu xử lý Henssge và vá lỗi cục bộ; hiệu quả vá lỗi được đo tách biệt ở A3.",
        "Bổ sung đối chứng một lần gọi công bằng (Cấu hình 1b, e2e_baseline.py, N = 9 lượt trên 3 chủ đề) theo thiết kế E2E-plan (Huot và cộng sự, ICLR 2025): cung cấp nguyên văn chỉ dẫn 4 tác tử và đầy đủ JSON Schema trong 1 lượt gọi, không hậu xử lý và không vá lỗi. Kết quả: hợp lệ cú pháp 5/9, vượt kiểm định logic 1/9 (Wilson 95%: [2,0%; 43,5%]), chứng minh sinh một lần không giữ được nhất quán ngay cả khi có đầy đủ schema.",
        "Bổ sung lớp hoán vị song ánh tự động (id_shuffle.py + test_id_shuffle.py): hoán vị ngẫu nhiên đồng thời cả mã nghi phạm (SUSP-01..03) và mã vật chứng/hung khí (EV-01..05) ngay khi phát hành hồ sơ, giữ nguyên tuyệt đối cấu trúc suy luận và đáp án (kiểm chứng qua 3.000 lượt chạy phân bố đều ~1/3 thủ phạm và ~1/5 hung khí).",
        f"Kết quả đa dạng thực tế: trên gpt-4o-mini (N = {mini['n']}) phân bố trước hoán vị là {dist(mini['culprit'], mini['n'])}; trên gpt-4o (N = {g4o['n']}, gồm {g4o_clean['n']} lượt mới hoàn toàn sau khi bật id_shuffle ở benchmarks/benchmark_gpt-4o.json + 6 lượt CyberTech chạy cùng ngày trên prompt không neo ngay trước bước id_shuffle) phân bố thủ phạm đạt {dist(g4o['culprit'], g4o['n'])} và mốc 21:30 chỉ còn {g4o['times'].get('21:30', 0)}/{g4o['n']}.",
        "Điều chỉnh văn phong Tóm tắt, Abstract và Kết luận tương xứng số liệu thực đo, bỏ các tính từ phóng đại.",
    ],
    "Tóm tắt, Abstract, Mục 4.3.3, Mục 4.4 (Bảng 4.2), Mục 5.3",
    "detective-backend/agents.py, id_shuffle.py, e2e_baseline.py, ablation_results.json, e2e_baseline_results.json",
    pending=[
        f"Bộ benchmarks/benchmark_gpt-4o.json hiện đã chạy xong {g4o_clean['n']}/30 lượt hoàn toàn trên bản có id_shuffle + bỏ hết điểm neo (dừng ở lượt 25 do giới hạn HTTP 429; P50 = {vn(g4o_clean['p50'])} s, P95 = {vn(g4o_clean['p95'])} s, 100% logic hợp lệ). Sẽ chạy nốt 6 lượt CyberTech cuối cùng khi mở hạn mức để thay thế 6 lượt tiền-id_shuffle trong bộ N = 30 trước ngày 02/12/2026.",
    ],
)

item(
    "A2",
    "Cỡ mẫu, phương pháp tính thống kê và đo các tiêu chí Bảng 3.2",
    "Bắt buộc",
    "Cỡ mẫu 10 lượt/mô hình quá nhỏ; chưa có khoảng tin cậy Wilson; cột P95 thực chất là giá trị lớn nhất; tiêu chí A3, C1, C2 chưa đo; token mới ước lượng; thiếu cờ phân biệt hồ sơ dự phòng.",
    [
        f"Tăng cỡ mẫu đám mây lên N = 30 lượt/mô hình (Tổng đám mây N = 60, Wilson 95%: [{vn(cloud_ci[0], 1)}%; {vn(cloud_ci[1], 1)}%], P50 = {vn(cloud_p50)} s, P95 = {vn(cloud_p95)} s). Cụ thể: gh/gpt-4o-mini đạt {mini['k_logic']}/{mini['n']} (Wilson [{vn(mini['ci'][0], 1)}%; {vn(mini['ci'][1], 1)}%], P50 = {vn(mini['p50'])} s, P95 = {vn(mini['p95'])} s, TB {vn(mini['tok'], 0)} token/lượt); gh/gpt-4o đạt {g4o['k_logic']}/{g4o['n']} (Wilson [{vn(g4o['ci'][0], 1)}%; {vn(g4o['ci'][1], 1)}%], P50 = {vn(g4o['p50'])} s, P95 = {vn(g4o['p95'])} s, Patch TB = {vn(g4o['avg_patch'])}).",
        "Tính P50 và P95 đúng chuẩn bằng nội suy tuyến tính (numpy.percentile), tách riêng với min/max.",
        "Đo thực tế token qua trường usage của API cho cả 4 tác tử và vòng vá (token_usage trong JSON) cùng thời gian kiểm định ký hiệu c2_latency_ms (< 1 ms).",
        "Báo cáo đầy đủ kết quả từng tiêu chí Bảng 3.2 tại Bảng 4.3: A1, A2, A3, C2 ĐẠT; L1 (P50 <= 20 s) và C1 (<= 500 token/lượt vá) ghi nhận CHƯA ĐẠT kèm phân tích nguyên nhân.",
        "Ghi nhận cờ used_fallback_sample, fallback_triggered và agent_models theo từng lượt; cả 60 lượt đám mây có used_fallback_sample = False và đúng mô hình chính 100%.",
        f"Đối với khảo sát cục bộ gemma4:e4b-it-qat (RTX 3050 4 GB VRAM): báo cáo giữ nguyên {gemma_hyb['n']} lượt thực nghiệm xuyên đêm và ghi chú minh bạch ở chú thích Bảng 4.1 rằng CharacterAgent và ClueAgent đã tự động chuyển mạch dự phòng sang mô hình đám mây (tức hệ lai cục bộ–đám mây). Ngoài ra, đã bổ sung cờ --no-fallback trong benchmark_runner.py và chạy thăm dò {gemma_pure['n']} lượt thuần ngoại tuyến (benchmarks/benchmark_gemma4.json): kết quả {gemma_pure['k_llm_logic']}/{gemma_pure['n']} lượt LLM tự sinh vượt kiểm định (cả {gemma_pure['fallback']}/{gemma_pure['n']} lượt phải trả về hồ sơ dự phòng do CharacterAgent gặp lỗi cú pháp JSON ở mức lượng tử hóa Q4_0 trên VRAM 4 GB, P50 = {vn(gemma_pure['p50'])} s).",
        "Đồng bộ benchmark_evaluation.ipynb và verify_results.py để toàn bộ bảng biểu kiểm chứng lại trực tiếp từ các tệp JSON thô.",
    ],
    "Mục 4.2, Mục 4.3 (Bảng 4.1), Mục 4.5 (Bảng 4.3), Phụ lục A",
    "detective-backend/benchmark_runner.py, verify_results.py, benchmark_results_gpt4o_mini.json, benchmark_results_gpt4o_v2.json, benchmark_results_gemma4_local.json, benchmarks/benchmark_gemma4.json",
    pending=[
        "Thử nghiệm mở rộng mẫu chạy thuần ngoại tuyến cho gemma4 (tối ưu grammar/timeout trên bộ nhớ 24 GB RAM) nếu cần thêm dữ liệu đối sánh thuần local trước 02/12/2026.",
    ],
)

item(
    "A3",
    "Câu hỏi nghiên cứu RQ3 về hiệu quả sửa lỗi cục bộ",
    "Bắt buộc",
    "Trong bộ cũ chỉ có 1 lượt vá và thất bại; khẳng định độ phức tạp ngữ cảnh O(1) chưa chính xác.",
    [
        "Thiết kế thực nghiệm tiêm lỗi có kiểm soát (fault_injection_runner.py): 4 nhóm lỗi x 20 ca = 80 ca trên gh/gpt-4o-mini.",
        f"Kết quả (fault_injection_results.json): tỷ lệ vá thành công chung đạt 63,8% (51/80, Wilson 95%: [52,8%; 73,4%]); phân theo nhóm: sai cửa sổ TOD 50,0%, trùng mã/đa thủ phạm 100,0%, thiếu vật chứng then chốt 45,0%, lỗi tham chiếu 60,0%.",
        f"Đo token và độ trễ thực tế: trung bình 4.227,6 token/lượt vá, P50 = 7,21 s; so với sinh lại toàn bộ trên gpt-4o-mini ({vn(mini['tok'], 0)} token, P50 = {vn(mini['p50'])} s) giảm {vn(100 * (1 - 4227.6 / mini['tok']), 1)}% lượng token và {vn(100 * (1 - 7.21 / mini['p50']), 1)}% độ trễ. Ngoài ra, trên bộ gpt-4o N=30 hiện tại đã ghi nhận {g4o['patched']} lượt tự nhiên phát sinh lỗi ở bản thảo đầu và đều được vá thành công.",
        "Loại bỏ hoàn toàn ký hiệu O(1)/O(N) ở Chương 3 và Chương 4; diễn giải chính xác là hàm vá nhận toàn bộ danh sách nghi phạm, vật chứng và chân lý gốc nên ngữ cảnh tăng theo quy mô hồ sơ, lợi thế nằm ở việc chỉ sửa 1 tác tử thay vì chạy lại toàn chuỗi 4 tác tử.",
        "Ghi nhận trung thực tiêu chí C1 (<= 500 token/lượt vá) là CHƯA ĐẠT trong Bảng 4.3.",
    ],
    "Mục 3.9, Mục 4.4, Mục 4.5, Mục 4.7 (Bảng 4.5, Hình 4.4), Mục 5.3",
    "detective-backend/fault_injection_runner.py, fault_injection_results.json",
    pending=[
        "Kiểm tra bổ sung nhánh suy luận (ReasoningAgent) trong fault_injection_runner.py nếu phát sinh thời gian chạy sau khi hoàn tất 2 hạng mục benchmark chính.",
    ],
)

item(
    "A4",
    "Đánh giá chất lượng và tính khả giải của hồ sơ từ phía người chơi",
    "Bắt buộc",
    "Thiếu thử nghiệm người chơi hoặc tác tử giải độc lập; Hình 4.3 minh họa lỗi không rõ nguồn dữ liệu.",
    [
        f"Áp dụng phương án (ii): xây dựng tác tử phá án độc lập (solver_agent.py) chỉ nhận ClientCaseDossier (không có ground_truth, không có cờ đáp án) và tự suy luận tìm thủ phạm + vật chứng then chốt.",
        f"Trên bộ {solver_old['n']} ca tiêu chuẩn (solver_benchmark_results.json, gpt-4o-mini, T = 0,2): giải đúng thủ phạm {solver_old['culprit_ok']}/{solver_old['n']} (95,0%, Wilson 95%: [{vn(solver_old['ci'][0], 1)}%; {vn(solver_old['ci'][1], 1)}%]), tìm đúng vật chứng then chốt 100%, tỷ lệ mắc bẫy nghi binh 0%. Ca thất bại duy nhất (CASE-41A3E7) giúp phát hiện lỗi nghi binh gắn cho thủ phạm và đã được khắc phục ở cả prompt lẫn validator.py.",
        f"Thử nghiệm trên bộ hồ sơ sinh mới sau khi bỏ điểm neo và bật id_shuffle bằng mô hình đối sánh mạnh (gemini/gemini-3-flash-preview, lưu tại benchmarks/solver_benchmark.json): hiện đã chạy xong {solver_new['n']} ca đầu tiên với kết quả {solver_new['perfect']}/{solver_new['n']} ca đạt 100/100 điểm, 0% mắc bẫy nghi binh (tạm dừng ở ca thứ 4 do vượt hạn mức 20 RPD Free Tier của Gemini API).",
        "Làm rõ trong Mục 5.3 và Phụ lục A.5 rằng bảng deduction_logs chỉ ghi nhận phiên thử nghiệm và Solver Agent; chưa thực hiện khảo sát trên nhóm người chơi thực có quy trình.",
        "Sửa chú thích Hình 4.3 nêu rõ nguồn dữ liệu là 121 lỗi Pydantic trích xuất từ 3 lượt cấu hình prompt nguyên khối trong ablation_results.json.",
    ],
    "Mục 4.8 (Bảng 4.6), Hình 4.3, Mục 5.3, Phụ lục A.5",
    "detective-backend/solver_agent.py, solver_benchmark_results.json, benchmarks/solver_benchmark.json, ablation_results.json",
    pending=[
        "Chạy tiếp 17 ca còn lại trên benchmarks/solver_benchmark.json (nhờ cơ chế lưu checkpoint tự động từng ca mới bổ sung trong solver_agent.py) để hoàn tất đủ 20/20 ca mới trước hạn nộp 02/12/2026.",
    ],
)

para("B. Mức độ khẳng định so với nội dung mã nguồn kiểm tra", bold=True, italic=True)

item(
    "B1",
    "Phạm vi thực tế của kiểm định đồ thị hai phía và bảng ánh xạ 10 điều Knox",
    "Bắt buộc",
    "validate_case_diagnostics không gọi case_graph.py; kiểm định thực chất là kiểm tra cờ cấu trúc; Điều 2 và nhiều điều Knox ánh xạ chưa tương ứng.",
    [
        "Kết nối trực tiếp build_bipartite_case_graph vào validate_case_diagnostics trong validator.py để kiểm tra tính tồn tại cạnh bác bỏ ngoại phạm của thủ phạm.",
        "Điều chỉnh toàn bộ diễn đạt ở Mục 2.4 và Mục 3.8: phân biệt rạch ròi ràng buộc được kiểm tra tất định bằng mã (đơn thủ phạm, cửa sổ TOD Henssge, toàn vẹn tham chiếu ID, độ dài chuỗi suy luận, tồn tại cạnh then chốt, không gắn nghi binh cho thủ phạm) với ràng buộc ngữ nghĩa do prompt định hướng.",
        "Cập nhật Bảng 2.1 phân loại rõ từng điều trong 10 điều Knox: điều nào có mã kiểm định, điều nào bảo đảm theo thiết kế prompt; bỏ ánh xạ sai Điều 2 sang Henssge.",
        "Bổ sung luật test_red_herring_cannot_link_to_culprit vào validator.py và test_validator.py.",
        "Bổ sung phần hình thức hóa hệ ràng buộc không-thời gian theo hướng CSP/SMT tại Mục 2.4.4 và đưa vào hướng phát triển Mục 5.4.4.",
    ],
    "Mục 2.4, Mục 2.5 (Bảng 2.1), Mục 3.1, Mục 3.8, Mục 5.3, Mục 5.4",
    "detective-backend/validator.py, case_graph.py, test_validator.py",
)

item(
    "B2",
    "Tách biệt chân lý gốc khỏi dữ liệu người chơi và chặn hồ sơ không hợp lệ",
    "Bắt buộc",
    "API trả toàn bộ ground_truth và cờ đáp án về client Unity/WebGL; generate_case vẫn trả hồ sơ lỗi và lưu is_valid = True.",
    [
        "Tạo schema ClientCaseDossier và ClientSuspect/ClientEvidence trong models.py loại bỏ toàn bộ ground_truth, reasoning_chain, is_culprit, secret_innocent_fact, is_crucial, is_red_herring, is_weapon và linked_suspect_id.",
        "Các endpoint công khai (/api/case/sample, /api/case/{id}, /api/case/generate) chỉ trả ClientCaseDossier; kết án của người chơi được chấm phía máy chủ qua POST /api/case/verify. Client Unity (CaseData.cs, AccusationModal.cs) được cập nhật tương ứng.",
        "Endpoint nội bộ (/api/case/{id}/internal, /api/case/{id}/graph) khóa bằng header X-Internal-Token (biến môi trường INTERNAL_API_TOKEN), vô hiệu hóa hoàn toàn khi không cấu hình; chữ ký HMAC của client không mở được các route này.",
        "Hồ sơ không vượt qua tái kiểm định được lưu với is_valid = False trong SQLite và trả HTTP 422, tuyệt đối không phát hành tới client.",
        "Bổ sung test_client_isolation.py (6 ca kiểm thử độc lập xác nhận không rò rỉ đáp án, không rò rỉ is_weapon và chặn hồ sơ lỗi).",
    ],
    "Mục 3.4, Mục 3.6, Mục 3.11, Mục 4.3.1, Phụ lục A.4",
    "detective-backend/models.py, main.py, database.py, test_client_isolation.py, Unity CaseData.cs, AccusationModal.cs",
)

item(
    "B3",
    "Tham số pháp y Henssge và cấu hình mô hình sử dụng",
    "Khuyến nghị",
    "Dung sai ±1,5 giờ chưa có trích dẫn; kiểm thử Henssge kiểm tra vòng tròn; mô hình ollama/gemma4:31b-cloud không phải chạy cục bộ.",
    [
        "Bổ sung trích dẫn Henssge (1988, 2000); giải thích rõ khoảng tin cậy pháp y 95% của phương pháp nhiệt độ trực tràng là >= ±2,8 giờ và dung sai ±1,5 giờ trong trò chơi là tham số thiết kế thu hẹp nằm gọn trong giới hạn tin cậy pháp y.",
        "Mở rộng test_henssge.py thêm ca đối chiếu trực tiếp với bảng giá trị tham chiếu công bố của nomogram Henssge (kiểm thử không vòng tròn).",
        "Ghi rõ nhà cung cấp, phiên bản, nhiệt độ lấy mẫu (T = 0,7 cho sinh; T = 0,2 cho vá/giải), top_p = 0,9 và thời điểm đo 11/2026; loại bỏ hoàn toàn gemma4:31b-cloud khỏi báo cáo và notebook.",
    ],
    "Mục 2.3.5, Mục 4.1, Phụ lục A.3",
    "detective-backend/test_henssge.py, llm_service.py, benchmark_evaluation.ipynb",
)

para("C. An toàn thông tin", bold=True, italic=True)

item(
    "C1",
    "Lộ bí mật trong kho mã nguồn công khai",
    "Bắt buộc – xử lý ngay",
    "Lịch sử git chứa token Hugging Face (hf_...) trong flux_test_archive.ipynb; security.py có DEFAULT_SECRET và llm_service.py có sk-9router-local.",
    [
        "Đã thu hồi (revoke) ngay token Hugging Face bị lộ trên tài khoản Hugging Face.",
        "Đã xóa vĩnh viễn tệp flux_test_archive.ipynb khỏi toàn bộ lịch sử git bằng git filter-repo và cập nhật lại toàn bộ các thẻ v1.0.0–v1.2.0; xác nhận không còn chuỗi hf_ trong git log --all.",
        "Xóa bỏ khóa HMAC mặc định khỏi security.py (máy chủ từ chối khởi động nếu thiếu GAME_CLIENT_SECRET).",
        "Xóa bỏ chuỗi \"sk-9router-local\" khỏi toàn bộ mã nguồn backend (llm_service.py, agents.py, solver_agent.py, fault_injection_runner.py) và mã nguồn client Unity (ServerConfig.cs, SettingsModal.cs).",
    ],
    "Mục 3.11.4, Phụ lục A.4",
    "detective-backend/security.py, llm_service.py, Unity ServerConfig.cs, SettingsModal.cs",
)

item(
    "C2",
    "Giới hạn cơ chế HMAC, mô hình đe dọa và trạng thái bộ kiểm thử",
    "Bắt buộc",
    "HMAC với bí mật nhúng ở WebGL không phải xác thực người dùng; CORS mở [*]; WebSocket thiếu xác thực; một số ca pytest lỗi.",
    [
        "Trình bày trung thực trong Mục 3.11 rằng HMAC phía client chỉ ngăn gọi API tự do và sửa gói tin đường truyền, không chống được người dùng trích xuất khóa từ bản build trình duyệt – do đó phải kết hợp kiến trúc tách đáp án B2.",
        "Bổ sung Bảng 3.3 Mô hình đe dọa và đối sách (đọc trộm đáp án, spam tiêu hao token LLM, phát lại request, nghe lén WebSocket LAN).",
        "Cài đặt giới hạn tần suất 5 yêu cầu/phút/IP (HTTP 429) cho /api/case/generate, cấu hình CORS theo danh sách biến CORS_ORIGINS, bộ nhớ đệm nonce + cửa sổ 60 s; ghi nhận rõ giới hạn WebSocket phòng chơi dùng trong mạng LAN tin cậy.",
        "Cập nhật các tệp kiểm thử tích hợp để chạy kèm chữ ký chuẩn trong cấu hình mặc định: toàn bộ 89/89 ca pytest đều đạt.",
    ],
    "Mục 3.11 (Bảng 3.3), Mục 4.3.1",
    "detective-backend/security.py, main.py, test_security.py, test_rooms.py, test_api_database_integration.py, test_assets_integration.py",
)

para("D. Tổng quan tài liệu và nội dung học thuật", bold=True, italic=True)

item(
    "D1",
    "Bổ sung tổng quan nghiên cứu liên quan và rút gọn lý thuyết thừa",
    "Khuyến nghị",
    "Danh mục 21 tài liệu còn mỏng, lẫn 3 trang tài liệu phần mềm; thiếu khảo sát sinh truyện có ràng buộc và cơ chế tự sửa lỗi; Mục 2.1 trình bày attention không dùng đến.",
    [
        "Bổ sung Mục 2.6.1–2.6.3 khảo sát các công trình về sinh truyện có ràng buộc (Plan-and-Write, FUDGE, Dramatron), sinh nội dung trò chơi bằng LLM (PCGML) và cơ chế tự sửa lỗi lặp (Self-Refine – Madaan và cộng sự, NeurIPS 2023; Reflexion), làm rõ đóng góp của đồ án là phản hồi từ bộ kiểm định tất định bên ngoài.",
        "Rút gọn Mục 2.1, loại bỏ phần công thức cơ chế attention không sử dụng ở các chương sau.",
        "Rà soát toàn bộ tài liệu tham khảo (loại 3 trang tài liệu phần mềm, sửa lỗi khớp trích dẫn giữa nội văn và danh mục tài liệu).",
    ],
    "Mục 2.1, Mục 2.6, Tài liệu tham khảo",
    "thesis_latex/chapters/02_theoretical_background.tex, references.bib",
)

para("E. Hình thức trình bày", bold=True, italic=True)

item(
    "E",
    "Thống nhất đơn vị, thuật ngữ, dấu thập phân và hình thức báo cáo/sản phẩm",
    "Bắt buộc / Khuyến nghị",
    "Sai tên đơn vị/chức danh trên bìa; không thống nhất luận văn/khóa luận/đồ án; sai tên đề tài ở Mục 5.1; chỉ số trên từ viết tắt; Unity 2.5D; dấu chấm thập phân.",
    [
        "Sửa bìa và Lời cảm ơn thành \"Trường Công nghệ thông tin, Đại học Phenikaa\" và \"Giảng viên hướng dẫn\".",
        "Thống nhất toàn bộ là \"Đồ án tốt nghiệp\" trong báo cáo PDF, tệp slide (.pptx), mã nguồn giao diện Unity (SettingsModal.cs: bỏ chữ \"Luận văn\" và xóa toàn bộ emoji trên các nút bấm chọn cấu hình) và tên tệp.",
        "Đồng bộ tên đề tài tại Mục 5.1 và slide khớp hoàn toàn với bìa báo cáo.",
        "Bỏ chỉ số trên ngay sau từ viết tắt; sửa \"Unity 2.5D\" thành \"Unity 2D\"; rà soát thay thế các từ ngữ quảng bá (như \"hoàn hảo\" ở Mục 4.8) bằng văn phong khoa học chuẩn mực.",
        "Thống nhất dấu phẩy thập phân kiểu Việt Nam và bổ sung đơn vị đo, cỡ mẫu, chú thích ở tất cả bảng/biểu đồ.",
    ],
    "Trang bìa, Lời cảm ơn, Mục 1.6, Mục 4.8, Mục 5.1, toàn văn các chương",
    "thesis_latex/chapters/*.tex, BAO_VE_DO_AN_TOT_NGHIEP.pptx, Unity SettingsModal.cs",
)

# ---------------- Section IV (Matched to GVHD Mục IV) ----------------
para("IV. ĐỐI CHIẾU CÁC NỘI DUNG CẦN BỔ SUNG (MỤC IV CỦA PHIẾU GÓP Ý)", bold=True, space_before=4, space_after=4)
for item_iv in [
    "Thực nghiệm đối chứng & loại bỏ thành phần: đã bổ sung prompt nguyên khối (0/3), đối chứng E2E-plan công bằng (1/9), đa tác tử không hậu xử lý / không vá / đầy đủ, trên 3 chủ đề độc lập kèm phân bố giờ gây án, hung khí, Jaccard (Bảng 4.2).",
    "Thực nghiệm tiêm lỗi cho vá lỗi cục bộ: đã bổ sung 80 ca trên 4 nhóm lỗi, tỷ lệ vá 63,8%, chi phí đo thực tế 4.227,6 token và P50 7,21 s (Bảng 4.5, Hình 4.4).",
    "Kết quả đo đầy đủ A1, A2, A3, L1, C1, C2 kèm Wilson 95% CI: đã tổng hợp trong Bảng 4.1 và Bảng 4.3.",
    "Đánh giá khả năng giải được: đã thực hiện bằng Solver Agent độc lập (19/20 ca bộ chuẩn; 3/3 ca đầu trên bộ mới không neo, tiếp tục chạy nốt 17 ca trước 02/12).",
    "Mô hình đe dọa & thu hồi token: đã bổ sung Bảng 3.3, tách dữ liệu client, xóa lịch sử git chứa token HF và xác nhận thu hồi.",
    "Phụ lục tái lập: đã bổ sung Phụ lục A nêu lệnh chạy, tệp thô, cấu hình mô hình và verify_results.py.",
    "Cập nhật Mục Hạn chế (Mục 5.3): nêu rõ phạm vi kiểm định cấu trúc/cờ, giới hạn WebSocket LAN, thiên lệch phân bố LLM thô trước id_shuffle, và việc chưa thử nghiệm người chơi.",
]:
    bullet(item_iv)

# ---------------- Section V (Matched to GVHD Mục V) ----------------
para("V. TRẢ LỜI CÁC CÂU HỎI PHẢN BIỆN (MỤC V CỦA PHIẾU GÓP Ý)", bold=True, space_before=4, space_after=4)

rich([("Câu hỏi 1 (Tính hợp lệ của thực nghiệm).", True, False)], space_after=2)
for t in [
    "Trong bản thảo trước ngày 19/11, tỷ lệ 90%–100% phản ánh chủ yếu các ràng buộc cứng (ấn định SUSP-01, mã nguồn tự ghi đè alibi thủ phạm) và 30/30 lượt ra giờ 21:40 do LLM sao chép trực tiếp giá trị ví dụ trong prompt.",
    "Trong bản sửa: đã bỏ hẳn ràng buộc SUSP-01 và toàn bộ giờ ví dụ; kiểm chứng đối chứng công bằng E2E-plan (cùng chỉ dẫn 4 tác tử, đầy đủ schema trong một lần gọi) chỉ đạt 1/9 vượt kiểm định (so với 60/60 của pipeline đám mây), chứng tỏ việc phân rã chuỗi tác tử kết hợp hậu xử lý Henssge và sửa lỗi cục bộ quyết định hiệu quả logic. Với N = 3/cấu hình ở ablation, đóng góp riêng của hậu xử lý và vá lỗi chưa tách được bằng ablation và được tách đo bằng thực nghiệm tiêm lỗi 80 ca (63,8% vá thành công).",
    "Về phân bố: sau khi bỏ neo và thêm hoán vị song ánh id_shuffle.py cho cả nghi phạm lẫn vật chứng khi phát hành, xác suất mỗi mã thủ phạm đến tay người chơi hội tụ về 1/3 (~33,3%) và mốc giờ không còn bị khóa cứng vào một giá trị duy nhất.",
]:
    bullet(t)

rich([("Câu hỏi 2 (Hình thức hóa tính giải được).", True, False)], space_before=4, space_after=2)
for t in [
    "Ví dụ phản chứng vượt qua bộ kiểm định cờ nhưng không giải được duy nhất: một hồ sơ có EV-04 đặt is_crucial = True, linked_suspect_id trỏ tới thủ phạm, core_contradiction dài >= 10 ký tự, nhưng mô tả EV-04 chỉ nói \"một tách trà nguội trên bàn\" không hề mâu thuẫn với ngoại phạm \"ở thư viện 20:00–22:00\". Ngoài ra ca thực tế CASE-41A3E7 từng cho thấy vật chứng nghi binh có thể vô tình minh oan cho chính thủ phạm nếu không kiểm tra ràng buộc tách biệt — lỗi này đã được bổ sung luật chặn trong validator.py.",
    "Hình thức hóa bài toán kiểm định tính duy nhất (CSP/SMT): mô hình hóa mỗi nghi phạm s bởi hàm vị trí L(s, t); ngoại phạm trong khung [a, b] là khẳng định L(s, t) = loc_khai; vật chứng mâu thuẫn tại thời điểm t0 là phủ định L(s, t0) != loc_khai. Thủ phạm s* phải thỏa có mặt tại hiện trường trong cửa sổ TOD Henssge. Bài toán giải được duy nhất khi hệ ràng buộc chỉ có đúng một nghiệm s* (kiểm tra bằng SMT Z3 bằng cách thêm khẳng định s != s* và chứng minh UNSAT).",
    "Độ phức tạp ngữ cảnh: vì repair_clues nhận toàn bộ danh sách nghi phạm, vật chứng và chân lý gốc nên kích thước ngữ cảnh tăng tuyến tính theo quy mô hồ sơ; ký hiệu O(1) đã được gỡ bỏ khỏi toàn bộ báo cáo. Lợi ích thực đo được là giảm hằng số token tiêu thụ từ 18.396 token xuống còn 4.227,6 token/lượt vá (giảm 77,0%).",
]:
    bullet(t)

rich([("Câu hỏi 3 (An toàn thông tin của hệ thống).", True, False)], space_before=4, space_after=2)
for t in [
    "Ba kịch bản tấn công trên bản thảo cũ: (1) Người chơi mở DevTools trình duyệt khi chạy WebGL đọc thẳng ground_truth từ JSON trả về; (2) Người dùng trích xuất khóa HMAC từ bản build client, tự ký yêu cầu gửi hàng loạt tới POST /api/case/generate gây tiêu hao hạn mức API LLM; (3) Bot quét lịch sử git thu thập token Hugging Face hf_... để khai thác tài nguyên.",
    "Vì sao HMAC không phải cơ chế xác thực người dùng: HMAC sử dụng khóa đối xứng bí mật dùng chung. Khi khóa nằm trong ứng dụng client phân phối công khai (đặc biệt WebGL), mọi người dùng đều có quyền truy cập vào chính khóa đó nên chỉ ngăn được việc chỉnh sửa gói tin từ bên thứ ba hoặc gọi API thiếu chữ ký đơn giản, hoàn toàn không xác định được danh tính người gửi.",
    "Kiến trúc khắc phục: toàn bộ đáp án giữ tại backend và chấm qua POST /api/case/verify; client chỉ nhận ClientCaseDossier; route nội bộ bảo vệ bằng INTERNAL_API_TOKEN riêng phía server; áp dụng rate-limit 5 req/min/IP, CORS danh sách, nonce 60 s; xóa toàn bộ secret mặc định và lịch sử token Hugging Face.",
]:
    bullet(t)

# ---------------- Section VI ----------------
para("VI. KẾ HOẠCH HOÀN THIỆN BỔ SUNG TRƯỚC NGÀY 02/12/2026 VÀ CAM KẾT", bold=True, space_before=4, space_after=4)
for plan_line in [
    f"Chạy bổ sung 6 lượt CyberTech cuối cùng cho gh/gpt-4o trên đúng phiên bản mã nguồn hợp nhất (có id_shuffle và prompt không neo) để thay thế 6 lượt CyberTech tiền-id_shuffle trong bộ N = 30.",
    f"Chạy tiếp 17 ca còn lại trong benchmarks/solver_benchmark.json (hiện đã hoàn thành {solver_new['n']}/20 ca, đạt 100/100 điểm) ngay khi hạn mức API được cấp lại để đạt đủ N = 20 ca đối chiếu cho bộ đề không neo mới.",
    "Kiểm tra bổ sung dữ liệu tiêm lỗi cho nhánh sửa lỗi ReasoningAgent nếu cần mở rộng phân tích ở Phụ lục.",
]:
    bullet(plan_line)

para(
    f"Sinh viên cam kết toàn bộ số liệu trong báo cáo bản sửa (104 trang), tệp thuyết trình và bản giải trình này đều được tính toán tái lập trực tiếp từ các tệp dữ liệu thô trong kho mã nguồn (kiểm chứng tự động bởi verify_results.py đạt 100% OK và 89/89 ca pytest đạt) tại tham chiếu {COMMIT}. Những nội dung còn hạn chế hoặc đang chạy mở rộng trước ngày 02/12/2026 đều được ghi nhận trung thực.",
    space_before=4,
    space_after=8,
)

para("SINH VIÊN THỰC HIỆN", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=1)
para("(Ký và ghi rõ họ tên)", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=24)
para("Nguyễn Ngọc Công Anh", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

doc.save(OUT)
print("Saved:", OUT)
print("Commit ref:", COMMIT)
print("mini:", mini["k_logic"], "/", mini["n"], "P50:", round(mini["p50"], 2), "P95:", round(mini["p95"], 2))
print("gpt4o_v2:", g4o["k_logic"], "/", g4o["n"], "P50:", round(g4o["p50"], 2), "P95:", round(g4o["p95"], 2), "patched:", g4o["patched"])
print("gpt4o_clean:", g4o_clean["k_logic"], "/", g4o_clean["n"], "P50:", round(g4o_clean["p50"], 2), "P95:", round(g4o_clean["p95"], 2))
print("gemma_hyb:", gemma_hyb["k_logic"], "/", gemma_hyb["n"], "P50:", round(gemma_hyb["p50"], 2))
print("gemma_pure_llm:", gemma_pure["k_llm_logic"], "/", gemma_pure["n"], "P50:", round(gemma_pure["p50"], 2))
print("solver_old:", solver_old["culprit_ok"], "/", solver_old["n"], "| solver_new:", solver_new["perfect"], "/", solver_new["n"])
