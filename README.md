# ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC — UNSOLVED CASE FILES AI

**Đề tài:** *Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán*  
*(Hướng tiếp cận Neuro-Symbolic kết hợp Hệ đa tác tử và Bộ kiểm định hình thức)*

- **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh — MSSV: `22010201` — Lớp: `K16-KHMT`
- **Cán bộ hướng dẫn:** TS. Nguyễn Văn Tánh — Khoa Khoa học máy tính, Trường Đại học Phenikaa

---

## 📊 Tiến độ Thực hiện & Danh mục Kết quả Bàn giao

Dự án đã hoàn thành **100% các hạng mục giai đoạn nghiên cứu, cài đặt và kiểm thử định lượng**, sẵn sàng cho buổi báo cáo tiến độ và hoàn thiện bản thảo:

| Hạng mục Yêu cầu | Tệp / Thư mục trên Repo | Trạng thái | Ghi chú |
|---|---|---|---|
| **Bản thảo Báo cáo (Word)** | [`BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx`](./BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx) | ✅ Hoàn tất (100%) | Bản mềm `.docx` đầy đủ 5 chương, bảng biểu & hình vẽ để giảng viên nhận xét |
| **Bản mềm Báo cáo (PDF)** | [`BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.pdf`](./BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.pdf) | ✅ Hoàn tất (63 trang) | Bản biên dịch trực tiếp từ mã nguồn LaTeX (`thesis_latex/`) |
| **Mã nguồn LaTeX Luận văn** | [`thesis_latex/`](./thesis_latex) | ✅ Hoàn tất (100%) | Gồm `main.tex`, 5 chương `chapters/`, `references.bib` và thư mục ảnh `figures/` |
| **Slide Báo cáo Tiến độ** | [`BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx`](./BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx) | ✅ Hoàn tất (23 slides) | Trình bày kiến trúc, giải thuật và kết quả thực nghiệm (kèm Speaker Notes) |
| **Kết quả Thực nghiệm** | [`benchmark_evaluation.ipynb`](./benchmark_evaluation.ipynb) | ✅ Hoàn tất (100%) | Tổng hợp 30 phiên đối sánh 3 LLM, kiểm chứng Henssge & Smart Per-Agent Fallback |
| **Mã nguồn Backend AI** | [`detective-backend/`](./detective-backend) | ✅ Hoàn tất (100%) | FastAPI (ASGI), 4 Agents + Fallback, Henssge Bisection, Đồ thị hai phía, SQLite WAL |
| **Mã nguồn & Tài nguyên Game** | [`Unity/My project/`](./Unity/My%20project) | ✅ Hoàn tất (100%) | Unity 6 URP 2D Client (Bảng ghim Corkboard, Pháp y Henssge, Co-op LAN 3 người) |
| **Bản đóng gói Chơi thử (.zip)** | [GitHub Releases (`v1.0.0`)](https://github.com/NNgocCongAnh/graduation-project/releases/tag/v1.0.0) | ✅ Đã phát hành | Tải `UnsolvedCaseFiles_v1.0.0.zip`, giải nén và chạy `UnsolvedCaseFiles.exe` |

---

## 🏗️ Kiến trúc Hệ thống

Hệ thống vận hành theo mô hình **Dịch vụ Web phân tán** kết hợp **Lõi lai Neuro-Symbolic** và **Client đa nền tảng**:

```text
[ Unity 6 URP 2D Client (WebGL / Desktop EXE) ]
            │  REST API (HTTP/JSON + HMAC-SHA-256) & WebSocket (/ws/rooms/{room_id})
            ▼
[ FastAPI 0.137.1 Backend (ASGI / Uvicorn) + Pydantic v2 + SQLite WAL (SQLAlchemy 2.0) ]
            │
            ├── 1. OutlineAgent   ──► Cốt truyện, Victim & GroundTruth -> Khóa TOD bằng Henssge (Bisection)
            ├── 2. CharacterAgent ──► Nghi phạm & Lời khai ngoại phạm (SUSP-01..SUSP-03)
            ├── 3. ClueAgent      ──► Vật chứng then chốt & Nghi binh (EV-01..EV-04)
            ├── 4. Bộ kiểm định   ──► validate_case_diagnostics (7 ViolationType) + Sửa lỗi cục bộ O(1)
            └── 5. DeductionAgent ──► Chuỗi suy luận đa bước (ReasoningChain)
            │
            ▼
[ 9Router Gateway (:20128) / Google Gemini & Gemma / OpenAI GPT / Local Ollama (:11434) ]
```

* **Smart Per-Agent Fallback (`agents.py`):** Khi mô hình chính gặp lỗi hạn mức hoặc gián đoạn kết nối, từng tác tử tự động chuyển mạch theo chuỗi dự phòng (`gemini/gemma-4-31b-it` → `gh/gpt-3.5-turbo-0613` → `gh/gpt-4o-mini` → `gemma4:e4b-it-qat` cục bộ) và ghi nhận lại trong `GenerationMetadata.agent_models`.

---

## 📁 Cấu trúc Kho chứa GitHub

```text
├── BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx   # Bản thảo Word nhận xét
├── BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.pdf    # Bản mềm PDF hoàn chỉnh (63 trang)
├── BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx                     # Bộ 23 slide báo cáo
├── benchmark_evaluation.ipynb                            # Notebook thực nghiệm & kiểm chứng
├── detective-backend/                                    # Backend FastAPI, 4 Agents, Validator & SQLite WAL
│   ├── agents.py                                         # Outline/Character/Clue/Deduction + Per-Agent Fallback
│   ├── llm_service.py                                    # Điều phối pipeline & Vá lỗi cục bộ O(1)
│   ├── validator.py                                      # Henssge Bisection, Đồ thị hai phía & Chấm điểm
│   ├── database.py                                       # SQLAlchemy 2.0 WAL (cases, deduction_logs, benchmark_runs)
│   ├── security.py                                       # Middleware xác thực HMAC-SHA-256 (cửa sổ 60s)
│   ├── benchmark_runner.py                               # Bộ chạy benchmark đa mô hình
│   └── main.py                                           # FastAPI Endpoints & WebSocket Co-op Manager
├── Unity/My project/                                     # Client Unity 6 (6000.5.8f1) URP 2D & Tài nguyên
├── thesis_latex/                                         # Mã nguồn LaTeX của luận văn & thư mục figures/
└── README.md
```

---

## 🚀 Hướng dẫn Khởi chạy & Thực nghiệm Nhanh

### 1. Khởi chạy Backend (`detective-backend`)
```bash
cd detective-backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
* Tài liệu OpenAPI (Swagger): `http://localhost:8000/docs`
* Cấu hình mô hình qua biến môi trường trong `.env` (`LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL`).

### 2. Chạy Đánh giá Thực nghiệm & Benchmark
```bash
# Chạy benchmark đa mô hình qua dòng lệnh
python detective-backend/benchmark_runner.py --models gemini/gemma-4-31b-it gh/gpt-4o-mini --trials 10

# Hoặc mở và chạy trực tiếp benchmark_evaluation.ipynb tại thư mục gốc
```

---

## 🕵️ Chơi Co-op trong mạng LAN (tối đa 3 người)

**Máy chủ (1 máy):**
1. Khởi chạy backend lắng nghe mạng nội bộ:
   ```bash
   cd detective-backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. Cho phép Python qua Windows Firewall ở mạng **Private**: TCP `8000` (game/WebSocket) và UDP `47777` (tự động tìm phòng LAN).
3. Mở game (`UnsolvedCaseFiles.exe`), nhấn **L** → **TỰ LÀM MÁY CHỦ**.

**Máy khách (tối đa 2 máy):** Mở game, nhấn **L** → **TÌM MÁY CHỦ** (hoặc nhập IP máy chủ) → nhập cùng **Mã phòng** → **KẾT NỐI**.

| Phím | Chức năng |
|---|---|
| Giữ **V** | Thoại trực tiếp (PCM 16 kHz qua WebSocket) |
| **T** | Trò chuyện văn bản |
| **L** | Mở phòng chơi LAN |
| **Esc** | Đóng hộp thoại |
