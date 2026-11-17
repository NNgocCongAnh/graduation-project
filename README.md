# ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC — UNSOLVED CASE FILES AI

**Đề tài:** *Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán*  
*(Hướng tiếp cận Neuro-Symbolic kết hợp Hệ đa tác tử và Bộ kiểm định hình thức)*

- **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh — MSSV: `22010201` — Lớp: `K16-KHMT`
- **Cán bộ hướng dẫn:** TS. Nguyễn Văn Tánh — Khoa Khoa học máy tính, Trường Đại học Phenikaa

---

## 📦 Tài liệu & Sản phẩm Bàn giao Chính thức (Thư mục Gốc)

| Sản phẩm | Tệp / Liên kết | Mô tả |
|---|---|---|
| **Báo cáo Đồ án (PDF)** | [`BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.pdf`](./BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.pdf) | Bản biên dịch hoàn chỉnh từ LaTeX (5 chương + phụ lục tham khảo) |
| **Báo cáo Đồ án (Word)** | [`BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx`](./BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx) | Bản tài liệu Microsoft Word đồng bộ đầy đủ bảng biểu và hình vẽ |
| **Slide Bảo vệ (PowerPoint)** | [`BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx`](./BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx) | Bộ 23 slide thuyết trình kèm ghi chú trình bày (Speaker Notes) |
| **Notebook Thực nghiệm** | [`benchmark_evaluation.ipynb`](./benchmark_evaluation.ipynb) | Tổng hợp 30 phiên benchmark, kiểm chứng Henssge/đồ thị & Smart Fallback |
| **Bản cài đặt Game (.zip)** | [GitHub Releases (`v1.0.0`)](https://github.com/NNgocCongAnh/graduation-project/releases) | Gói trò chơi `UnsolvedCaseFiles_v1.0.0.zip` (Unity 6 URP 2D + DLL phụ thuộc) |

---

## 🏗️ Kiến trúc Hệ thống

Hệ thống vận hành theo mô hình **Dịch vụ Web phân tán** kết hợp **Lõi lai Neuro-Symbolic** và **Client đa nền tảng**:

```text
[ Unity 6 URP 2D Client / V0 React Web Prototype ]
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

## 📁 Cấu trúc Thư mục Chính

```text
├── BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.pdf
├── BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx
├── BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx
├── benchmark_evaluation.ipynb
├── detective-backend/          # Backend FastAPI, 4 Agents, Henssge Validator, SQLite WAL, Unit Tests
│   ├── agents.py               # OutlineAgent, CharacterAgent, ClueAgent, DeductionAgent + Per-Agent Fallback
│   ├── llm_service.py          # CaseGeneratorService & Localized Patch Repair O(1)
│   ├── validator.py            # Henssge Bisection Solver, Bipartite Checks & Deterministic Scoring
│   ├── database.py             # SQLAlchemy 2.0 WAL (cases, deduction_logs, benchmark_runs)
│   ├── security.py             # HMAC-SHA-256 & Anti-Replay Middleware (60s window)
│   ├── benchmark_runner.py     # Script chạy benchmark đa mô hình & log fallback từng Agent
│   └── main.py                 # FastAPI Endpoints & WebSocket Co-op Manager
├── Unity/My project/           # Client Unity 6 (6000.5.8f1) URP 2D (Corkboard, Henssge Modal, LAN Co-op)
├── thesis_latex/               # Mã nguồn LaTeX báo cáo đồ án & script generate_thesis_charts.py
├── V0/                         # Nguyên mẫu giao diện Web React ban đầu (V0/frontend/)
├── docker-compose.yml          # Cấu hình chạy container Docker
└── README.md
```

---

## 🚀 Hướng dẫn Khởi chạy Nhanh

### 1. Chạy Backend (`detective-backend`)
```bash
cd detective-backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
* Swagger OpenAPI: `http://localhost:8000/docs`
* Cấu hình mô hình mặc định qua `detective-backend/.env` (`LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL`).

### 2. Chạy Benchmark & Kiểm thử (Pytest / Jupyter)
```bash
# Kiểm thử đơn vị các mô-đun cốt lõi
python -m pytest detective-backend/test_henssge.py detective-backend/test_validator.py detective-backend/test_database.py detective-backend/test_security.py

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
2. Lần đầu, cho phép Python qua Windows Firewall ở mạng **Private**: TCP `8000` (game/WebSocket) và UDP `47777` (tự động tìm phòng LAN).
3. Mở game, nhấn **L** → **TỰ LÀM MÁY CHỦ**.

**Máy khách (tối đa 2 máy):** Mở game, nhấn **L** → **TÌM MÁY CHỦ** (hoặc nhập IP máy chủ) → nhập cùng **Mã phòng** → **KẾT NỐI**.

| Phím | Chức năng |
|---|---|
| Giữ **V** | Thoại trực tiếp (PCM 16 kHz qua WebSocket) |
| **T** | Trò chuyện văn bản |
| **L** | Mở phòng chơi LAN |
| **Esc** | Đóng hộp thoại |
