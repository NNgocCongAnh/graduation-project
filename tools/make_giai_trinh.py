"""Generate the response-to-advisor document (.docx) from raw result files."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(sys.argv[1])
COMMIT = sys.argv[2] if len(sys.argv) > 2 else "(chưa commit)"
OUT = ROOT / "GIAI_TRINH_GOP_Y_GVHD_22010201.docx"
BE = ROOT / "detective-backend"


def wilson(k: int, n: int, z: float = 1.96):
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
    k_json = sum(bool(r["json_valid"]) for r in d)
    tok = [r["token_usage"]["total_tokens"] for r in d if r.get("token_usage")]
    return {
        "n": n, "k_logic": k_logic, "k_json": k_json,
        "ci": wilson(k_logic, n),
        "p50": float(np.percentile(lat, 50)), "p95": float(np.percentile(lat, 95)),
        "min": min(lat), "max": max(lat),
        "tok": float(np.mean(tok)) if tok else 0.0,
        "culprit": Counter(r["culprit_id"] for r in d),
        "times": Counter(r["crime_time"] for r in d),
        "fallback": sum(bool(r.get("used_fallback_sample")) for r in d),
        "patched": sum(1 for r in d if r.get("patch_retries", 0) > 0),
    }


mini = stats(BE / "benchmark_results_gpt4o_mini.json")
g4o = stats(BE / "benchmark_results_gpt4o.json")


def dist(c: Counter, n: int) -> str:
    return "; ".join(f"{k}: {v}/{n}" for k, v in sorted(c.items()))


doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.font.size = Pt(13)
for s in doc.sections:
    s.left_margin, s.right_margin = Cm(3), Cm(2)
    s.top_margin, s.bottom_margin = Cm(2), Cm(2)


def para(text: str = "", bold=False, italic=False, align=None, size=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(4)
    return p


def rich(parts):
    """parts: list of (text, bold, italic)."""
    p = doc.add_paragraph()
    for t, b, i in parts:
        r = p.add_run(t)
        r.bold, r.italic = b, i
    p.paragraph_format.space_after = Pt(4)
    return p


def bullet(text: str):
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(text)
    p.paragraph_format.space_after = Pt(2)


def table(rows, widths=None, header=True):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            r = cell.paragraphs[0].add_run(str(val))
            r.font.size = Pt(11)
            r.bold = header and i == 0
            if widths:
                cell.width = Cm(widths[j])
    doc.add_paragraph()
    return t


def item(code, title, level, opinion, done, where, files):
    rich([(f"{code}. {title} ", True, False), (f"[{level}]", True, True)])
    rich([("Ý kiến của GVHD: ", False, True), (opinion, False, False)])
    rich([("Nội dung đã tiếp thu và chỉnh sửa:", False, True)])
    for d in done:
        bullet(d)
    rich([("Vị trí trong báo cáo: ", False, True), (where, False, False)])
    rich([("Mã nguồn / dữ liệu: ", False, True), (f"{files} — commit {COMMIT}.", False, False)])


# ---------------- Header ----------------
para("ĐẠI HỌC PHENIKAA", size=13)
para("TRƯỜNG CÔNG NGHỆ THÔNG TIN", bold=True)
para("Hà Nội, ngày 25 tháng 11 năm 2026", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT)
para("BẢNG GIẢI TRÌNH TIẾP THU Ý KIẾN GÓP Ý CỦA GIẢNG VIÊN HƯỚNG DẪN", bold=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, size=14)
para("Đối với bản sửa báo cáo và sản phẩm Đồ án tốt nghiệp", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
rich([("Kính gửi: ", False, True), ("TS. Nguyễn Văn Tánh – Giảng viên hướng dẫn", True, False)]).alignment = WD_ALIGN_PARAGRAPH.CENTER

para("I. THÔNG TIN CHUNG", bold=True)
table([
    ["Sinh viên thực hiện", "Nguyễn Ngọc Công Anh – MSSV: 22010201 – Lớp K16-KHMT"],
    ["Tên đề tài", "Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán"],
    ["Căn cứ", "Phiếu nhận xét và góp ý của GVHD ngày 19/11/2026"],
    ["Tài liệu nộp kèm", "(1) BAO_CAO_DO_AN_TOT_NGHIEP_22010201.pdf (bản sửa); (2) BAO_VE_DO_AN_TOT_NGHIEP.pptx; (3) Kho mã nguồn github.com/NNgocCongAnh/graduation-project, nhánh main, commit " + COMMIT],
    ["Cách kiểm chứng", "Toàn bộ kiểm thử (test_*.py), script thực nghiệm (benchmark_runner.py, fault_injection_runner.py, solver_agent.py) và tệp kết quả thô (*_results*.json) nay đã được đưa vào kho mã nguồn. Mọi số liệu trong báo cáo bản sửa được tính trực tiếp từ các tệp này."],
], widths=[4.5, 11.5], header=False)

# ---------------- Summary ----------------
para("II. TỔNG HỢP TÌNH TRẠNG XỬ LÝ", bold=True)
table([
    ["Mục", "Nội dung góp ý", "Mức độ", "Tình trạng"],
    ["A1", "Đối chứng, ablation, đa dạng chủ đề", "Bắt buộc", "Đã bổ sung; kết quả ablation báo cáo trung thực (cỡ mẫu nhỏ, chưa tách được đóng góp từng thành phần)"],
    ["A2", "Cỡ mẫu, Wilson CI, P95, token thực đo, cờ dự phòng", "Bắt buộc", "Đã xử lý"],
    ["A3", "RQ3 – tiêm lỗi, bỏ O(1)", "Bắt buộc", "Đã xử lý; tiêu chí C1 ghi nhận CHƯA ĐẠT"],
    ["A4", "Đánh giá tính khả giải", "Bắt buộc", "Đã xử lý bằng tác tử giải độc lập; chưa có thử nghiệm người chơi"],
    ["B1", "Phạm vi kiểm định thực tế", "Bắt buộc", "Đã xử lý"],
    ["B2", "Tách chân lý gốc, chặn hồ sơ lỗi", "Bắt buộc", "Đã xử lý"],
    ["B3", "Tham số pháp y, cấu hình mô hình", "Khuyến nghị", "Đã xử lý"],
    ["C1", "Lộ bí mật trong kho mã nguồn", "Bắt buộc – ngay", "Đã xử lý"],
    ["C2", "Giới hạn HMAC, mô hình đe dọa, kiểm thử", "Bắt buộc", "Đã xử lý"],
    ["D1", "Tổng quan tài liệu", "Khuyến nghị", "Đã xử lý"],
    ["E", "Hình thức trình bày", "Bắt buộc / Khuyến nghị", "Đã xử lý"],
], widths=[1.3, 6, 2.7, 6])

# ---------------- Details ----------------
para("III. GIẢI TRÌNH CHI TIẾT TỪNG MỤC GÓP Ý", bold=True)
para("A. Thiết kế và tính hợp lệ của thực nghiệm", bold=True, italic=True)

item("A1", "Mô hình đối chứng và ràng buộc cứng trong prompt", "Bắt buộc",
     "Chưa có thực nghiệm đối chứng; prompt ấn định culprit_id = SUSP-01 và mốc 21:40; 30 phiên cùng một chủ đề nên chưa chứng minh được tính đa dạng.",
     [
         "Bỏ ràng buộc culprit_id = \"SUSP-01\" và ví dụ 21:40 khỏi prompt OutlineAgent; prompt yêu cầu mô hình tự chọn thủ phạm trong SUSP-01..03.",
         "Mở rộng thành 3 chủ đề: Biệt thự Blackwood, Chuyến tàu đêm Thống Nhất, Phòng thí nghiệm CyberTech (10 lượt/chủ đề/mô hình).",
         "Bổ sung nghiên cứu loại trừ 4 cấu hình (prompt nguyên khối; không hậu xử lý; không vá lỗi; đầy đủ), tệp ablation_results.json. Kết quả: prompt nguyên khối thất bại ở cả 3 lượt với 35–43 lỗi Pydantic mỗi lượt; ba cấu hình đa tác tử đều đạt 3/3. Với N = 3/cấu hình, báo cáo ghi rõ chưa tách được đóng góp riêng của hậu xử lý Henssge và của vá lỗi cục bộ; đóng góp của vá lỗi được đo riêng bằng thực nghiệm tiêm lỗi (A3).",
         "Vì prompt nguyên khối ban đầu không cung cấp lược đồ JSON, bổ sung đối chứng một lần gọi công bằng (Cấu hình 1b) theo thiết kế hệ cơ sở E2E-plan của Huot và cộng sự (Agents' Room, ICLR 2025): mô hình nhận nguyên văn chỉ dẫn của cả 4 tác tử (trích tự động từ mã nguồn) cùng lược đồ JSON đầy đủ, vẫn trong một lần gọi, không hậu xử lý, không vá lỗi (e2e_baseline.py, run_e2e_baseline.py). Kết quả 9 lượt: hợp lệ cú pháp 5/9, vượt kiểm định logic 1/9 (Wilson 95%: [2,0%; 43,5%]); lỗi logic gồm giờ gây án ngoài cửa sổ TOD (3), nghi binh gắn thủ phạm (2), suy luận trích sai mã (1). Báo cáo đối chiếu với Bảng 4 của MuSR (Sprague và cộng sự, ICLR 2024), nơi cách sinh vụ án bằng một prompt cho truyện ngắn và đơn giản hơn quy trình nhiều bước.",
         f"Chỉ số đa dạng được báo cáo trung thực: với gpt-4o-mini (N = {mini['n']}) phân bố thủ phạm {dist(mini['culprit'], mini['n'])}; với gpt-4o (N = {g4o['n']}) {dist(g4o['culprit'], g4o['n'])}. Mô hình vẫn thiên lệch chọn SUSP-02 và giờ gây án còn tập trung quanh mốc ví dụ trong prompt; điểm này được đưa vào mục Hạn chế.",
         "Khắc phục phía người chơi: bổ sung bước hoán vị ngẫu nhiên mã nghi phạm bằng mã nguồn (id_shuffle.py) ở lớp phát hành POST /api/case/generate. Hoán vị được áp dụng nhất quán cho mọi mã SUSP-xx trong hồ sơ và xáo trộn thứ tự nghi phạm; logic vụ án không đổi, còn mã và vị trí thủ phạm phân bố đều (test_id_shuffle.py: 3.000 lần hoán vị, mỗi mã khoảng 1/3). Benchmark vẫn đo đầu ra thô của LLM nên báo cáo giữ nguyên số liệu thiên lệch để trung thực.",
         "gpt-4o được chạy lại trên mã nguồn hiện tại nhưng dừng ở 18/30 lượt do hết hạn mức API (18/18 hợp lệ, P50 40,98 s; benchmark_results_gpt4o_v2.json); bảng chính giữ bộ 30 lượt cũ, có ghi rõ phiên bản.",
         "Lời văn Tóm tắt, Abstract và Kết luận được điều chỉnh tương xứng kết quả đo.",
     ],
     "Mục 4.3.3, Mục 4.4 (Bảng 4.2), Mục 5.3; Tóm tắt/Abstract.",
     "agents.py, benchmark_runner.py, ablation_results.json")

item("A2", "Cỡ mẫu, thống kê và các tiêu chí chưa được đo", "Bắt buộc",
     "Mỗi mô hình 10 lượt, chưa có khoảng tin cậy; cột P95 thực chất là giá trị lớn nhất; tiêu chí A3, C1, C2 chưa đo; token là ước lượng; không phân biệt hồ sơ dự phòng.",
     [
         f"gpt-4o-mini: {mini['n']} lượt chạy mới trên mã nguồn đã sửa (benchmark_results_gpt4o_mini.json): logic hợp lệ {mini['k_logic']}/{mini['n']}, Wilson 95% [{vn(mini['ci'][0],1)}%; {vn(mini['ci'][1],1)}%], P50 = {vn(mini['p50'])} s, P95 = {vn(mini['p95'])} s, token trung bình {vn(mini['tok'],0)}/lượt.",
         f"gpt-4o: {g4o['n']} lượt (benchmark_results_gpt4o.json): logic hợp lệ {g4o['k_logic']}/{g4o['n']}, Wilson 95% [{vn(g4o['ci'][0],1)}%; {vn(g4o['ci'][1],1)}%], P50 = {vn(g4o['p50'])} s, P95 = {vn(g4o['p95'])} s.",
         "P95 tính bằng nội suy tuyến tính (numpy.percentile), không còn dùng giá trị lớn nhất.",
         "Token đo từ trường usage của API cho từng tác tử và từng lượt vá (trường token_usage trong tệp kết quả).",
         "Kết quả từng tiêu chí của Bảng 3.2 được báo cáo ở Bảng 4.3: A1, A2, A3, C2 đạt; L1 (P50 ≤ 20 s) và C1 (≤ 500 token/lượt vá) ghi nhận CHƯA ĐẠT kèm phân tích nguyên nhân.",
         f"Mỗi lượt ghi used_fallback_sample và fallback_triggered; trong {mini['n']} lượt gpt-4o-mini có {mini['fallback']} lượt dùng hồ sơ dự phòng.",
         "Các lượt gpt-4o-mini chạy thăm dò trên phiên bản prompt trước khi sửa lỗi ClueAgent không được gộp vào bảng kết quả; toàn bộ 30 lượt báo cáo được chạy liên tục trên cùng một phiên bản mã nguồn.",
     ],
     "Mục 4.2 (công thức Wilson, phân vị), Mục 4.3 (Bảng 4.1), Mục 4.5 (Bảng 4.3), Phụ lục A.",
     "benchmark_runner.py, benchmark_results_gpt4o_mini.json, benchmark_results_gpt4o.json")

item("A3", "RQ3 – hiệu quả sửa lỗi cục bộ", "Bắt buộc",
     "Chỉ có 1 lượt vá và lượt đó thất bại; khẳng định O(1) chưa chính xác vì hàm vá nhận toàn bộ hồ sơ.",
     [
         "Bổ sung thực nghiệm tiêm lỗi có kiểm soát (fault_injection_runner.py): 4 nhóm vi phạm × 20 ca = 80 ca trên gpt-4o-mini.",
         "Kết quả: tỷ lệ vá thành công chung 63,8% (51/80), Wilson 95% [52,8%; 73,4%]; theo nhóm: TOD 50,0%, trùng mã/đa thủ phạm 100,0%, thiếu vật chứng then chốt 45,0%, lỗi tham chiếu 60,0%.",
         f"Chi phí đo thực tế: 4.227,6 token/lượt vá, P50 7,21 s; so với sinh lại toàn bộ đo trên benchmark gpt-4o-mini ({vn(mini['tok'],0)} token, P50 {vn(mini['p50'])} s) giảm {vn(100*(1-4227.6/mini['tok']),1)}% token và {vn(100*(1-7.21/mini['p50']),1)}% độ trễ.",
         "Đã bỏ toàn bộ ký hiệu O(1)/O(N) trong Chương 3 và Chương 4; báo cáo nêu rõ ngữ cảnh vá vẫn tăng theo quy mô hồ sơ và chênh lệch với sinh lại toàn bộ là chênh lệch hằng số.",
         "Tiêu chí C1 (≤ 500 token) ghi nhận CHƯA ĐẠT, kèm phân tích nguyên nhân (Mục 4.5).",
     ],
     "Mục 3.9, Mục 4.4, Mục 4.5, Mục 4.7 (Bảng 4.5, Hình 4.4), Mục 5.3.",
     "fault_injection_runner.py, fault_injection_results.json")

item("A4", "Đánh giá chất lượng hồ sơ từ phía người chơi", "Bắt buộc",
     "Chưa có thử nghiệm người chơi hoặc tác tử giải độc lập; Hình 4.3 không có thực nghiệm tương ứng.",
     [
         "Chọn phương án (ii): tác tử phá án độc lập (solver_agent.py, gpt-4o-mini, T = 0,2) chỉ nhận ClientCaseDossier, không có chân lý gốc và các cờ đáp án.",
         "Kết quả trên 20 hồ sơ, 3 chủ đề: xác định đúng thủ phạm 95,0% (19/20), Wilson 95% [76,4%; 99,1%]; tìm đúng vật chứng then chốt 100%; mắc bẫy nghi binh 0%. Hạn chế: khi rà soát sau thực nghiệm phát hiện dữ liệu gửi tác tử còn cờ is_weapon (đánh dấu hung khí); cờ đã được gỡ khỏi ClientCaseDossier nhưng chưa chạy lại do hết hạn mức API, nên kết quả có thể lạc quan.",
         "Phân tích ca thất bại duy nhất (CASE-41A3E7): xác định được nguyên nhân từ phía hệ thống – prompt ClueAgent gán cứng vật chứng nghi binh EV-02 cho SUSP-02, nên khi thủ phạm là SUSP-02 hồ sơ chứa vật chứng \"minh oan\" cho thủ phạm. Đã sửa prompt (nghi binh luôn trỏ tới nghi phạm vô tội) và bổ sung luật kiểm định tương ứng.",
         "Bản sửa không sử dụng dữ liệu người chơi: bảng deduction_logs hiện chỉ chứa bản ghi của bộ kiểm thử và Solver Agent. Báo cáo nêu rõ chưa có thử nghiệm người chơi có quy trình (Mục 5.3, Phụ lục A.5).",
         "Hình 4.3 ghi rõ nguồn: 121 lỗi Pydantic từ 3 lượt cấu hình prompt nguyên khối trong ablation_results.json.",
     ],
     "Mục 4.8 (Bảng 4.6), Hình 4.3, Mục 5.3, Phụ lục A.5.",
     "solver_agent.py, solver_benchmark_results.json, agents.py, validator.py")

para("B. Mức độ khẳng định so với nội dung mã nguồn kiểm tra", bold=True, italic=True)

item("B1", "Phạm vi thực của kiểm định tính giải được", "Bắt buộc",
     "Bộ kiểm định chỉ kiểm tra cờ; case_graph.py không tham gia kiểm định; Bảng 2.1 ánh xạ Knox chưa tương ứng.",
     [
         "validate_case_diagnostics gọi build_bipartite_case_graph và yêu cầu tồn tại cạnh bác bỏ ngoại phạm của thủ phạm.",
         "Viết lại Mục 2.4 và Mục 3.8: nêu rõ bộ kiểm định chỉ bảo đảm bất biến cấu trúc (một thủ phạm, toàn vẹn tham chiếu, có vật chứng then chốt, cửa sổ TOD), không kiểm định ngữ nghĩa lời khai; phân biệt ràng buộc được kiểm tra bằng mã với ràng buộc chỉ nằm trong prompt.",
         "Bảng 2.1 phân loại rõ điều Knox nào có mã kiểm tra, điều nào chỉ được bảo đảm qua thiết kế/prompt; Điều 2 không còn ánh xạ sang Henssge.",
         "Bổ sung luật mới: vật chứng nghi binh không được gắn với thủ phạm (test_red_herring_cannot_link_to_culprit).",
         "Hình thức hóa ràng buộc không-thời gian (CSP/SMT) được trình bày ở Mục 2.4.4 và đưa vào hướng phát triển (Mục 5.4.4).",
     ],
     "Mục 2.4, Mục 2.5 (Bảng 2.1), Mục 3.1, Mục 3.8, Mục 5.3, Mục 5.4.",
     "validator.py, case_graph.py, test_validator.py")

item("B2", "Tách chân lý gốc và chặn hồ sơ không hợp lệ", "Bắt buộc",
     "API trả toàn bộ hồ sơ kèm đáp án cho client; hồ sơ lỗi vẫn được trả về và lưu is_valid = True.",
     [
         "Tách mô hình ClientCaseDossier (không có ground_truth, reasoning_chain, is_culprit, secret_innocent_fact, is_crucial, is_red_herring, linked_suspect_id); các endpoint /api/case/sample, /api/case/{id}, /api/case/generate chỉ trả mô hình này. Unity chuyển sang chấm điểm phía máy chủ (POST /api/case/verify).",
         "Các endpoint chứa đáp án (/api/case/{id}/internal, /api/case/{id}/graph) yêu cầu header X-Internal-Token khớp biến INTERNAL_API_TOKEN chỉ có phía máy chủ; nếu chưa cấu hình thì endpoint bị tắt. Chữ ký HMAC của client (có thể trích xuất) không mở được các endpoint này.",
         "Danh sách vụ án (/api/case/all, /api/cases) không còn trả culprit_id và actual_crime_time.",
         "Hồ sơ không vượt tái kiểm định được lưu is_valid = False và trả HTTP 422, không gửi tới client.",
         "Kiểm thử: test_client_isolation.py (6 ca), gồm kiểm tra chữ ký client không mở được endpoint nội bộ và danh sách không lộ thủ phạm.",
     ],
     "Mục 3.4, Mục 3.6, Mục 3.11, Mục 4.3.1, Phụ lục A.4.",
     "models.py, main.py, database.py, CaseData.cs, AccusationModal.cs, test_client_isolation.py")

item("B3", "Tham số pháp y và mô hình được sử dụng", "Khuyến nghị",
     "Dung sai ±1,5 giờ chưa có trích dẫn; kiểm thử Henssge mang tính vòng tròn; cấu hình mô hình chưa rõ.",
     [
         "Trích dẫn Henssge (1988, 2000); phân biệt khoảng tin cậy pháp y 95% (±2,8 giờ) với cửa sổ trò chơi ±1,5 giờ là lựa chọn thiết kế nằm trong khoảng tin cậy đó.",
         "test_henssge.py bổ sung ca đối chiếu với giá trị tham chiếu công bố, gọi trực tiếp bộ giải chia đôi.",
         "Mô tả đầy đủ cấu hình: nhà cung cấp (GitHub Models qua gateway 9Router cục bộ; Ollama cục bộ cho gemma4:e4b-it-qat), T = 0,7, top_p = 0,9, response_format JSON, thời điểm đo 11/2026. Bản sửa không còn dùng gemma4:31b-cloud và không còn khẳng định triển khai cục bộ cho mô hình chạy trên đám mây.",
     ],
     "Mục 2.3.5, Mục 4.1, Phụ lục A.3.",
     "test_henssge.py, llm_service.py")

para("C. An toàn thông tin", bold=True, italic=True)

item("C1", "Lộ bí mật trong kho mã nguồn công khai", "Bắt buộc – xử lý ngay",
     "Lịch sử git chứa token Hugging Face; khóa HMAC mặc định và LLM_API_KEY mặc định trong mã nguồn.",
     [
         "Token Hugging Face đã được thu hồi trên trang quản lý token của Hugging Face.",
         "Đã xóa tệp flux_test_archive.ipynb khỏi toàn bộ lịch sử bằng git filter-repo và gắn lại các thẻ v1.0.0–v1.2.0; kiểm tra lại bằng git log --all không còn chuỗi hf_… trong lịch sử.",
         "security.py không còn khóa mặc định: thiếu GAME_CLIENT_SECRET thì máy chủ dừng khởi động. Đã loại bỏ \"sk-9router-local\" khỏi llm_service.py, agents.py, solver_agent.py, fault_injection_runner.py; khóa gateway chỉ đọc từ biến môi trường LLM_API_KEY.",
     ],
     "Mục 3.11.4, Phụ lục A.4.",
     "security.py, llm_service.py, agents.py, .gitignore")

item("C2", "Giới hạn của cơ chế HMAC", "Bắt buộc",
     "HMAC với bí mật nhúng trong client không phải cơ chế xác thực; CORS mở; WebSocket không xác thực; chưa có giới hạn tần suất; một số kiểm thử thất bại.",
     [
         "Mục 3.11 trình bày lại: HMAC chỉ cản trở gọi API tùy tiện, không phải xác thực người dùng, vì bí mật có thể trích xuất từ client WebGL. Vì vậy đáp án không bao giờ được gửi tới client (B2).",
         "Bổ sung mô hình đe dọa (Bảng 3.3): người chơi đọc đáp án, lạm dụng endpoint sinh vụ án làm tiêu hao token, phát lại yêu cầu, nghe lén kênh thoại LAN, rò rỉ bí mật.",
         "Biện pháp: giới hạn tần suất 5 yêu cầu/phút/IP cho /api/case/generate (HTTP 429); CORS theo danh sách khi đặt CORS_ORIGINS (khi chưa đặt, chế độ phát triển cho phép mọi origin nhưng tắt credentials); nonce + cửa sổ thời gian 60 s chống phát lại. WebSocket phòng chơi LAN hiện chưa có xác thực phiên và được ghi nhận là hạn chế, giới hạn dùng trong mạng LAN tin cậy.",
         "Bộ kiểm thử chạy thành công toàn bộ trong cấu hình mặc định: 89/89 ca đạt.",
     ],
     "Mục 3.11 (Bảng 3.3), Mục 4.3.1.",
     "security.py, main.py, test_security.py, test_rooms.py, test_api_database_integration.py, test_assets_integration.py")

para("D. Tổng quan tài liệu", bold=True, italic=True)
item("D1", "Tổng quan nghiên cứu còn mỏng", "Khuyến nghị",
     "Chưa khảo sát sinh kịch bản có ràng buộc, sinh nội dung trò chơi bằng LLM và cơ chế tự sửa lỗi; Mục 2.1 có lý thuyết attention không dùng tới.",
     [
         "Bổ sung Mục 2.6.1–2.6.3: sinh truyện có ràng buộc (Plan-and-Write, FUDGE, Dramatron), PCG bằng LLM (PCGML, Togelius & Yannakakis), tự sửa lỗi (Self-Refine – Madaan và cộng sự, NeurIPS 2023; Reflexion); nêu điểm khác của đồ án là phản hồi đến từ bộ kiểm định tất định bên ngoài.",
         "Rút gọn Mục 2.1, bỏ công thức attention không dùng tới.",
         "Bỏ 3 trang tài liệu phần mềm khỏi danh mục tham khảo.",
     ],
     "Mục 2.1, Mục 2.6, Danh mục tài liệu tham khảo.",
     "thesis_latex (references.bib)")

para("E. Hình thức trình bày", bold=True, italic=True)
item("E", "Hình thức", "Bắt buộc / Khuyến nghị",
     "Tên đơn vị, chức danh, loại tài liệu, tên đề tài chưa thống nhất; chỉ số trên sau từ viết tắt; Unity 2.5D; dấu thập phân.",
     [
         "Bìa, Lời cảm ơn ghi \"Trường Công nghệ thông tin, Đại học Phenikaa\"; \"Giảng viên hướng dẫn\".",
         "Thống nhất \"Đồ án tốt nghiệp\" trong báo cáo, slide và tên tệp (BAO_CAO_DO_AN_TOT_NGHIEP_22010201.pdf, BAO_VE_DO_AN_TOT_NGHIEP.pptx).",
         "Tên đề tài ở Mục 5.1 và slide khớp tên trên bìa.",
         "Bỏ chỉ số trên sau từ viết tắt; sửa \"Unity 2.5D\" thành \"Unity 2D\".",
         "Các bảng, đoạn được sửa trong bản này dùng dấu phẩy thập phân.",
     ],
     "Trang bìa, Lời cảm ơn, Mục 1.6, Mục 5.1.",
     "thesis_latex/chapters/00_frontmatter.tex")

# ---------------- Questions ----------------
para("IV. TRẢ LỜI CÁC CÂU HỎI PHẢN BIỆN", bold=True)
rich([("Câu hỏi 1 (Tính hợp lệ của thực nghiệm).", True, False)])
for t in [
    "Ở bản thảo trước, tỷ lệ 90%–100% chủ yếu phản ánh ràng buộc cứng: prompt ấn định SUSP-01, mã nguồn ghi đè khung ngoại phạm và cửa sổ TOD. 30/30 hồ sơ có giờ 21:40 vì prompt chứa ví dụ mốc 21:40 và mô hình sao chép giá trị ví dụ.",
    "Bản sửa bỏ ràng buộc SUSP-01 và mốc 21:40, chạy 3 chủ đề. Tuy nhiên dữ liệu mới cho thấy mô hình vẫn thiên lệch: chọn SUSP-02 ở phần lớn số lượt và giờ gây án tập trung quanh mốc ví dụ mới trong prompt. Đây là giới hạn của việc giao lựa chọn cho LLM: mỗi lần gọi độc lập, mô hình lặp lại cùng một lựa chọn chứ không tạo được phân bố ngẫu nhiên. Đồ án đã bổ sung hoán vị ngẫu nhiên mã nghi phạm bằng mã nguồn khi phát hành hồ sơ, để thủ phạm phân bố đều với người chơi; việc bỏ mốc ví dụ 21:30 trong prompt và để mã nguồn chọn khung giờ là hướng tiếp theo.",
    "Thiết kế đối chứng: các cấu hình nguyên khối; một lần gọi với cùng chỉ dẫn và lược đồ (E2E-plan theo Huot và cộng sự, 2025); không hậu xử lý; không vá lỗi; đầy đủ. Kết quả cho thấy sinh một lần không giữ được nhất quán ngay cả khi có đủ chỉ dẫn (E2E-plan chỉ 1/9 vượt kiểm định so với 60/60 của pipeline), tuy chênh lệch này là đóng góp gộp của phân rã tác tử và hậu xử lý Henssge; với N = 3, đóng góp của hậu xử lý và vá lỗi chưa tách được và cần ≥ 30 lượt/cấu hình. Đóng góp của vá lỗi được đo riêng bằng tiêm lỗi (63,8% vá thành công).",
]:
    bullet(t)
rich([("Câu hỏi 2 (Hình thức hóa tính giải được).", True, False)])
for t in [
    "Ví dụ phản chứng: hồ sơ có EV-04 is_crucial = True, linked_suspect_id trỏ đúng thủ phạm, core_contradiction dài hơn 10 ký tự, nhưng mô tả EV-04 chỉ là \"một tách trà nguội trên bàn\" – không mâu thuẫn với lời khai \"ở thư viện 20:00–22:00\". Hồ sơ vượt toàn bộ kiểm định nhưng không suy ra được thủ phạm. Ca thực tế CASE-41A3E7 (vật chứng nghi binh minh oan cho chính thủ phạm) là một dạng lỗi tương tự mà bộ kiểm định cũ không bắt được; luật mới đã bổ sung.",
    "Hình thức hóa: mỗi nghi phạm s có hàm vị trí L(s, t); lời khai là ràng buộc L(s, t) = loc trên khoảng [a, b]; vật chứng là ràng buộc loại trừ (ví dụ nhật ký thẻ từ: L(s, t0) ≠ loc). Thủ phạm phải thỏa L(s*, t_crime) = hiện trường với t_crime ∈ cửa sổ TOD. Hồ sơ giải được duy nhất khi hệ ràng buộc chỉ thỏa được với đúng một s*; kiểm tra bằng bộ giải SMT (Z3) bằng cách khẳng định s ≠ s* và chứng minh không thỏa được.",
    "Độ phức tạp: hàm vá nhận toàn bộ danh sách nghi phạm, vật chứng và chân lý gốc nên ngữ cảnh tăng tuyến tính theo quy mô hồ sơ; khẳng định O(1) là sai và đã được bỏ. Chênh lệch với sinh lại toàn bộ là hằng số, đo được 4.227,6 so với 18.396 token.",
]:
    bullet(t)
rich([("Câu hỏi 3 (An toàn thông tin).", True, False)])
for t in [
    "Kịch bản tấn công: (1) người chơi mở công cụ phát triển trình duyệt, đọc ground_truth trong phản hồi API; (2) trích xuất bí mật HMAC từ bản WebGL, tự ký yêu cầu, gọi liên tục /api/case/generate làm tiêu hao hạn mức LLM; (3) bot quét lịch sử GitHub lấy token Hugging Face để dùng tài nguyên trả phí.",
    "HMAC dùng khóa đối xứng: ai có khóa đều ký được. Khi khóa nằm trong client phát hành công khai, mọi người dùng đều có khóa, nên HMAC không xác định được người gửi – chỉ chống sửa gói tin bởi bên thứ ba và cản trở gọi API tùy tiện.",
    "Kiến trúc khắc phục đã áp dụng: máy chủ giữ toàn bộ đáp án và chấm điểm (client chỉ nhận ClientCaseDossier); endpoint nội bộ dùng token riêng phía máy chủ; giới hạn tần suất; CORS theo danh sách; không có bí mật mặc định; token bị lộ đã thu hồi và xóa khỏi lịch sử. Khi phát hành công khai cần thêm xác thực người dùng (phiên/JWT ngắn hạn), giới hạn tần suất theo tài khoản và xác thực WebSocket qua WSS.",
]:
    bullet(t)

para("V. CAM KẾT", bold=True)
para("Sinh viên cam kết các số liệu trong báo cáo bản sửa được tính từ các tệp kết quả thô nêu trên và có thể tái lập bằng các script trong kho mã nguồn tại commit " + COMMIT + ". Những nội dung chưa đạt (tiêu chí L1, C1; chưa có thử nghiệm người chơi; thiên lệch phân bố thủ phạm) được ghi nhận trung thực trong mục Hạn chế của báo cáo.")
p = para("SINH VIÊN THỰC HIỆN", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)
para("(Ký và ghi rõ họ tên)", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT)
para("\n\n")
para("Nguyễn Ngọc Công Anh", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

doc.save(OUT)
print("saved", OUT)
print("mini", {k: v for k, v in mini.items() if k not in ("culprit", "times")}, mini["culprit"], mini["times"].most_common(5))
print("4o", {k: v for k, v in g4o.items() if k not in ("culprit", "times")})
