import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 1. Colors & Theme (Phenikaa Academic Defense)
COLOR_BG = RGBColor(248, 249, 250)         # #F8F9FA
COLOR_NAVY = RGBColor(29, 53, 87)          # Phenikaa Navy #1D3557
COLOR_RED = RGBColor(230, 57, 70)          # Phenikaa Red #E63946
COLOR_TEAL = RGBColor(42, 157, 143)        # Success / Symbolic #2A9D8F
COLOR_AMBER = RGBColor(217, 119, 6)        # Highlight / Warning #D97706
COLOR_DARK = RGBColor(15, 23, 42)          # Deep Slate #0F172A
COLOR_MUTED = RGBColor(100, 116, 139)      # Slate Muted #64748B
COLOR_WHITE = RGBColor(255, 255, 255)      # Pure White
COLOR_BORDER = RGBColor(226, 232, 240)     # Border Subtle #E2E8F0
COLOR_CARD_BG = RGBColor(255, 255, 255)

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"
FONT_CODE = "Consolas"
TOTAL_SLIDES = 23


def generate_comprehensive_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    root_dir = os.path.dirname(os.path.abspath(__file__))
    figures_dir = os.path.join(root_dir, "thesis_latex", "figures")

    def add_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.fill.background()

    def add_hdr(slide, chapter, title, subtitle=None):
        tb_ch = slide.shapes.add_textbox(Inches(0.8), Inches(0.32), Inches(11.7), Inches(0.28))
        p_ch = tb_ch.text_frame.paragraphs[0]
        p_ch.text = chapter.upper()
        p_ch.font.name = FONT_HEADING
        p_ch.font.size = Pt(11)
        p_ch.font.bold = True
        p_ch.font.color.rgb = COLOR_RED

        tb_ti = slide.shapes.add_textbox(Inches(0.8), Inches(0.58), Inches(11.7), Inches(0.55))
        p_ti = tb_ti.text_frame.paragraphs[0]
        p_ti.text = title
        p_ti.font.name = FONT_HEADING
        p_ti.font.size = Pt(22)
        p_ti.font.bold = True
        p_ti.font.color.rgb = COLOR_DARK

        if subtitle:
            tb_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.13), Inches(11.7), Inches(0.3))
            p_sub = tb_sub.text_frame.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.name = FONT_BODY
            p_sub.font.size = Pt(12)
            p_sub.font.color.rgb = COLOR_MUTED

        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.48), Inches(0.9), Inches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = COLOR_NAVY
        bar.line.fill.background()

    def add_ftr(slide, current_slide, total_slides=TOTAL_SLIDES):
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.02), Inches(11.733), Inches(0.01))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_BORDER
        line.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(0.8), Inches(7.06), Inches(9.0), Inches(0.3))
        p = tb.text_frame.paragraphs[0]
        p.text = "TRƯỜNG ĐẠI HỌC PHENIKAA • KHOA KHOA HỌC MÁY TÍNH • ĐỒ ÁN TỐT NGHIỆP 2026"
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_MUTED

        tb_num = slide.shapes.add_textbox(Inches(10.533), Inches(7.06), Inches(2.0), Inches(0.3))
        p_num = tb_num.text_frame.paragraphs[0]
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.text = f"{current_slide:02d} / {total_slides:02d}"
        p_num.font.name = FONT_BODY
        p_num.font.size = Pt(10)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_NAVY

    def add_card_box(slide, left, top, width, height):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.adjustments[0] = 0.03
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1)
        return card

    def add_callout_box(slide, left, top, width, height, col, label, body):
        tint_map = {
            COLOR_RED: RGBColor(254, 242, 242),
            COLOR_AMBER: RGBColor(255, 247, 237),
            COLOR_TEAL: RGBColor(240, 253, 250),
            COLOR_NAVY: RGBColor(238, 242, 255),
        }
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        box.adjustments[0] = 0.04
        box.fill.solid()
        box.fill.fore_color.rgb = tint_map.get(col, RGBColor(241, 245, 249))
        box.line.color.rgb = col
        box.line.width = Pt(1)
        box.vertical_anchor = MSO_ANCHOR.TOP

        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.14)
        tf.margin_right = Inches(0.14)
        tf.margin_top = Inches(0.1)
        tf.margin_bottom = Inches(0.08)

        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = body
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10)
        p2.font.color.rgb = COLOR_DARK
        p2.space_before = Pt(4)
        return box

    def add_notes(slide, text):
        slide.notes_slide.notes_text_frame.text = text.strip()

    def add_three_column_cards(slide, cards_data, body_size=11, callout_mode=True):
        p_w = Inches(3.71)
        p_gap = Inches(0.3)
        start_x = Inches(0.8)
        for idx, (t1, t2, col, desc, lbl, box_text) in enumerate(cards_data):
            px = start_x + idx * (p_w + p_gap)
            add_card_box(slide, px, Inches(1.78), p_w, Inches(4.95))

            tb_th = slide.shapes.add_textbox(px + Inches(0.2), Inches(1.9), p_w - Inches(0.4), Inches(0.65))
            tf_th = tb_th.text_frame
            tf_th.word_wrap = True
            p_th = tf_th.paragraphs[0]
            p_th.text = t1
            p_th.font.name = FONT_HEADING
            p_th.font.size = Pt(13)
            p_th.font.bold = True
            p_th.font.color.rgb = col

            p_tag = tf_th.add_paragraph()
            p_tag.text = t2.upper()
            p_tag.font.name = FONT_HEADING
            p_tag.font.size = Pt(9)
            p_tag.font.bold = True
            p_tag.font.color.rgb = COLOR_MUTED

            if callout_mode:
                tb_desc = slide.shapes.add_textbox(px + Inches(0.2), Inches(2.58), p_w - Inches(0.4), Inches(1.55))
                tf_desc = tb_desc.text_frame
                tf_desc.word_wrap = True
                p_d = tf_desc.paragraphs[0]
                p_d.text = desc
                p_d.font.name = FONT_BODY
                p_d.font.size = Pt(body_size)
                p_d.font.color.rgb = COLOR_DARK
                add_callout_box(slide, px + Inches(0.2), Inches(4.25), p_w - Inches(0.4), Inches(2.28), col, lbl, box_text)
            else:
                tb_desc = slide.shapes.add_textbox(px + Inches(0.2), Inches(2.6), p_w - Inches(0.4), Inches(3.95))
                tf_desc = tb_desc.text_frame
                tf_desc.word_wrap = True
                p_d = tf_desc.paragraphs[0]
                p_d.text = desc
                p_d.font.name = FONT_BODY
                p_d.font.size = Pt(body_size)
                p_d.font.color.rgb = COLOR_DARK

    # ==========================================
    # SLIDE 1: COVER (OFFICIAL REGISTERED TITLE)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1)

    tb_u = s1.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.733), Inches(0.55))
    p1 = tb_u.text_frame.paragraphs[0]
    p1.text = "TRƯỜNG ĐẠI HỌC PHENIKAA • KHOA KHOA HỌC MÁY TÍNH"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_NAVY

    b1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.38), Inches(3.6), Inches(0.4))
    b1.adjustments[0] = 0.1
    b1.fill.solid()
    b1.fill.fore_color.rgb = COLOR_RED
    b1.line.fill.background()
    p_b = b1.text_frame.paragraphs[0]
    p_b.alignment = PP_ALIGN.CENTER
    p_b.text = "BÁO CÁO ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC"
    p_b.font.name = FONT_HEADING
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_WHITE

    tb_title = s1.shapes.add_textbox(Inches(0.8), Inches(1.98), Inches(11.733), Inches(2.45))
    tf = tb_title.text_frame
    tf.word_wrap = True
    p_t1 = tf.paragraphs[0]
    p_t1.text = (
        "NGHIÊN CỨU VÀ XÂY DỰNG TRÒ CHƠI TRINH THÁM GIẢI ĐỐ TRÊN NỀN TẢNG WEB, "
        "ỨNG DỤNG MÔ HÌNH NGÔN NGỮ LỚN (LLM) ĐỂ SINH TỰ ĐỘNG CÁC BỘ HỒ SƠ VỤ ÁN CÓ TÍNH LOGIC VÀ NHẤT QUÁN"
    )
    p_t1.font.name = FONT_HEADING
    p_t1.font.size = Pt(23)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_DARK

    p_t2 = tf.add_paragraph()
    p_t2.text = "Hướng tiếp cận Neuro-Symbolic kết hợp Hệ đa tác tử và Bộ kiểm định hình thức"
    p_t2.font.name = FONT_BODY
    p_t2.font.size = Pt(16)
    p_t2.font.bold = True
    p_t2.font.color.rgb = COLOR_NAVY
    p_t2.space_before = Pt(10)

    add_card_box(s1, Inches(0.8), Inches(4.7), Inches(11.733), Inches(1.95))
    tb_info = s1.shapes.add_textbox(Inches(1.1), Inches(4.9), Inches(11.1), Inches(1.55))
    tf_info = tb_info.text_frame

    p_i1 = tf_info.paragraphs[0]
    p_i1.text = "Sinh viên thực hiện: Nguyễn Ngọc Công Anh  |  MSSV: 22010201  |  Lớp: K16-KHMT"
    p_i1.font.name = FONT_HEADING
    p_i1.font.size = Pt(15)
    p_i1.font.bold = True
    p_i1.font.color.rgb = COLOR_NAVY

    p_i2 = tf_info.add_paragraph()
    p_i2.text = "Cán bộ hướng dẫn: TS. Nguyễn Văn Tánh  |  Ngành: Khoa học máy tính (Chuyên ngành AI)"
    p_i2.font.name = FONT_HEADING
    p_i2.font.size = Pt(15)
    p_i2.font.bold = True
    p_i2.font.color.rgb = COLOR_RED
    p_i2.space_before = Pt(8)

    p_i3 = tf_info.add_paragraph()
    p_i3.text = "Hà Nội – Năm 2026  •  Bảo vệ Đồ án Tốt nghiệp Đại học"
    p_i3.font.name = FONT_BODY
    p_i3.font.size = Pt(13)
    p_i3.font.color.rgb = COLOR_MUTED
    p_i3.space_before = Pt(8)

    add_notes(s1, """Kính thưa Quý Thầy Cô trong Hội đồng chấm đồ án tốt nghiệp và các bạn sinh viên.
Em tên là Nguyễn Ngọc Công Anh, sinh viên lớp K16-KHMT, Khoa Khoa học máy tính, Trường Đại học Phenikaa.
Hôm nay em xin phép trình bày báo cáo đồ án tốt nghiệp với đề tài: "Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán", thực hiện theo hướng tiếp cận Neuro-Symbolic kết hợp Hệ đa tác tử và Bộ kiểm định hình thức, dưới sự hướng dẫn khoa học của TS. Nguyễn Văn Tánh.""")

    # ==========================================
    # SLIDE 2: AGENDA
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2)
    add_hdr(s2, "MỤC LỤC BÁO CÁO", "Cấu Trúc Báo Cáo Đồ Án Tốt Nghiệp", "Bố cục 5 chương trọng tâm từ cơ sở lý thuyết tới kiểm chứng thực nghiệm")
    add_ftr(s2, 2)

    col_w = Inches(2.18)
    col_gap = Inches(0.2)
    start_x = Inches(0.8)
    cards_data = [
        ("CHƯƠNG 1", "TỔNG QUAN", COLOR_RED, "Phát biểu Bài toán", [
            "Hành trình phát triển đề tài",
            "3 giới hạn của LLM đơn khối",
            "3 câu hỏi nghiên cứu RQ1–3",
            "Phạm vi & 4 đóng góp chính",
        ]),
        ("CHƯƠNG 2", "LÝ THUYẾT", COLOR_NAVY, "Cơ sở & Đối chiếu", [
            "Transformer & Nhận thức kép",
            "10 điều răn Ronald Knox",
            "Mô hình nhiệt học Henssge",
            "Đồ thị hai phía & SOTA",
        ]),
        ("CHƯƠNG 3", "KIẾN TRÚC", COLOR_TEAL, "Thiết kế Hệ thống", [
            "7 quyết định ADR & Framework",
            "4 Tác tử + Smart Fallback",
            "Kiểm định ký hiệu & Vá O(1)",
            "SQLite WAL & Unity 6 URP",
        ]),
        ("CHƯƠNG 4", "THỰC NGHIỆM", COLOR_AMBER, "Đánh giá Định lượng", [
            "Cấu hình máy & 53 unit tests",
            "30 phiên đo 3 mô hình LLM",
            "Ca lỗi EV-03 của gh/gpt-4o",
            "Phân rã độ trễ từng tác tử",
        ]),
        ("CHƯƠNG 5", "KẾT LUẬN", COLOR_DARK, "Nghiệm thu & Q&A", [
            "Đối chiếu kết quả RQ1, 2, 3",
            "Hạn chế kỹ thuật hiện tại",
            "Giải trình phản biện",
            "Hướng phát triển tiếp theo",
        ]),
    ]

    for idx, (ch_tag, sub_tag, color_tag, title_text, bullets) in enumerate(cards_data):
        cx = start_x + idx * (col_w + col_gap)
        add_card_box(s2, cx, Inches(1.78), col_w, Inches(4.95))

        tb_h = s2.shapes.add_textbox(cx + Inches(0.15), Inches(1.9), col_w - Inches(0.3), Inches(0.65))
        p_c1 = tb_h.text_frame.paragraphs[0]
        p_c1.text = ch_tag
        p_c1.font.name = FONT_HEADING
        p_c1.font.size = Pt(13)
        p_c1.font.bold = True
        p_c1.font.color.rgb = color_tag

        p_c2 = tb_h.text_frame.add_paragraph()
        p_c2.text = sub_tag
        p_c2.font.name = FONT_HEADING
        p_c2.font.size = Pt(9)
        p_c2.font.bold = True
        p_c2.font.color.rgb = COLOR_MUTED

        tb_c = s2.shapes.add_textbox(cx + Inches(0.15), Inches(2.65), col_w - Inches(0.3), Inches(3.9))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True

        p_ct = tf_c.paragraphs[0]
        p_ct.text = title_text
        p_ct.font.name = FONT_HEADING
        p_ct.font.size = Pt(12)
        p_ct.font.bold = True
        p_ct.font.color.rgb = color_tag

        for b in bullets:
            p_b = tf_c.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.name = FONT_BODY
            p_b.font.size = Pt(10.5)
            p_b.font.color.rgb = COLOR_DARK
            p_b.space_before = Pt(7)

    add_notes(s2, """Báo cáo của em gồm 5 chương tuần tự: Chương 1 trình bày bối cảnh và lý do lựa chọn kiến trúc lai cho đề tài Web game trinh thám; Chương 2 đi sâu vào mô hình y pháp Henssge và đồ thị hai phía; Chương 3 giải trình 7 quyết định lựa chọn công nghệ ADR, đường ống 4 tác tử và bộ kiểm định; Chương 4 báo cáo thực nghiệm 30 phiên trên 3 mô hình LLM và phân tích ca lỗi thực tế; Chương 5 tổng kết nghiệm thu các câu hỏi nghiên cứu và giải trình phản biện.""")

    # ==========================================
    # SLIDE 3: RESEARCH EVOLUTION & WEB + UNITY PLATFORM
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3)
    add_hdr(
        s3,
        "CHƯƠNG 1: TỔNG QUAN",
        "Quá Trình Phát Triển Đề Tài & Kiến Trúc Nền Tảng Web",
        "Giải quyết trọn vẹn yêu cầu \"trên nền tảng Web\" và \"hồ sơ vụ án có tính logic, nhất quán\""
    )
    add_ftr(s3, 3)

    add_three_column_cards(s3, [
        ("1. Nguyên mẫu Khởi đầu", "V0/frontend & Web API", COLOR_NAVY,
         "Khởi điểm theo tên đề tài đăng ký, tác giả xây dựng nguyên mẫu Web React (V0/frontend/) kết nối dịch vụ FastAPI gọi LLM sinh hồ sơ vụ án.",
         "KIẾN TRÚC DỊCH VỤ WEB:",
         "Toàn bộ lõi sinh án và chấm điểm được triển khai dưới dạng dịch vụ Web RESTful API (FastAPI, HTTP/JSON, WebSockets, CORS, tài liệu /docs)."),
        ("2. Thách thức Phát sinh", "Giới hạn Prompt Thuần túy", COLOR_RED,
         "Khi thử nghiệm sinh trực tiếp bằng LLM đơn khối, hồ sơ thường vấp phải ảo giác giờ tử vong, mâu thuẫn lời khai ngoại phạm và không bảo đảm tính giải được.",
         "YÊU CẦU KHOA HỌC:",
         "Để bảo đảm cụm từ \"có tính logic và nhất quán\" trong tên đề tài, hệ thống cần kết hợp LLM với bộ kiểm định toán học tất định độc lập."),
        ("3. Giải pháp Hoàn thiện", "Neuro-Symbolic Đa nền tảng", COLOR_TEAL,
         "Nâng cấp lõi lên 4 tác tử tuần tự kèm phương trình Henssge, đồ thị hai phía, và mở rộng Client Unity 6 URP 2D (tương thích WebGL trình duyệt và máy trạm).",
         "GIÁ TRỊ ĐẠT ĐƯỢC:",
         "Đạt 100% hợp lệ lược đồ trên 30 phiên thử nghiệm, kiểm soát 90–100% tính logic, hỗ trợ chơi đơn hoặc phối hợp nhóm qua mạng LAN."),
    ])

    add_notes(s3, """Kính thưa Hội đồng, slide này giải trình sự phát triển tự nhiên từ tên đề tài đăng ký ban đầu đến kiến trúc hoàn chỉnh hiện tại.
Giai đoạn đầu, em đã cài đặt nguyên mẫu Web React tại thư mục V0/frontend kết nối tới FastAPI Web API.
Tuy nhiên, thực nghiệm cho thấy nếu chỉ gọi LLM trực tiếp thì không thể đáp ứng yêu cầu "logic và nhất quán" do hiện tượng ảo giác thông số pháp y và sai lệch ngoại phạm. Vì vậy, em nâng cấp phần lõi thành hệ Neuro-Symbolic kết hợp 4 tác tử và bộ kiểm định toán học, đồng thời mở rộng Client lên Unity 6 URP 2D — vừa hỗ trợ xuất bản WebGL trên trình duyệt, vừa mở khóa các tính năng 2D và mạng LAN.""")

    # ==========================================
    # SLIDE 4: THREE LIMITATIONS OF MONOLITHIC LLMs
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4)
    add_hdr(
        s4,
        "CHƯƠNG 1: TỔNG QUAN",
        "Ba Giới Hạn Bản Chất Của LLM Nguyên Khối Trong Trinh Thám",
        "Vì sao cơ chế dự đoán token tự quy hồi không tự bảo đảm tính nhất quán hình thức"
    )
    add_ftr(s4, 4)

    add_three_column_cards(s4, [
        ("1. Ảo giác Nhân quả & Sinh học", "Biến thiên Thời gian", COLOR_RED,
         "LLM sinh văn bản theo xác suất ngữ cảnh tiếp theo P(w_t | w_<t), không sở hữu bộ giải phương trình vật lý hay đồng hồ logic nội tại.",
         "VÍ DỤ RỦI RO Y PHÁP:",
         "Thân nhiệt tử thi đo được và khung giờ tử vong ước đoán lệch khỏi quy luật tỏa nhiệt sau khi chết, hoặc giờ gây án rơi ra ngoài cửa sổ TOD."),
        ("2. Suy giảm Suy luận Đa bước", "Lan truyền Sai số", COLOR_AMBER,
         "Khi một câu lệnh đơn lẻ phải tự sinh đồng thời nạn nhân, 3 nghi phạm và 4 vật chứng, sai lệch ở phần đầu kéo theo đứt gãy toàn bộ chuỗi lập luận phía sau.",
         "BIỂU HIỆN THỰC NGHIỆM:",
         "Xuất hiện lỗi tham chiếu thực thể hỏng (ví dụ trỏ tới mã nghi phạm không tồn tại) hoặc manh mối không đủ để bác bỏ ngoại phạm của thủ phạm."),
        ("3. Chi phí Tái sinh Toàn phần", "Độ phức tạp O(N)", COLOR_NAVY,
         "Nếu phát hiện mâu thuẫn logic và xử lý bằng cách hủy toàn bộ hồ sơ để sinh lại từ đầu, hệ thống tiêu tốn lặp lại toàn bộ lượng token đầu vào/ra.",
         "HỆ QUẢ VẬN HÀNH:",
         "Kéo dài thời gian chờ đợi trong trò chơi tương tác (từ ~2,500–3,500 tokens mỗi lần lặp lại) và không giữ được phần bối cảnh hợp lệ trước đó."),
    ])

    add_notes(s4, """Về mặt toán học, các LLM giải mã theo xác suất tự quy hồi nên gặp ba rào cản lớn khi áp dụng vào trinh thám:
Thứ nhất là ảo giác thông số sinh học và thời gian tử vong.
Thứ hai là suy giảm độ chính xác khi phải giữ ràng buộc nhiều thực thể cùng lúc trong một prompt đơn lẻ.
Thứ ba là bài toán chi phí: nếu sửa lỗi bằng cách sinh lại cả hồ sơ từ đầu sẽ gây lãng phí khoảng 2.500 đến 3.500 token và tăng độ trễ người dùng.""")

    # ==========================================
    # SLIDE 5: GOALS & RESEARCH QUESTIONS (RQs)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5)
    add_hdr(
        s5,
        "CHƯƠNG 1: TỔNG QUAN",
        "Mục Tiêu & Ba Câu Hỏi Nghiên Cứu Cốt Lõi (RQ1–RQ3)",
        "Định hình phương pháp tiếp cận Neuro-Symbolic kết hợp Hệ đa tác tử"
    )
    add_ftr(s5, 5)

    add_three_column_cards(s5, [
        ("RQ1: Phân rã Đa tác tử", "Multi-Agent Pipeline", COLOR_NAVY,
         "Làm thế nào để phân rã quy trình sáng tác vụ án thành chuỗi tác tử tuần tự nhằm giảm tải ngữ cảnh và tách chân lý gốc khỏi dữ liệu người chơi?",
         "HƯỚNG GIẢI QUYẾT:",
         "Cài đặt 4 tác tử chuyên biệt: OutlineAgent -> CharacterAgent -> ClueAgent -> DeductionAgent với lược đồ Pydantic v2 hẹp từng bước."),
        ("RQ2: Kiểm định Ký hiệu", "Formal Verification", COLOR_TEAL,
         "Làm thế nào để hình thức hóa quy luật làm lạnh thi thể Henssge và cấu trúc chứng cứ đồ thị hai phía làm bộ lọc kiểm định tất định?",
         "HƯỚNG GIẢI QUYẾT:",
         "Giao quyền tính cửa sổ TOD cho giải thuật chia đôi Henssge (validator.py) và kiểm tra 7 mã lỗi ViolationType trên đồ thị hai phía."),
        ("RQ3: Tối ưu Sửa lỗi", "Localized Patch Repair", COLOR_RED,
         "Cơ chế sửa lỗi cục bộ với độ phức tạp ngữ cảnh hằng số O(1) giúp cô lập vi phạm và tiết kiệm tài nguyên ra sao so với tái sinh O(N)?",
         "HƯỚNG GIẢI QUYẾT:",
         "Định tuyến thông báo chẩn đoán tới đúng phân hệ lỗi (outline / character / clue), chỉ xử lý lát cắt ngữ cảnh ~300–500 tokens."),
    ])

    add_notes(s5, """Ba câu hỏi nghiên cứu định hướng toàn bộ đồ án:
RQ1 giải quyết khâu phân rã nhận thức thông qua 4 tác tử trong agents.py.
RQ2 giải quyết tính công bằng và nhất quán bằng phương trình Henssge và đồ thị hai phía.
RQ3 giải quyết chi phí khôi phục lỗi thông qua định tuyến vá lỗi cục bộ O(1).""")

    # ==========================================
    # SLIDE 6: RONALD KNOX'S FAIR-PLAY FORMALIZATION
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6)
    add_hdr(
        s6,
        "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT",
        "Hình Thức Hóa Mười Điều Răn Trinh Thám Công Bằng (Knox, 1929)",
        "Chuyển hóa quy tắc văn học trinh thám cổ điển thành ràng buộc mã nguồn Pydantic v2 & Validator"
    )
    add_ftr(s6, 6)

    add_card_box(s6, Inches(0.8), Inches(1.78), Inches(6.6), Inches(4.95))
    tb_k_l = s6.shapes.add_textbox(Inches(1.0), Inches(1.92), Inches(6.2), Inches(4.65))
    tf_k_l = tb_k_l.text_frame
    tf_k_l.word_wrap = True
    pk_0 = tf_k_l.paragraphs[0]
    pk_0.text = "ÁNH XẠ CÁC QUY TẮC KNOX SANG RÀNG BUỘC HỆ THỐNG (BẢNG 2.1)"
    pk_0.font.name = FONT_HEADING
    pk_0.font.size = Pt(12.5)
    pk_0.font.bold = True
    pk_0.font.color.rgb = COLOR_NAVY

    knox_rules = [
        "• Điều 1 (Không yếu tố siêu nhiên): Thời điểm tử vong và hạ thân nhiệt phải tuân theo phương trình nhiệt học Henssge.",
        "• Điều 2 (Không chất độc giả tưởng): Vũ khí và nguyên nhân tử vong phải là cơ chế vật lý có thật.",
        "• Điều 3 (Không lối đi bí mật ẩn giấu): Mọi vị trí hiện trường và nơi thu giữ vật chứng được công bố rõ trong hồ sơ.",
        "• Điều 4 (Thủ phạm xuất hiện từ đầu): Tập nghi phạm cố định V_S; ground_truth.culprit_id bắt buộc thuộc {s.id}.",
        "• Điều 5 & 6 (Không may rủi): Thám tử tách biệt khỏi V_S; chấm điểm yêu cầu chọn đúng s* kèm vật chứng then chốt.",
        "• Điều 7 & 8 (Không anh em sinh đôi / Không giấu manh mối): Kiểm tra DUPLICATE_ID và công khai toàn bộ V_E lên bảng ghim.",
    ]
    for r in knox_rules:
        p_r = tf_k_l.add_paragraph()
        p_r.text = r
        p_r.font.name = FONT_BODY
        p_r.font.size = Pt(10.5)
        p_r.font.color.rgb = COLOR_DARK
        p_r.space_before = Pt(7)

    add_card_box(s6, Inches(7.65), Inches(1.78), Inches(4.88), Inches(4.95))
    tb_k_r = s6.shapes.add_textbox(Inches(7.85), Inches(1.92), Inches(4.48), Inches(4.65))
    tf_k_r = tb_k_r.text_frame
    tf_k_r.word_wrap = True

    pkr_0 = tf_k_r.paragraphs[0]
    pkr_0.text = "HIỆN THỰC TRONG MÃ NGUỒN"
    pkr_0.font.name = FONT_HEADING
    pkr_0.font.size = Pt(12.5)
    pkr_0.font.bold = True
    pkr_0.font.color.rgb = COLOR_TEAL

    code_items = [
        ("1. Tập đóng nghi phạm:", "2 <= len(suspects) <= 5 (mặc định 3); đúng 1 nghi phạm mang cờ is_culprit = True."),
        ("2. Ràng buộc mã định danh:", "Kiểm tra duy nhất SUSP-* và EV-*, chặn lỗi DUPLICATE_ID và SCHEMA_ERROR."),
        ("3. Tính công bằng suy luận:", "Mọi vật chứng V_E (tối thiểu 2, chuẩn 3–4) hiển thị minh bạch trên Corkboard UI."),
        ("4. Chống nộp bừa (Anti-Spam):", "Nếu tổng vật chứng >= 3 và người chơi chọn toàn bộ V_E -> gán nhãn SPAM_DETECTED (0 điểm)."),
    ]
    for head_txt, desc_txt in code_items:
        ph = tf_k_r.add_paragraph()
        ph.text = head_txt
        ph.font.name = FONT_HEADING
        ph.font.size = Pt(11)
        ph.font.bold = True
        ph.font.color.rgb = COLOR_NAVY
        ph.space_before = Pt(9)

        pb = tf_k_r.add_paragraph()
        pb.text = desc_txt
        pb.font.name = FONT_BODY
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = COLOR_DARK
        pb.space_before = Pt(2)

    add_notes(s6, """Để trò chơi bảo đảm tính công bằng cho người suy luận, tác giả áp dụng 8 điều khoản liên quan trong Mười điều răn của Ronald Knox (1929) vào tầng lược đồ Pydantic và hàm kiểm định: ví dụ Điều 1 ánh xạ sang định luật tỏa nhiệt Henssge, Điều 4 khóa tập nghi phạm đóng, Điều 7 kiểm tra trùng ID, Điều 8 bảo đảm công khai toàn bộ manh mối lên giao diện bảng ghim.""")

    # ==========================================
    # SLIDE 7: RELATED WORK COMPARISON (TABLE 2.2)
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_bg(s7)
    add_hdr(
        s7,
        "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT",
        "Đối Chiếu Với Các Công Trình Nghiên Cứu Liên Quan (Bảng 2.2)",
        "Xác định khoảng trống nghiên cứu giữa đánh giá tĩnh, chơi kịch bản có sẵn và tạo sinh giải được"
    )
    add_ftr(s7, 7)

    works = [
        (
            "MuSR (Sprague et al., ICLR 2024)",
            "Benchmark suy luận nhiều bước",
            COLOR_NAVY,
            "• Sinh cây suy luận sang văn bản (~1,000 từ) để đo năng lực CoT của LLM.\n"
            "• Hạn chế: Là bộ kiểm thử đánh giá thụ động tĩnh, không phải game tương tác.\n"
            "• Không tích hợp ràng buộc y pháp Henssge hay cơ chế sửa lỗi cục bộ."
        ),
        (
            "Digital Detectives (Wu et al., ACL 2024)",
            "Đa tác tử chơi Jubensha",
            COLOR_AMBER,
            "• Cho các tác tử LLM nhập vai suy luận trên kịch bản có sẵn bởi con người.\n"
            "• Hạn chế: Chưa giải quyết bài toán tự động sáng tác vụ án mới.\n"
            "• Chưa kiểm chứng tính giải được bằng đồ thị hay hàm chấm điểm tất định."
        ),
        (
            "ContraDoc (Li et al., NAACL 2024)",
            "Phát hiện tự mâu thuẫn văn bản",
            COLOR_MUTED,
            "• Tập dữ liệu gán nhãn phát hiện xung đột logic tự thân trong văn bản dài.\n"
            "• Hạn chế: Dừng ở bài toán phân loại/hậu kiểm văn bản tổng quát.\n"
            "• Không nằm trong vòng lặp tạo sinh có khả năng sửa lỗi định hướng."
        ),
        (
            "Hệ thống Đề xuất (Đồ án 2026)",
            "Neuro-Symbolic Tạo sinh & Chơi Game",
            COLOR_TEAL,
            "• Đường ống 4 tác tử tuần tự + Bộ kiểm định tất định (Henssge + Đồ thị hai phía).\n"
            "• Sửa lỗi cục bộ O(1) + Chấm điểm tất định trong bộ nhớ (< 0.1 ms).\n"
            "• Kiến trúc Web RESTful API kết hợp Unity 6 URP 2D (Co-op LAN 3 người)."
        ),
    ]

    w_col = Inches(2.81)
    w_gap = Inches(0.16)
    for idx, (title_w, sub_w, col_w_tag, body_w) in enumerate(works):
        wx = Inches(0.8) + idx * (w_col + w_gap)
        card = add_card_box(s7, wx, Inches(1.78), w_col, Inches(4.95))
        if idx == 3:
            card.line.color.rgb = COLOR_TEAL
            card.line.width = Pt(2)
            card.fill.fore_color.rgb = RGBColor(240, 253, 250)

        tb = s7.shapes.add_textbox(wx + Inches(0.15), Inches(1.92), w_col - Inches(0.3), Inches(4.65))
        tf_w = tb.text_frame
        tf_w.word_wrap = True
        pw0 = tf_w.paragraphs[0]
        pw0.text = title_w
        pw0.font.name = FONT_HEADING
        pw0.font.size = Pt(12)
        pw0.font.bold = True
        pw0.font.color.rgb = col_w_tag

        pw1 = tf_w.add_paragraph()
        pw1.text = sub_w.upper()
        pw1.font.name = FONT_HEADING
        pw1.font.size = Pt(8.5)
        pw1.font.bold = True
        pw1.font.color.rgb = COLOR_MUTED
        pw1.space_before = Pt(3)

        pw2 = tf_w.add_paragraph()
        pw2.text = body_w
        pw2.font.name = FONT_BODY
        pw2.font.size = Pt(10.5)
        pw2.font.color.rgb = COLOR_DARK
        pw2.space_before = Pt(10)

    add_notes(s7, """Khi đối chiếu với ba công trình tiêu biểu đã công bố tại ICLR 2024, ACL 2024 và NAACL 2024:
MuSR tập trung tạo bộ dữ liệu tĩnh để đánh giá CoT; Deciphering Digital Detectives cho tác tử chơi trên kịch bản viết sẵn; còn ContraDoc dừng ở phát hiện mâu thuẫn văn bản tổng quát.
Đồ án của em kết hợp cả khâu tạo sinh chủ động lẫn kiểm định vật lý Henssge, kiểm tra đồ thị hai phía, sửa lỗi cục bộ O(1) và đóng gói thành trò chơi hoàn chỉnh.""")

    # ==========================================
    # SLIDE 8: HENSSGE FORENSIC COOLING MODEL
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_bg(s8)
    add_hdr(
        s8,
        "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT",
        "Mô Hình Làm Lạnh Thi Thể Hai Hàm Mũ Của Henssge (1988)",
        "Cơ sở vật lý y pháp khóa cứng cửa sổ thời gian tử vong (TOD) thay cho ước đoán của LLM"
    )
    add_ftr(s8, 8)

    add_card_box(s8, Inches(0.8), Inches(1.78), Inches(5.8), Inches(4.95))
    tb_h = s8.shapes.add_textbox(Inches(1.0), Inches(1.92), Inches(5.4), Inches(4.65))
    tf_h = tb_h.text_frame
    tf_h.word_wrap = True

    ph0 = tf_h.paragraphs[0]
    ph0.text = "PHƯƠNG TRÌNH HAI HÀM MŨ HENSSGE (validator.py)"
    ph0.font.name = FONT_HEADING
    ph0.font.size = Pt(12.5)
    ph0.font.bold = True
    ph0.font.color.rgb = COLOR_NAVY

    ph1 = tf_h.add_paragraph()
    ph1.text = "Phi(t) = (T_body - T_amb) / (37.2 - T_amb)"
    ph1.font.name = FONT_CODE
    ph1.font.size = Pt(12.5)
    ph1.font.bold = True
    ph1.font.color.rgb = COLOR_RED
    ph1.space_before = Pt(8)

    ph2 = tf_h.add_paragraph()
    ph2.text = "• Khi T_amb <= 23.2°C:\n  Phi(t) = 1.25·exp(-k·t) - 0.25·exp(-5·k·t)\n• Khi T_amb > 23.2°C:\n  Phi(t) = 1.11·exp(-k·t) - 0.11·exp(-10·k·t)"
    ph2.font.name = FONT_CODE
    ph2.font.size = Pt(10.5)
    ph2.font.color.rgb = COLOR_DARK
    ph2.space_before = Pt(8)

    ph3 = tf_h.add_paragraph()
    ph3.text = "Hằng số làm lạnh k (theo cân nặng M kg & hệ số C):"
    ph3.font.name = FONT_BODY
    ph3.font.size = Pt(11)
    ph3.font.color.rgb = COLOR_DARK
    ph3.space_before = Pt(8)

    ph4 = tf_h.add_paragraph()
    ph4.text = "k = 1.2815 / (M · C)^0.625 - 0.0284"
    ph4.font.name = FONT_CODE
    ph4.font.size = Pt(12.5)
    ph4.font.bold = True
    ph4.font.color.rgb = COLOR_NAVY
    ph4.space_before = Pt(4)

    ph5 = tf_h.add_paragraph()
    ph5.text = "• Cửa sổ TOD = [T_discovery - (t* + 1.5h), T_discovery - (t* - 1.5h)]\n• Động cơ ký hiệu ghi đè trực tiếp TOD vào hồ sơ qua apply_henssge_tod_window."
    ph5.font.name = FONT_BODY
    ph5.font.size = Pt(10.5)
    ph5.font.color.rgb = COLOR_MUTED
    ph5.space_before = Pt(8)

    fig_henssge = os.path.join(figures_dir, "henssge_curves.png")
    if os.path.exists(fig_henssge):
        s8.shapes.add_picture(fig_henssge, Inches(6.85), Inches(1.82), Inches(5.68), Inches(4.8))

    add_notes(s8, """Để loại trừ tình trạng LLM tự bịa thân nhiệt và giờ chết mâu thuẫn nhau, hệ thống tích hợp phương trình làm lạnh thi thể hai hàm mũ chuẩn y pháp của Henssge (1988), có xét hai chế độ nhiệt độ môi trường ngưỡng 23.2 độ C, cân nặng M và hệ số trang phục C. Sau khi giải ra khoảng thời gian sau tử vong t*, bộ kiểm định khóa cứng cửa sổ TOD với biên độ ±1.5 giờ.""")

    # ==========================================
    # SLIDE 9: BISECTION ROOT FINDER
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_bg(s9)
    add_hdr(
        s9,
        "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT",
        "Giải Phương Trình Henssge Bằng Phương Pháp Chia Đôi (Bisection)",
        "Hội tụ nghiệm duy nhất t* trên miền [0, 48] giờ trong thời gian dưới 1 mili-giây"
    )
    add_ftr(s9, 9)

    add_card_box(s9, Inches(0.8), Inches(1.78), Inches(5.65), Inches(4.95))
    tb_b_l = s9.shapes.add_textbox(Inches(1.0), Inches(1.94), Inches(5.25), Inches(4.65))
    tf_b_l = tb_b_l.text_frame
    tf_b_l.word_wrap = True
    pbl0 = tf_b_l.paragraphs[0]
    pbl0.text = "CƠ SỞ GIẢI TÍCH SỐ HỌC (THUẬT TOÁN 1)"
    pbl0.font.name = FONT_HEADING
    pbl0.font.size = Pt(12.5)
    pbl0.font.bold = True
    pbl0.font.color.rgb = COLOR_NAVY

    pbl_body = (
        "1. Phương trình Phi(t) = Phi_target là phương trình siêu việt, không có nghiệm giải tích dạng đóng.\n\n"
        "2. Với k > 0, hàm Phi(t) đơn điệu giảm ngặt trên [0, 48] giờ từ giá trị Phi(0) = 1.0.\n\n"
        "3. Khi Phi(48) < Phi_target < 1.0, theo tính liên tục tồn tại nghiệm t* duy nhất để giải số bằng phương pháp chia đôi.\n\n"
        "4. Tham số thực thi thực tế: miền [0.0, 48.0] giờ, sai số epsilon = 1e-4, tối đa N_max = 100 bước lặp."
    )
    pbl1 = tf_b_l.add_paragraph()
    pbl1.text = pbl_body
    pbl1.font.name = FONT_BODY
    pbl1.font.size = Pt(11)
    pbl1.font.color.rgb = COLOR_DARK
    pbl1.space_before = Pt(10)

    add_card_box(s9, Inches(6.7), Inches(1.78), Inches(5.83), Inches(4.95))
    tb_b_r = s9.shapes.add_textbox(Inches(6.9), Inches(1.94), Inches(5.43), Inches(4.65))
    tf_b_r = tb_b_r.text_frame
    tf_b_r.word_wrap = True
    pbr0 = tf_b_r.paragraphs[0]
    pbr0.text = "CÀI ĐẶT THỰC TẾ TRONG detective-backend/validator.py"
    pbr0.font.name = FONT_HEADING
    pbr0.font.size = Pt(12)
    pbr0.font.bold = True
    pbr0.font.color.rgb = COLOR_TEAL

    pbr_code = tf_b_r.add_paragraph()
    pbr_code.text = (
        "def solve_pmi_bisection(body_temp, ambient_temp,\n"
        "                        body_weight_kg=70.0, cooling_factor=1.0):\n"
        "    phi_target = (body_temp - ambient_temp) / (37.2 - ambient_temp)\n"
        "    if phi_target >= 1.0: return 0.0\n"
        "    if phi_target <= 0.0: return None\n"
        "    k = henssge_cooling_constant(body_weight_kg, cooling_factor)\n"
        "    a, b = 0.0, 48.0\n"
        "    if henssge_phi(b, k, ambient_temp) - phi_target > 0: return None\n"
        "    for _ in range(100):\n"
        "        m = (a + b) / 2.0\n"
        "        fm = henssge_phi(m, k, ambient_temp) - phi_target\n"
        "        if abs(fm) < 1e-4 or (b - a) / 2.0 < 1e-4: return m\n"
        "        if (henssge_phi(a, k, ambient_temp) - phi_target) * fm < 0: b = m\n"
        "        else: a = m\n"
        "    return (a + b) / 2.0\n\n"
        "• Được kiểm chứng độc lập bởi 30/30 test trong test_henssge.py."
    )
    pbr_code.font.name = FONT_CODE
    pbr_code.font.size = Pt(9.5)
    pbr_code.font.color.rgb = COLOR_DARK
    pbr_code.space_before = Pt(8)

    add_notes(s9, """Do phương trình Henssge là phương trình siêu việt không có nghiệm đóng, hệ thống giải số bằng phương pháp chia đôi trên khoảng [0, 48] giờ với ngưỡng hội tụ 10^-4. Toàn bộ hàm solve_pmi_bisection và biến đổi biên độ TOD đã được kiểm chứng vượt qua 30 trên 30 kịch bản trong tệp test_henssge.py.""")

    # ==========================================
    # SLIDE 10: BIPARTITE GRAPH MODELING
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    add_bg(s10)
    add_hdr(
        s10,
        "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT",
        "Mô Hình Hóa Quan Hệ Chứng Cứ Bằng Đồ Thị Hai Phía",
        "Kiểm tra tính duy nhất của thủ phạm và sự tồn tại của manh mối bẻ gãy ngoại phạm"
    )
    add_ftr(s10, 10)

    add_card_box(s10, Inches(0.8), Inches(1.78), Inches(5.8), Inches(4.95))
    tb_b = s10.shapes.add_textbox(Inches(1.0), Inches(1.94), Inches(5.4), Inches(4.65))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True

    pb0 = tf_b.paragraphs[0]
    pb0.text = "ĐỒ THỊ HAI PHÍA G = (V_S ∪ V_E, E)"
    pb0.font.name = FONT_HEADING
    pb0.font.size = Pt(12.5)
    pb0.font.bold = True
    pb0.font.color.rgb = COLOR_NAVY

    pb1 = tf_b.add_paragraph()
    pb1.text = (
        "• V_S: Tập đỉnh nghi phạm (địa chỉ định danh SUSP-01..SUSP-k).\n"
        "• V_E: Tập đỉnh vật chứng (EV-01..EV-m).\n"
        "• Phân loại 3 lớp cạnh:\n"
        "   - E_alibi: Lời khai ngoại phạm bao phủ actual_crime_time.\n"
        "   - E_break: Chứng cứ then chốt (is_crucial=True) bẻ gãy ngoại phạm.\n"
        "   - E_herring: Chứng cứ nghi binh (is_red_herring=True) tạo độ nhiễu."
    )
    pb1.font.name = FONT_BODY
    pb1.font.size = Pt(10.5)
    pb1.font.color.rgb = COLOR_DARK
    pb1.space_before = Pt(8)

    pb2 = tf_b.add_paragraph()
    pb2.text = "ĐIỀU KIỆN BẤT BIẾN KHẢ GIẢI:"
    pb2.font.name = FONT_HEADING
    pb2.font.size = Pt(11.5)
    pb2.font.bold = True
    pb2.font.color.rgb = COLOR_RED
    pb2.space_before = Pt(10)

    pb3 = tf_b.add_paragraph()
    pb3.text = (
        "1. Duy nhất một thủ phạm s* khớp culprit_id ∈ V_S.\n"
        "2. Tồn tại ít nhất 1 cạnh bẻ gãy e ∈ E_break phủ định ngoại phạm s*.\n"
        "3. Toàn bộ liên kết linked_suspect_id phải trỏ tới nút thuộc V_S."
    )
    pb3.font.name = FONT_BODY
    pb3.font.size = Pt(10.5)
    pb3.font.color.rgb = COLOR_DARK
    pb3.space_before = Pt(5)

    fig_bipartite = os.path.join(figures_dir, "bipartite_graph.png")
    if os.path.exists(fig_bipartite):
        s10.shapes.add_picture(fig_bipartite, Inches(6.85), Inches(1.82), Inches(5.68), Inches(4.8))

    add_notes(s10, """Bên cạnh thời gian tử vong, hệ thống biểu diễn quan hệ giữa nghi phạm và chứng cứ dưới dạng đồ thị hai phía G = (V_S, V_E, E). Một hồ sơ chỉ được chấp nhận khi có duy nhất một thủ phạm s*, có ít nhất một manh mối then chốt bẻ gãy được lời khai ngoại phạm của s*, và mọi mã tham chiếu phải trỏ đúng tới nút hợp lệ trong tập nghi phạm.""")

    # ==========================================
    # SLIDE 11: ARCHITECTURE OVERVIEW & ADR FRAMEWORK CHOICES
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    add_bg(s11)
    add_hdr(
        s11,
        "CHƯƠNG 3: KIẾN TRÚC HỆ THỐNG",
        "Kiến Trúc 3 Tầng & Lý Do Lựa Chọn Các Framework (ADR-001..007)",
        "Phân tích ưu thế kỹ thuật của từng công nghệ so với phương án đối chứng (Bảng 3.1)"
    )
    add_ftr(s11, 11)

    fig_arch = os.path.join(figures_dir, "architecture_overview.png")
    if os.path.exists(fig_arch):
        s11.shapes.add_picture(fig_arch, Inches(0.8), Inches(1.78), Inches(6.25), Inches(4.9))

    fw_cards = [
        ("1. FastAPI (ASGI) vs Flask / Django / Node.js", COLOR_NAVY,
         "Giữ kết nối I/O bất đồng bộ 10–20s chờ 4 tác tử LLM + WebSocket nhóm 3 người (rooms.py) không nghẽn luồng như WSGI của Flask; đồng bộ Python khoa học."),
        ("2. Pydantic v2 (Rust) vs dataclasses / Marshmallow", COLOR_TEAL,
         "Nhân Rust pydantic-core phân giải nhanh, ép kiểu và bắt lỗi biểu thức chính quy (^SUSP-\\d{2}$) trực tiếp tại cổng API."),
        ("3. SQLite WAL + SQLAlchemy 2.0 vs PostgreSQL / MongoDB", COLOR_AMBER,
         "Đảm bảo ACID & khóa ngoại ON DELETE CASCADE; WAL đọc/ghi song song không nghẽn và nhúng gọn trong detective.db không cần cài máy chủ rời."),
        ("4. Unity 6 URP 2D + Web API vs Thuần React / Unreal 5", COLOR_RED,
         "Vượt rào cản hộp cát trình duyệt để quét phòng LAN qua UDP cổng 47777 (LanDiscoveryClient.cs), kết xuất ánh sáng 2D/dây chỉ đỏ mượt và vẫn hỗ trợ WebGL."),
    ]
    for i, (ftitle, fcol, fdesc) in enumerate(fw_cards):
        top_y = Inches(1.78 + i * 1.25)
        add_card_box(s11, Inches(7.25), top_y, Inches(5.28), Inches(1.15))
        tb_f = s11.shapes.add_textbox(Inches(7.4), top_y + Inches(0.08), Inches(4.98), Inches(1.0))
        tf_f = tb_f.text_frame
        tf_f.word_wrap = True
        pf0 = tf_f.paragraphs[0]
        pf0.text = ftitle
        pf0.font.name = FONT_HEADING
        pf0.font.size = Pt(11)
        pf0.font.bold = True
        pf0.font.color.rgb = fcol
        pf1 = tf_f.add_paragraph()
        pf1.text = fdesc
        pf1.font.name = FONT_BODY
        pf1.font.size = Pt(9.5)
        pf1.font.color.rgb = COLOR_DARK
        pf1.space_before = Pt(3)

    add_notes(s11, """Về lựa chọn framework ở Mục 3.1, đồ án thiết lập 7 quyết định kiến trúc ADR với lý do kỹ thuật rõ ràng:
- Chọn FastAPI ASGI thay vì Flask WSGI để không bị khóa luồng khi chờ LLM 10-20 giây và xử lý đồng thời WebSocket.
- Chọn Pydantic v2 lõi Rust thay vì Marshmallow hoặc dataclasses để ép kiểu và bắt lỗi regex tức thì.
- Chọn SQLite WAL + SQLAlchemy 2.0 thay vì MongoDB hay PostgreSQL để vừa giữ toàn vẹn khóa ngoại CASCADE, vừa không bắt người chơi cài máy chủ DB rời.
- Kết hợp dịch vụ Web API với Client Unity 6 URP 2D nhằm vừa hỗ trợ xuất bản WebGL, vừa vượt giới hạn Sandbox trình duyệt để phát gói tin UDP dò phòng LAN trên cổng 47777.""")

    # ==========================================
    # SLIDE 12: 4-AGENT PIPELINE + PER-AGENT SMART FALLBACK
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    add_bg(s12)
    add_hdr(
        s12,
        "CHƯƠNG 3: KIẾN TRÚC HỆ THỐNG",
        "Đường Ống 4 Tác Tử Tuần Tự & Smart Fallback Cấp Độ Agent",
        "Cài đặt trực tiếp trên BaseAgent (agents.py) thay vì khung LangChain/AutoGen cồng kềnh"
    )
    add_ftr(s12, 12)

    col_w4 = Inches(2.78)
    col_gap4 = Inches(0.2)
    agents_data = [
        ("1. OutlineAgent", "Khung vụ án & Chân lý gốc", COLOR_NAVY,
         "• Sinh title, summary, Victim (ForensicData) và GroundTruth.\n"
         "• Ấn định culprit_id = \"SUSP-01\".\n"
         "• Hậu xử lý: apply_henssge_tod_window tính và ghi đè TOD."),
        ("2. CharacterAgent", "Nghi phạm & Ngoại phạm", COLOR_RED,
         "• Sinh danh sách Suspect (mặc định 3 nghi phạm).\n"
         "• Đúng 1 thủ phạm is_culprit=True có alibi trùm actual_crime_time.\n"
         "• Gắn secret_innocent_fact cho người vô tội."),
        ("3. ClueAgent", "Vật chứng & Nghi binh", COLOR_AMBER,
         "• Sinh 3–4 Evidence vật chứng hiện trường.\n"
         "• Bắt buộc >= 1 vật chứng then chốt (is_crucial=True).\n"
         "• Bổ sung tối thiểu 1 vật chứng nghi binh (is_red_herring=True)."),
        ("4. DeductionAgent", "Chuỗi suy luận đa bước", COLOR_TEAL,
         "• Tổng hợp ReasoningChain gồm 2–3 DeductionStep.\n"
         "• Trích xuất đúng clue_ids hợp lệ dẫn tới thủ phạm.\n"
         "• Lưu metadata: agent_latencies & agent_models."),
    ]

    for idx, (t1, t2, col, desc) in enumerate(agents_data):
        cx = Inches(0.8) + idx * (col_w4 + col_gap4)
        add_card_box(s12, cx, Inches(1.78), col_w4, Inches(3.55))

        tb_a = s12.shapes.add_textbox(cx + Inches(0.15), Inches(1.9), col_w4 - Inches(0.3), Inches(3.3))
        tf_a = tb_a.text_frame
        tf_a.word_wrap = True
        pa1 = tf_a.paragraphs[0]
        pa1.text = t1
        pa1.font.name = FONT_HEADING
        pa1.font.size = Pt(13)
        pa1.font.bold = True
        pa1.font.color.rgb = col

        pa2 = tf_a.add_paragraph()
        pa2.text = t2.upper()
        pa2.font.name = FONT_HEADING
        pa2.font.size = Pt(8.5)
        pa2.font.bold = True
        pa2.font.color.rgb = COLOR_MUTED

        pa3 = tf_a.add_paragraph()
        pa3.text = desc
        pa3.font.name = FONT_BODY
        pa3.font.size = Pt(10)
        pa3.font.color.rgb = COLOR_DARK
        pa3.space_before = Pt(8)

    add_callout_box(
        s12,
        Inches(0.8), Inches(5.48), Inches(11.733), Inches(1.28),
        COLOR_NAVY,
        "CƠ CHẾ CHUYỂN MẠCH DỰ PHÒNG THÔNG MINH THEO TỪNG TÁC TỬ (SMART PER-AGENT FALLBACK)",
        "• Khi mô hình chính gặp lỗi hạn mức/kết nối (HTTP 402/502/503), chỉ riêng Agent gặp lỗi tự động duyệt chuỗi FALLBACK_CANDIDATES: "
        "gemini/gemma-4-31b-it -> gh/gpt-3.5-turbo-0613 -> gh/gpt-4o-mini -> gemma4:e4b-it-qat (Ollama nội bộ RTX 3050).\n"
        "• Benchmark & GenerationMetadata ghi nhận chính xác tên mô hình mỗi Agent đã chạy (agent_models), chứng minh ngay cả khi lõi Agent rơi xuống mô hình nhỏ hơn, bộ kiểm định vẫn bảo đảm kết quả hợp lệ."
    )

    add_notes(s12, """Quy trình tạo sinh được phân rã qua 4 lớp kế thừa BaseAgent: OutlineAgent, CharacterAgent, ClueAgent và DeductionAgent.
Thay vì dùng framework trừu tượng nặng như LangChain, việc cài đặt trực tiếp trên AsyncOpenAI giúp tích hợp cơ chế Smart Per-Agent Fallback: nếu mô hình chính bị lỗi kết nối hoặc hết hạn mức, từng Agent có thể tự chuyển sang mô hình dự phòng nhỏ hơn như gh/gpt-3.5-turbo-0613 hoặc gemma4 chạy offline, đồng thời báo cáo rõ tên mô hình từng Agent trong log thực nghiệm.""")

    # ==========================================
    # SLIDE 13: SYMBOLIC VALIDATOR (7 VIOLATION TYPES) & VERIFY FLOW
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    add_bg(s13)
    add_hdr(
        s13,
        "CHƯƠNG 3: KIẾN TRÚC HỆ THỐNG",
        "Động Cơ Kiểm Định Ký Hiệu & Luồng Xác Thực Tách Biệt LLM",
        "Rà soát 7 mã vi phạm ViolationType và chấm điểm kết án tất định dưới 0.1 ms"
    )
    add_ftr(s13, 13)

    add_card_box(s13, Inches(0.8), Inches(1.78), Inches(6.2), Inches(4.95))
    tb_v = s13.shapes.add_textbox(Inches(1.0), Inches(1.92), Inches(5.8), Inches(4.65))
    tf_v = tb_v.text_frame
    tf_v.word_wrap = True
    pv0 = tf_v.paragraphs[0]
    pv0.text = "7 LOẠI VI PHẠM TRONG validate_case_diagnostics (BẢNG 3.4)"
    pv0.font.name = FONT_HEADING
    pv0.font.size = Pt(12)
    pv0.font.bold = True
    pv0.font.color.rgb = COLOR_NAVY

    viols = [
        "1. TOD_PHYSICS (outline): Thân nhiệt phi lý hoặc độ dài cửa sổ TOD ngoài [15, 720] phút.",
        "2. CRIME_TIME_OUTSIDE_TOD (outline): actual_crime_time nằm ngoài cửa sổ Henssge.",
        "3. ALIBI_UNBROKEN (clue/outline): Ngoại phạm thủ phạm trùm giờ án nhưng thiếu manh mối phá vỡ.",
        "4. NO_CRUCIAL_CLUE (clue): Không có vật chứng nào gắn cờ is_crucial = True.",
        "5. DUPLICATE_ID (character/clue): Trùng mã định danh SUSP-* hoặc EV-*.",
        "6. MULTIPLE_CULPRITS (character/outline): Số hung thủ khác 1 hoặc lệch culprit_id.",
        "7. SCHEMA_ERROR (clue/reasoning): Tham chiếu linked_suspect_id / clue_ids không tồn tại.",
    ]
    for v_txt in viols:
        pv = tf_v.add_paragraph()
        pv.text = v_txt
        pv.font.name = FONT_BODY
        pv.font.size = Pt(10.2)
        pv.font.color.rgb = COLOR_DARK
        pv.space_before = Pt(6)

    fig_flow = os.path.join(figures_dir, "decoupled_flowchart.png")
    if os.path.exists(fig_flow):
        s13.shapes.add_picture(fig_flow, Inches(7.2), Inches(1.8), Inches(5.33), Inches(3.3))

    add_callout_box(
        s13,
        Inches(7.2), Inches(5.22), Inches(5.33), Inches(1.5),
        COLOR_TEAL,
        "CHẤM ĐIỂM TẤT ĐỊNH (/api/case/verify)",
        "• evaluate_player_deduction chấm thang 100 điểm trong RAM (< 0.1 ms, 0 token): 40đ đúng thủ phạm + 40đ chứng cứ then chốt + 20đ độ cô đọng (-25đ/nghi binh).\n"
        "• 6 trạng thái DeductionVerdict; lọc SPAM_DETECTED khi chọn hết vật chứng."
    )

    add_notes(s13, """Mọi hồ sơ sau bước ghép sơ bộ phải vượt qua 5 nhóm kiểm tra trả về 7 loại vi phạm tường minh trong ViolationType.
Đồng thời ở pha chơi game (/api/case/verify), hệ thống tách biệt hoàn toàn LLM khỏi khâu chấm điểm: hàm evaluate_player_deduction thực thi phép toán tập hợp thuần túy trong RAM dưới 0.1 mili-giây và trả về kết quả phân loại DeductionVerdict.""")

    # ==========================================
    # SLIDE 14: LOCALIZED PATCH REPAIR O(1) vs O(N)
    # ==========================================
    s14 = prs.slides.add_slide(blank_layout)
    add_bg(s14)
    add_hdr(
        s14,
        "CHƯƠNG 3: KIẾN TRÚC HỆ THỐNG",
        "Cơ Chế Sửa Lỗi Cục Bộ Định Tuyến Theo Phân Hệ Vi Phạm",
        "So sánh độ phức tạp ngữ cảnh token: Sửa cục bộ O(1) so với Tái sinh toàn phần O(N)"
    )
    add_ftr(s14, 14)

    add_card_box(s14, Inches(0.8), Inches(1.78), Inches(5.7), Inches(4.95))
    tb_on = s14.shapes.add_textbox(Inches(1.0), Inches(1.94), Inches(5.3), Inches(4.65))
    tf_on = tb_on.text_frame
    tf_on.word_wrap = True
    p_on0 = tf_on.paragraphs[0]
    p_on0.text = "CHIẾN LƯỢC TÁI SINH TOÀN BỘ: ĐỘ PHỨC TẠP O(N)"
    p_on0.font.name = FONT_HEADING
    p_on0.font.size = Pt(12.5)
    p_on0.font.bold = True
    p_on0.font.color.rgb = COLOR_RED

    p_on1 = tf_on.add_paragraph()
    p_on1.text = (
        "Khi xuất hiện vi phạm logic đơn lẻ, toàn bộ 4 tác tử bị hủy và chạy lại từ đầu:\n\n"
        "• Lượng token lặp lại: N = T_Outline + T_Character + T_Clue + T_Deduction "
        "(ước tính khoảng 2,500 – 3,500 tokens cho hồ sơ 3 nghi phạm, 3–4 vật chứng).\n\n"
        "• Gia tăng độ trễ chờ đợi và đánh mất các thành phần văn cảnh đã hợp lệ ở bước trước."
    )
    p_on1.font.name = FONT_BODY
    p_on1.font.size = Pt(11)
    p_on1.font.color.rgb = COLOR_DARK
    p_on1.space_before = Pt(10)

    add_card_box(s14, Inches(6.83), Inches(1.78), Inches(5.7), Inches(4.95))
    tb_o1 = s14.shapes.add_textbox(Inches(7.03), Inches(1.94), Inches(5.3), Inches(2.95))
    tf_o1 = tb_o1.text_frame
    tf_o1.word_wrap = True
    p_o1_0 = tf_o1.paragraphs[0]
    p_o1_0.text = "GIẢI PHÁP ĐỒ ÁN: SỬA LỖI CỤC BỘ O(1) (THUẬT TOÁN 2)"
    p_o1_0.font.name = FONT_HEADING
    p_o1_0.font.size = Pt(12.5)
    p_o1_0.font.bold = True
    p_o1_0.font.color.rgb = COLOR_TEAL

    p_o1_1 = tf_o1.add_paragraph()
    p_o1_1.text = (
        "Định tuyến theo ConstraintViolation.component tới đúng tác tử liên quan:\n"
        "• component == 'outline'   -> OutlineAgent.repair_tod()\n"
        "• component == 'character' -> CharacterAgent.repair_suspects()\n"
        "• component == 'clue'      -> ClueAgent.repair_clues()\n\n"
        "Sau khi vá phân hệ outline, tự động chạy lại apply_henssge_tod_window."
    )
    p_o1_1.font.name = FONT_BODY
    p_o1_1.font.size = Pt(10.5)
    p_o1_1.font.color.rgb = COLOR_DARK
    p_o1_1.space_before = Pt(8)

    add_callout_box(
        s14,
        Inches(7.03), Inches(5.05), Inches(5.3), Inches(1.48),
        COLOR_TEAL,
        "NGỮ CẢNH THU GỌN HẰNG SỐ O(1)",
        "Mỗi lượt vá lỗi chỉ truyền lát cắt dữ liệu tối thiểu của thực thể vi phạm và thông điệp chẩn đoán (ước tính khoảng 300–500 tokens), bảo toàn nguyên vẹn các phần hồ sơ hợp lệ."
    )

    add_notes(s14, """Khi validate_case_diagnostics phát hiện lỗi, thay vì tái sinh cả 4 tác tử tiêu tốn khoảng 2.500 đến 3.500 token, hệ thống đọc trường component của ConstraintViolation để gọi đúng phương thức repair tương ứng với lát cắt ngữ cảnh chỉ khoảng 300 đến 500 token.""")

    # ==========================================
    # SLIDE 15: SQLITE WAL & HMAC-SHA-256 SECURITY
    # ==========================================
    s15 = prs.slides.add_slide(blank_layout)
    add_bg(s15)
    add_hdr(
        s15,
        "CHƯƠNG 3: KIẾN TRÚC HỆ THỐNG",
        "Lưu Trữ Quan Hệ SQLite (WAL) & Bảo Mật HMAC-SHA-256",
        "Chuẩn hóa dữ liệu bền vững trong detective.db (database.py) và xác thực gói tin (security.py)"
    )
    add_ftr(s15, 15)

    add_three_column_cards(s15, [
        ("1. Bảng cases (CaseRecord)", "Hồ sơ Vụ án", COLOR_NAVY,
         "• case_id (unique, indexed), title, summary, country, era, mystery_type.\n"
         "• culprit_id, actual_crime_time, is_valid, validator_score.\n"
         "• dossier_json lưu toàn văn cấu trúc; đồng bộ tự động từ thư mục cases/ lúc init_db().",
         "CHẾ ĐỘ SQLITE WAL:",
         "Bật PRAGMA journal_mode=WAL và foreign_keys=ON; đọc/ghi đồng thời không khóa luồng khi chơi nhóm."),
        ("2. deduction_logs & benchmark_runs", "Lịch sử & Đo đạc", COLOR_TEAL,
         "• deduction_logs (DeductionRecord): khóa ngoại case_id (ON DELETE CASCADE), accused_id, verdict, score, found_crucial_count.\n"
         "• benchmark_runs (BenchmarkRunRecord): model_name, trial_index, schema_valid, logic_valid, latency_seconds.",
         "TRUY VẤN THỐNG KÊ:",
         "Cung cấp API thống kê độ khó qua GET /api/case/{case_id}/stats và lưu vết 30 phiên thực nghiệm."),
        ("3. ClientIntegrityMiddleware", "Bảo mật HMAC-SHA-256", COLOR_RED,
         "• Yêu cầu mọi lệnh gọi đính kèm chữ ký X-Game-Signature tính bằng HMAC-SHA-256 trên tổ hợp (Method, Path, Timestamp, Nonce, SHA256(Body)).\n"
         "• Kiểm tra sai lệch thời gian <= 60 giây và lưu Nonce một lần chống phát lại.",
         "KIỂM CHỨNG ĐỘC LẬP:",
         "Đạt 7/7 kịch bản test_security.py; chặn hoàn toàn truy cập trái phép hoặc spam LLM bằng mã 403."),
    ])

    add_notes(s15, """Ở tầng lưu trữ (database.py), hệ thống dùng SQLite bật chế độ Write-Ahead Logging (WAL) và SQLAlchemy 2.0 với ba bảng thực tế: cases, deduction_logs và benchmark_runs.
Ở tầng bảo mật cổng API (security.py), ClientIntegrityMiddleware kiểm tra chữ ký HMAC-SHA-256 kèm timestamp và nonce dùng một lần trong cửa sổ 60 giây để ngăn chặn tấn công phát lại hoặc gọi API tiêu tốn token trái phép.""")

    # ==========================================
    # SLIDE 16: UNITY 6 URP 2D & LAN CO-OP CLIENT
    # ==========================================
    s16 = prs.slides.add_slide(blank_layout)
    add_bg(s16)
    add_hdr(
        s16,
        "CHƯƠNG 3: KIẾN TRÚC HỆ THỐNG",
        "Giao Diện Điều Tra Unity 6 URP 2D & Phối Hợp Nhóm LAN",
        "Không gian bàn làm việc thám tử độ phân giải 16:9 (1920x1080) kết nối REST API & WebSocket"
    )
    add_ftr(s16, 16)

    fig_cork = os.path.join(figures_dir, "corkboard_ui.png")
    if os.path.exists(fig_cork):
        s16.shapes.add_picture(fig_cork, Inches(0.8), Inches(1.78), Inches(5.7), Inches(3.85))

    fig_modal = os.path.join(figures_dir, "forensic_modal.png")
    if os.path.exists(fig_modal):
        s16.shapes.add_picture(fig_modal, Inches(6.83), Inches(1.78), Inches(5.7), Inches(3.85))

    add_callout_box(
        s16,
        Inches(0.8), Inches(5.75), Inches(11.733), Inches(1.08),
        COLOR_NAVY,
        "CÁC MÔ-ĐUN C# CHÍNH TRONG UNITY 6 (6000.5.8f1)",
        "• CorkboardManager.cs & DraggableCard.cs: Sinh thẻ Polaroid kéo thả, nối dây chỉ đỏ động; GameController.cs nạp sẵn StreamingAssets/sample_case.json.\n"
        "• AutopsyReportModal.cs & BankersLampController.cs: Hiển thị báo cáo pháp y Henssge, hiệu ứng đèn bàn (35/25/35 ms) và đàn hồi exp(-7t)cos(14t).\n"
        "• DetectiveNetworkManager.cs, LanDiscoveryClient.cs (UDP 47777) & VoiceChatController.cs: Phối hợp 3 thám tử qua WebSocket /ws/rooms/{room_id} (PCM 16-bit)."
    )

    add_notes(s16, """Trên giao diện người chơi, Client Unity 6 URP 2D mô phỏng bàn điều tra gồm bảng ghim Polaroid nối dây chỉ đỏ thời gian thực, cửa sổ báo cáo pháp y Henssge, hộp thoại phóng đại ảnh, và đèn bàn tương tác vật lý. Ngoài chơi đơn, hệ thống hỗ trợ tối đa 3 người chơi phối hợp qua mạng cục bộ LAN với khả năng tự động tìm phòng qua UDP cổng 47777 và truyền thoại PCM 16-bit qua WebSocket.""")

    # ==========================================
    # SLIDE 17: EXPERIMENTAL SETUP & UNIT TESTS
    # ==========================================
    s17 = prs.slides.add_slide(blank_layout)
    add_bg(s17)
    add_hdr(
        s17,
        "CHƯƠNG 4: THỰC NGHIỆM & ĐÁNH GIÁ",
        "Môi Trường Thực Nghiệm & Kiểm Chứng Độ Tin Cậy Mã Nguồn",
        "Đo đạc trên cấu hình phần cứng đồng nhất và bộ kiểm thử tự động pytest"
    )
    add_ftr(s17, 17)

    add_three_column_cards(s17, [
        ("1. Cấu hình Máy Thực nghiệm", "Mục 4.1.1 Báo cáo", COLOR_NAVY,
         "• Thiết bị: Laptop Lenovo Legion 5 (82JW).\n"
         "• CPU: AMD Ryzen 5 5600H (6 nhân, 12 luồng, 3.30 GHz).\n"
         "• RAM: 24 GB DDR4 3200 MHz.\n"
         "• GPU: NVIDIA GeForce RTX 3050 Laptop (4 GB GDDR6).\n"
         "• OS & Runtime: Windows 11 Pro 64-bit, Python 3.13.13.",
         "MÔI TRƯỜNG PHẦN MỀM:",
         "FastAPI 0.137.1, Uvicorn 0.49.0, Pydantic 2.14.3, SQLAlchemy 2.0.51, Unity 6000.5.8f1, cổng 9Router :20128."),
        ("2. Thiết lập Benchmark", "30 Phiên Độc Lập", COLOR_TEAL,
         "• Thực thi qua benchmark_runner.py trên cùng chủ đề: \"Bí ẩn Biệt thự Blackwood\".\n"
         "• 3 mô hình x 10 phiên = 30 phiên:\n"
         "  - gh/gpt-4o-mini (Thương mại tối ưu)\n"
         "  - gh/gpt-4o (Thương mại cỡ lớn)\n"
         "  - ollama/gemma4:31b-cloud (Trọng số mở)",
         "LƯU VẾT DỮ LIỆU:",
         "Toàn bộ 30 phiên lưu đồng thời vào benchmark_results.json và bảng benchmark_runs trong SQLite."),
        ("3. Kiểm thử Đơn vị Hệ thống", "53/53 Core Tests Pass", COLOR_RED,
         "Chạy pytest trong trạng thái mặc định bật HMAC-SHA-256:\n"
         "• test_henssge.py: 30/30 đạt.\n"
         "• test_validator.py: 12/12 đạt.\n"
         "• test_security.py: 7/7 đạt.\n"
         "• test_database.py: 4/4 đạt.",
         "TÍNH CHÍNH XÁC MÔ-ĐUN:",
         "Mô-đun phòng WebSocket (test_rooms.py) đạt 10/11 (1 case HTTP bị chặn 403 đúng quy tắc vì cố tình không ký HMAC)."),
    ])

    add_notes(s17, """Toàn bộ quá trình thực nghiệm được thực thi trên cấu hình máy thực tế Lenovo Legion 5, Ryzen 5 5600H, 24 GB RAM, RTX 3050 4 GB và Python 3.13.13.
Ở mức kiểm thử đơn vị dưới trạng thái mặc định bật bảo mật HMAC-SHA-256, 53 trên 53 kịch bản thuộc 4 mô-đun lõi đều vượt qua 100%. Đối với đánh giá đa mô hình, em chạy 30 phiên độc lập chia đều cho 3 đại diện: gh/gpt-4o-mini, gh/gpt-4o và ollama/gemma4:31b-cloud.""")

    # ==========================================
    # SLIDE 18: BENCHMARK RESULTS - PASS RATE & ERROR TAXONOMY
    # ==========================================
    s18 = prs.slides.add_slide(blank_layout)
    add_bg(s18)
    add_hdr(
        s18,
        "CHƯƠNG 4: THỰC NGHIỆM & ĐÁNH GIÁ",
        "Kết Quả 1: Tỷ Lệ Hợp Lệ Schema & Vượt Qua Kiểm Định Logic",
        "Tổng hợp 30 phiên thực nghiệm từ bảng benchmark_runs (Bảng 4.1, Hình 4.1 & Hình 4.3)"
    )
    add_ftr(s18, 18)

    fig_pass = os.path.join(figures_dir, "chart_pass_rate.png")
    if os.path.exists(fig_pass):
        s18.shapes.add_picture(fig_pass, Inches(0.8), Inches(1.78), Inches(5.7), Inches(3.8))

    fig_tax = os.path.join(figures_dir, "error_taxonomy.png")
    if os.path.exists(fig_tax):
        s18.shapes.add_picture(fig_tax, Inches(6.83), Inches(1.78), Inches(5.7), Inches(3.8))

    add_callout_box(
        s18,
        Inches(0.8), Inches(5.72), Inches(5.7), Inches(1.12),
        COLOR_TEAL,
        "KẾT QUẢ ĐỐI SÁNH (BẢNG 4.1)",
        "• gh/gpt-4o-mini: 100.0% Schema | 100.0% Logic (10/10) | Patch TB: 0.00.\n"
        "• ollama/gemma4:31b-cloud: 100.0% Schema | 100.0% Logic (10/10) | Patch TB: 0.00.\n"
        "• gh/gpt-4o: 100.0% Schema | 90.0% Logic (9/10) | Patch TB: 0.10."
    )

    add_callout_box(
        s18,
        Inches(6.83), Inches(5.72), Inches(5.7), Inches(1.12),
        COLOR_AMBER,
        "NHẬN XÉT PHÂN LOẠI LỖI",
        "• Phân rã lược đồ hẹp theo từng tác tử giúp Schema JSON đạt 100% ở cả 30 phiên.\n"
        "• Trong đợt đo 30 phiên có tích hợp Henssge ngay bước đầu, lỗi thực tế duy nhất phát sinh rơi vào nhóm SCHEMA_ERROR ở Lượt 5 của gh/gpt-4o."
    )

    add_notes(s18, """Kết quả 30 phiên thực nghiệm cho thấy cả 3 mô hình đều đạt 100% hợp lệ cú pháp Schema nhờ lược đồ Pydantic v2 hẹp theo từng tác tử và tiền xử lý chuỗi JSON.
Về tính logic: gh/gpt-4o-mini và mô hình trọng số mở ollama/gemma4:31b-cloud đều đạt 100% (10/10 lượt). Riêng gh/gpt-4o đạt 90% (9/10 lượt) vì ở Lượt 5 mô hình này sinh lỗi tham chiếu thực thể hỏng và đã bị bộ kiểm định phát hiện, chặn lọc kịp thời.""")

    # ==========================================
    # SLIDE 19: BENCHMARK RESULTS - LATENCY & PIPELINE BREAKDOWN
    # ==========================================
    s19 = prs.slides.add_slide(blank_layout)
    add_bg(s19)
    add_hdr(
        s19,
        "CHƯƠNG 4: THỰC NGHIỆM & ĐÁNH GIÁ",
        "Kết Quả 2: Phân Bố Độ Trễ P50/P95 & Thời Gian Từng Tác Tử",
        "Số liệu đo đạc thực tế trên 30 phiên benchmark và 6 hồ sơ lưu trong thư mục cases/ (Bảng 4.2)"
    )
    add_ftr(s19, 19)

    fig_lat = os.path.join(figures_dir, "chart_latency.png")
    if os.path.exists(fig_lat):
        s19.shapes.add_picture(fig_lat, Inches(0.8), Inches(1.78), Inches(5.7), Inches(4.9))

    add_card_box(s19, Inches(6.83), Inches(1.78), Inches(5.7), Inches(4.95))
    tb_eff = s19.shapes.add_textbox(Inches(7.03), Inches(1.94), Inches(5.3), Inches(4.65))
    tf_eff = tb_eff.text_frame
    tf_eff.word_wrap = True

    pef0 = tf_eff.paragraphs[0]
    pef0.text = "ĐỘ TRỄ TOÀN TRÌNH & PHÂN RÃ GIAI ĐOẠN"
    pef0.font.name = FONT_HEADING
    pef0.font.size = Pt(12.5)
    pef0.font.bold = True
    pef0.font.color.rgb = COLOR_NAVY

    pef_lines = [
        ("1. Phân vị P50 & P95 trên 30 phiên (Bảng 4.1):",
         "• ollama/gemma4:31b-cloud: P50 = 10.73s | P95 = 19.92s (nhanh nhất).\n"
         "• gh/gpt-4o-mini: P50 = 10.88s | P95 = 12.84s (dao động hẹp 10.21s–12.84s).\n"
         "• gh/gpt-4o: P50 = 19.53s | P95 = 27.12s."),
        ("2. Phân rã từng tác tử (Hồ sơ mẫu CASE-7BBAE9 / TB 6 hồ sơ):",
         "• OutlineAgent & Henssge: 3.27s (TB 3.04s, ~850 tokens)\n"
         "• CharacterAgent: 2.63s (TB 4.34s, ~1,100 tokens)\n"
         "• ClueAgent: 2.57s (TB 3.17s, ~950 tokens)\n"
         "• DeductionAgent: 1.56s (TB 2.75s, ~450 tokens)\n"
         "• Kiểm định Ký hiệu (validator.py): < 0.005s (< 5ms, 0 tokens)."),
    ]
    for h_txt, b_txt in pef_lines:
        ph = tf_eff.add_paragraph()
        ph.text = h_txt
        ph.font.name = FONT_HEADING
        ph.font.size = Pt(11)
        ph.font.bold = True
        ph.font.color.rgb = COLOR_TEAL if "Phân rã" in h_txt else COLOR_RED
        ph.space_before = Pt(8)

        pb = tf_eff.add_paragraph()
        pb.text = b_txt
        pb.font.name = FONT_BODY
        pb.font.size = Pt(10)
        pb.font.color.rgb = COLOR_DARK
        pb.space_before = Pt(3)

    add_notes(s19, """Về độ trễ đo được trong 30 phiên thực nghiệm: ollama/gemma4:31b-cloud đạt trung vị P50 nhanh nhất là 10.73 giây; gh/gpt-4o-mini đạt P50 10.88 giây với độ ổn định cao (P95 chỉ 12.84 giây); còn gh/gpt-4o có P50 là 19.53 giây.
Phân rã chi tiết trên hồ sơ CASE-7BBAE9 cho thấy 4 tác tử LLM chiếm tổng cộng 10.03 giây, trong khi toàn bộ tầng kiểm định ký hiệu (giải Henssge và kiểm tra đồ thị) thực thi dưới 5 mili-giây và tiêu tốn 0 token.""")

    # ==========================================
    # SLIDE 20: REAL FAILURE CASE ANALYSIS (TRIAL 5 gh/gpt-4o)
    # ==========================================
    s20 = prs.slides.add_slide(blank_layout)
    add_bg(s20)
    add_hdr(
        s20,
        "CHƯƠNG 4: THỰC NGHIỆM & ĐÁNH GIÁ",
        "Phân Tích Tình Huống Lỗi Thực Tế Tại Lượt 5 Của gh/gpt-4o",
        "Bằng chứng thực nghiệm khẳng định vai trò cổng chặn hậu kiểm của Bộ kiểm định ký hiệu"
    )
    add_ftr(s20, 20)

    add_card_box(s20, Inches(0.8), Inches(1.78), Inches(5.7), Inches(4.95))
    tb_cs1 = s20.shapes.add_textbox(Inches(1.0), Inches(1.94), Inches(5.3), Inches(4.65))
    tf_cs1 = tb_cs1.text_frame
    tf_cs1.word_wrap = True
    pcs1_0 = tf_cs1.paragraphs[0]
    pcs1_0.text = "HIỆN TƯỢNG VI PHẠM GHI NHẬN TRONG benchmark_runs"
    pcs1_0.font.name = FONT_HEADING
    pcs1_0.font.size = Pt(12)
    pcs1_0.font.bold = True
    pcs1_0.font.color.rgb = COLOR_RED

    pcs1_b = (
        "• Tựa đề hồ sơ: \"Cái Chết Bí Ẩn Trong Biệt Thự Blackwood\"\n"
        "• Thời gian thực thi: 27.12 giây | patch_retries = 1\n"
        "• Cấu trúc JSON Pydantic v2 và cửa sổ Henssge (21:40) đều hợp lệ.\n\n"
        "• Tuy nhiên, validate_case_diagnostics phát hiện lỗi tham chiếu tại ClueAgent:\n"
        "  [VALIDATION FAILURE]\n"
        "  Violation Type: schema_error\n"
        "  Component: clue\n"
        "  [CLUE:schema_error] Evidence 'EV-03' links to\n"
        "  non-existent suspect 'UNKNOWN'."
    )
    pcs1_p = tf_cs1.add_paragraph()
    pcs1_p.text = pcs1_b
    pcs1_p.font.name = FONT_BODY
    pcs1_p.font.size = Pt(10.5)
    pcs1_p.font.color.rgb = COLOR_DARK
    pcs1_p.space_before = Pt(8)

    add_card_box(s20, Inches(6.83), Inches(1.78), Inches(5.7), Inches(4.95))
    tb_cs2 = s20.shapes.add_textbox(Inches(7.03), Inches(1.94), Inches(5.3), Inches(4.65))
    tf_cs2 = tb_cs2.text_frame
    tf_cs2.word_wrap = True
    pcs2_0 = tf_cs2.paragraphs[0]
    pcs2_0.text = "NGUYÊN NHÂN GỐC RỄ & Ý NGHĨA KIỂM CHỨNG"
    pcs2_0.font.name = FONT_HEADING
    pcs2_0.font.size = Pt(12)
    pcs2_0.font.bold = True
    pcs2_0.font.color.rgb = COLOR_TEAL

    pcs2_b = (
        "1. Nguyên nhân: Dù CharacterAgent đã tạo đúng 3 mã SUSP-01..03, ClueAgent trên gh/gpt-4o vẫn tự điền chuỗi \"UNKNOWN\" vào linked_suspect_id thay vì None hoặc mã hợp lệ.\n\n"
        "2. Nếu thiếu kiểm định: Chuỗi \"UNKNOWN\" sẽ truyền xuống CorkboardManager.cs làm đứt liên kết thẻ nghi phạm và dây chỉ đỏ.\n\n"
        "3. Tác dụng của cổng lọc: Hệ thống đánh dấu component=\"clue\", gọi ClueAgent.repair_clues(), và vì prompt sửa hiện tại ưu tiên bổ sung manh mối ngoại phạm nên vẫn giữ trạng thái logic_valid=False, ngăn chặn dữ liệu hỏng tới tay người chơi."
    )
    pcs2_p = tf_cs2.add_paragraph()
    pcs2_p.text = pcs2_b
    pcs2_p.font.name = FONT_BODY
    pcs2_p.font.size = Pt(10.5)
    pcs2_p.font.color.rgb = COLOR_DARK
    pcs2_p.space_before = Pt(8)

    add_notes(s20, """Slide này phân tích sâu ca lỗi thật ở Lượt chạy số 5 của gh/gpt-4o. Dù là mô hình thương mại cỡ lớn và nhận đầy đủ cấu trúc từ bước trước, ClueAgent vẫn sinh vật chứng EV-03 tham chiếu tới nghi phạm "UNKNOWN" không tồn tại. Bộ kiểm định validate_case_diagnostics đã bắt chính xác mã schema_error và cô lập hồ sơ này trước khi nó làm lỗi hiển thị trên bảng ghim Unity.""")

    # ==========================================
    # SLIDE 21: RESEARCH QUESTIONS SUMMARY
    # ==========================================
    s21 = prs.slides.add_slide(blank_layout)
    add_bg(s21)
    add_hdr(
        s21,
        "CHƯƠNG 5: KẾT LUẬN",
        "Tổng Kết Đối Chiếu Theo Ba Câu Hỏi Nghiên Cứu (RQ1–RQ3)",
        "Nghiệm thu kết quả thực nghiệm đối chiếu với mục tiêu đặt ra ở Chương 1"
    )
    add_ftr(s21, 21)

    add_three_column_cards(s21, [
        ("Nghiệm thu RQ1", "Kiến trúc Đa tác tử", COLOR_NAVY,
         "• Cài đặt hoàn chỉnh chuỗi 4 tác tử tuần tự (OutlineAgent, CharacterAgent, ClueAgent, DeductionAgent) trên BaseAgent.\n"
         "• Tách chân lý nền tảng (GroundTruth) khỏi khâu trình bày và hỗ trợ Smart Per-Agent Fallback.\n"
         "• Đạt 100.0% tỷ lệ hợp lệ cú pháp Schema trên toàn bộ 30 phiên thử nghiệm.",
         "KIỂM CHỨNG THỰC TẾ:",
         "Hoạt động ổn định qua 6 hồ sơ thực tế lưu trong cases/ và trên Unity Client (CASE-2026-001, CASE-7BBAE9)."),
        ("Nghiệm thu RQ2", "Kiểm định Ký hiệu", COLOR_TEAL,
         "• Tích hợp phương trình làm lạnh hai hàm mũ Henssge giải bằng phương pháp chia đôi (tốc độ < 1 ms) khóa cứng TOD.\n"
         "• Mô hình hóa đồ thị hai phía kiểm soát 7 mã vi phạm ViolationType.\n"
         "• Chấm điểm kết án tất định trong RAM (< 0.1 ms, 0 token).",
         "KẾT QUẢ ĐẠT ĐƯỢC:",
         "Nâng tỷ lệ hợp lệ logic lên 100.0% ở gh/gpt-4o-mini và gemma4:31b-cloud, chặn lọc lỗi ở Lượt 5 của gh/gpt-4o (90.0%)."),
        ("Nghiệm thu RQ3", "Sửa lỗi Cục bộ O(1)", COLOR_RED,
         "• Định tuyến phản hồi chẩn đoán theo trường component tới đúng tác tử vi phạm.\n"
         "• Ngữ cảnh sửa lỗi thu hẹp còn ~300–500 tokens (O(1)) so với ~2,500–3,500 tokens khi tái sinh toàn pipeline O(N).",
         "HIỆU NĂNG TOÀN TRÌNH:",
         "P50 giữ ở mức 10.73s (gemma4:31b-cloud) và 10.88s (gpt-4o-mini), đáp ứng trải nghiệm trò chơi tương tác."),
    ])

    add_notes(s21, """Tổng kết đối chiếu với 3 câu hỏi nghiên cứu ban đầu: RQ1 đã giải quyết thông qua phân rã 4 tác tử và đạt 100% JSON Schema; RQ2 được giải quyết qua bộ giải chia đôi Henssge và đồ thị hai phía giúp đạt 90 đến 100% logic hợp lệ và chặn lỗi tham chiếu; RQ3 được hiện thực qua cơ chế sửa lỗi cục bộ O(1) giúp giữ độ trễ trung vị P50 ở mức khoảng 10.7 đến 10.9 giây.""")

    # ==========================================
    # SLIDE 22: DEFENSE Q&A / CHALLENGES
    # ==========================================
    s22 = prs.slides.add_slide(blank_layout)
    add_bg(s22)
    add_hdr(
        s22,
        "CHƯƠNG 5: KẾT LUẬN",
        "Giải Trình Phản Biện Các Thách Thức Kiến Trúc & Vận Hành",
        "Phản biện khoa học dựa trên dẫn chứng thực nghiệm và thiết kế mã nguồn"
    )
    add_ftr(s22, 22)

    add_three_column_cards(s22, [
        ("1. Tại sao không chỉ dùng CoT?", "Thay cho Bộ kiểm định", COLOR_NAVY,
         "Câu hỏi: Vì sao không dùng kỹ thuật gợi nhắc nâng cao như Chain-of-Thought (CoT) để ép LLM tuân thủ logic thay cho bộ kiểm định tất định?",
         "GIẢI TRÌNH:",
         "CoT chỉ tác động ở tầng xác suất ngữ cảnh. Bằng chứng là Lượt 5 của gh/gpt-4o vẫn gán sai \"UNKNOWN\" cho EV-03 dù nhận đủ lược đồ. Bộ kiểm định ngoài là lớp bảo vệ bắt buộc."),
        ("2. Giả định T_ambient ổn định?", "Mô hình Henssge", COLOR_AMBER,
         "Câu hỏi: Việc giả định nhiệt độ môi trường không đổi trong phương trình Henssge có làm giảm tính thực tế không?",
         "GIẢI TRÌNH:",
         "Với hiện trường phòng kín dưới 24 giờ, nhiệt độ ổn định là giả định chuẩn của biểu đồ Henssge (1988), kèm dung sai ±1.5 giờ hấp thụ dao động nhỏ và giữ dữ kiện minh bạch cho người chơi."),
        ("3. Ứng phó khi Cloud hết hạn mức?", "Fallback Đa mô hình", COLOR_TEAL,
         "Câu hỏi: Khi dịch vụ LLM đám mây gặp giới hạn quota (HTTP 402/503) khi trình diễn, hệ thống xử lý ra sao?",
         "GIẢI TRÌNH:",
         "Tầng BaseAgent tích hợp Smart Fallback theo từng tác tử (9Router Gemini/GPT -> Ollama nội bộ RTX 3050) kèm báo cáo agent_models, chứng minh độ bền của bộ kiểm định ngay cả với mô hình nhỏ."),
    ])

    add_notes(s22, """Em xin giải trình trước ba câu hỏi kỹ thuật trọng tâm:
Thứ nhất, lý do phải có bộ kiểm định tất định ngoài CoT được chứng minh ngay bởi ca lỗi Lượt 5 của gh/gpt-4o.
Thứ hai, giả định nhiệt độ ổn định kèm dung sai ±1.5 giờ là chuẩn mực của Henssge cho hiện trường phòng kín dưới 24h và bảo đảm tính công bằng dữ kiện cho người chơi.
Thứ ba, khi một dịch vụ đám mây gặp sự cố quota, cơ chế Smart Per-Agent Fallback tự động chuyển hướng sang mô hình dự phòng hoặc mô hình nội bộ trên RTX 3050 mà vẫn bảo toàn tính hợp lệ qua bộ kiểm định.""")

    # ==========================================
    # SLIDE 23: LIMITATIONS, FUTURE WORK & THANK YOU
    # ==========================================
    s23 = prs.slides.add_slide(blank_layout)
    add_bg(s23)
    add_hdr(
        s23,
        "CHƯƠNG 5: KẾT LUẬN",
        "Hạn Chế Kỹ Thuật, Hướng Phát Triển & Lời Cảm Ơn",
        "Đánh giá khách quan giới hạn hiện tại và lộ trình mở rộng hệ thống"
    )
    add_ftr(s23, 23)

    add_card_box(s23, Inches(0.8), Inches(1.78), Inches(5.7), Inches(3.7))
    tb_c1 = s23.shapes.add_textbox(Inches(1.0), Inches(1.92), Inches(5.3), Inches(3.4))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    p_c1_t = tf_c1.paragraphs[0]
    p_c1_t.text = "HẠN CHẾ KỸ THUẬT HIỆN TẠI (MỤC 5.3)"
    p_c1_t.font.name = FONT_HEADING
    p_c1_t.font.size = Pt(12.5)
    p_c1_t.font.bold = True
    p_c1_t.font.color.rgb = COLOR_RED

    p_c1 = tf_c1.add_paragraph()
    p_c1.text = (
        "• Chưa mở thẩm vấn hội thoại tự do với NPC để tránh bẻ khóa ngữ cảnh.\n\n"
        "• Lưu trữ SQLite đơn nút, chưa phân tán đa vùng khi mở rộng quy mô lớn.\n\n"
        "• Không gian kịch bản tập trung ở phòng kín (3 nghi phạm, 3–4 vật chứng).\n\n"
        "• Hàm repair_clues chưa chuyên biệt hóa sửa trực tiếp lỗi SCHEMA_ERROR dạng linked_suspect_id = \"UNKNOWN\"."
    )
    p_c1.font.name = FONT_BODY
    p_c1.font.size = Pt(10.5)
    p_c1.font.color.rgb = COLOR_DARK
    p_c1.space_before = Pt(8)

    add_card_box(s23, Inches(6.83), Inches(1.78), Inches(5.7), Inches(3.7))
    tb_c2 = s23.shapes.add_textbox(Inches(7.03), Inches(1.92), Inches(5.3), Inches(3.4))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    p_c2_t = tf_c2.paragraphs[0]
    p_c2_t.text = "HƯỚNG NGHIÊN CỨU TIẾP THEO (MỤC 5.4)"
    p_c2_t.font.name = FONT_HEADING
    p_c2_t.font.size = Pt(12.5)
    p_c2_t.font.bold = True
    p_c2_t.font.color.rgb = COLOR_TEAL

    p_c2 = tf_c2.add_paragraph()
    p_c2.text = (
        "• Tinh chỉnh mô hình ngôn ngữ nhỏ (Llama-3 8B / Qwen 2.5 7B) bằng kỹ thuật LoRA trên tập hồ sơ đã kiểm định để đóng gói chạy ngoại tuyến.\n\n"
        "• Bổ sung sửa tất định cho lỗi SCHEMA_ERROR và tích hợp cơ sở dữ liệu đồ thị Neo4j (Cypher) cho vụ án nhiều hiện trường.\n\n"
        "• Phát triển mô-đun thẩm vấn NPC kiểm soát bằng Máy trạng thái hữu hạn (FSM) đối chiếu với GroundTruth."
    )
    p_c2.font.name = FONT_BODY
    p_c2.font.size = Pt(10.5)
    p_c2.font.color.rgb = COLOR_DARK
    p_c2.space_before = Pt(8)

    banner = s23.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.68), Inches(11.733), Inches(1.15))
    banner.adjustments[0] = 0.04
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(238, 242, 255)
    banner.line.color.rgb = COLOR_NAVY
    banner.line.width = Pt(1.5)

    tb_th = s23.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.333), Inches(0.95))
    p_th1 = tb_th.text_frame.paragraphs[0]
    p_th1.text = "XIN TRÂN TRỌNG CẢM ƠN QUÝ THẦY CÔ TRONG HỘI ĐỒNG VÀ CÁC BẠN ĐÃ LẮNG NGHE!"
    p_th1.font.name = FONT_HEADING
    p_th1.font.size = Pt(15)
    p_th1.font.bold = True
    p_th1.font.color.rgb = COLOR_NAVY

    p_th2 = tb_th.text_frame.add_paragraph()
    p_th2.text = "HỎI ĐÁP & BẢO VỆ TRƯỚC HỘI ĐỒNG  •  EM XIN PHÉP LẮNG NGHE Ý KIẾN ĐÓNG GÓP VÀ TRẢ LỜI PHẢN BIỆN"
    p_th2.font.name = FONT_BODY
    p_th2.font.size = Pt(11.5)
    p_th2.font.bold = True
    p_th2.font.color.rgb = COLOR_RED
    p_th2.space_before = Pt(5)

    add_notes(s23, """Trên tinh thần khách quan, em cũng tổng kết 4 hạn chế hiện tại của hệ thống và đề xuất 3 hướng mở rộng: tinh chỉnh SLM bằng LoRA, bổ sung sửa tất định lỗi tham chiếu kết hợp Neo4j, và xây dựng hội thoại kiểm soát bằng FSM.
Em xin chân thành cảm ơn TS. Nguyễn Văn Tánh đã tận tình hướng dẫn và cảm ơn Quý Thầy Cô trong Hội đồng đã lắng nghe. Em xin sẵn sàng tiếp thu góp ý và trả lời các câu hỏi chất vấn.""")

    out_pptx = os.path.join(root_dir, "BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx")
    prs.save(out_pptx)
    print(f"Presentation saved to: {out_pptx}")


if __name__ == "__main__":
    generate_comprehensive_presentation()
