# BỘ MÃ NGUỒN BÁO CÁO ĐỒ ÁN TỐT NGHIỆP (LATEX)
### TRƯỜNG ĐẠI HỌC PHENIKAA - KHOA KHOA HỌC MÁY TÍNH

> **Đề tài:** Phương pháp tiếp cận Neuro-Symbolic trong việc sinh thủ tục kịch bản trinh thám có thể giải được sử dụng Hệ đa tác tử và Bộ kiểm định hình thức  
> **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh (MSSV: 22010201) - K16-KHMT  
> **Cán bộ hướng dẫn:** TS. Nguyễn Văn Tánh  
> **Quy mô luận văn:** 5 chương hoàn chỉnh, ~16,200 từ (~55 - 65 trang chuẩn A4).

---

## 1. CẤU TRÚC THƯ MỤC DỰ ÁN LATEX

```
thesis_latex/
├── main.tex                               # File master điều phối toàn bộ luận văn
├── references.bib                         # Danh mục tài liệu tham khảo chuẩn BibTeX
├── generate_thesis_charts.py              # Script sinh tự động các biểu đồ thực nghiệm
├── figures/                               # Thư mục chứa hình ảnh thực tế
│   ├── corkboard_ui.png                   # Ảnh chụp giao diện Bàn điều tra Corkboard 2.5D
│   ├── forensic_modal.png                 # Ảnh chụp Báo cáo Khám nghiệm Tử thi Henssge
│   ├── architecture_overview.png          # Sơ đồ Kiến trúc Phân tầng Hệ thống
│   ├── decoupled_flowchart.png            # Sơ đồ Luồng phân tách Tất định vs LLM
│   ├── chart_pass_rate.png                # Biểu đồ đối sánh Schema & Pass Rate 3 mô hình
│   └── chart_latency.png                  # Biểu đồ thời gian phản hồi P50 và P95
└── chapters/                              # 5 Chương nội dung học thuật chi tiết
    ├── 00_frontmatter.tex                 # Bìa, Lời cam đoan, Lời cảm ơn, Tóm tắt VN & EN, Mục lục
    ├── 01_introduction.tex                # Chương 1: Tổng quan, Bối cảnh, 3 RQs, Đóng góp
    ├── 02_theoretical_background.tex      # Chương 2: Cơ sở lý thuyết, Henssge, Đồ thị, Knox, Đối sánh
    ├── 03_system_architecture.tex         # Chương 3: Phân tích & Thiết kế, 5 ADRs (Tại sao), Pydantic, Unity
    ├── 04_implementation_and_evaluation.tex # Chương 4: Cài đặt, Benchmark 30 trials, Case study lỗi GPT-4o
    └── 05_conclusion_future_work.tex      # Chương 5: Kết luận, 3 Hạn chế, 3 Hướng phát triển
```

---

## 2. HƯỚNG DẪN XEM VÀ BIÊN DỊCH BÁO CÁO

### Cách 1: Sử dụng Visual Studio Code (Khuyên dùng)
1. Cài đặt tiện ích mở rộng **LaTeX Workshop** trên VS Code.
2. Mở thư mục `d:\Work\Đồ Án Tốt Nghiệp\thesis_latex` trên VS Code.
3. Mở file `main.tex` và nhấn tổ hợp phím `Ctrl + Alt + B` (Build LaTeX project) hoặc click vào biểu tượng kính lúp để xem PDF Preview trực tiếp song song với mã nguồn.

### Cách 2: Sử dụng Overleaf (Biên dịch trực tuyến 1 Click)
1. Nén toàn bộ thư mục `thesis_latex` thành file `.zip`.
2. Truy cập [Overleaf.com](https://www.overleaf.com) -> Chọn **New Project** -> **Upload Project**.
3. Tải file `.zip` lên và nhấn **Recompile**. Toàn bộ tài liệu 60 trang sẽ được render PDF tức thì với đầy đủ bảng biểu và hình ảnh.

### Cách 3: Biên dịch bằng Dòng lệnh (Terminal)
Nếu máy bạn đã cài MiKTeX hoặc TeX Live:
```bash
cd "d:\Work\Đồ Án Tốt Nghiệp\thesis_latex"
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
File `main.pdf` sẽ được tạo ra ngay trong thư mục.
