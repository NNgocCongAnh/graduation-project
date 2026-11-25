# ĐỒ ÁN TỐT NGHIỆP — UNSOLVED CASE FILES AI

**Đề tài:** *Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán*

- **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh — MSSV `22010201` — Lớp `K16-KHMT`
- **Giảng viên hướng dẫn:** TS. Nguyễn Văn Tánh — Trường Công nghệ thông tin, Đại học Phenikaa

---

## Cấu trúc kho mã nguồn

| Thư mục / tệp | Nội dung |
| :--- | :--- |
| [`detective-backend/`](./detective-backend) | Máy chủ FastAPI: chuỗi 4 tác tử LLM (`agents.py`), bộ kiểm định ký hiệu và mô hình Henssge (`validator.py`), đồ thị hai phía (`case_graph.py`), hoán vị định danh (`id_shuffle.py`), bảo mật (`security.py`), SQLite (`database.py`), phòng chơi LAN (`rooms.py`) |
| [`detective-backend/tests/`](./detective-backend/tests) | 89 kiểm thử đơn vị và tích hợp (pytest) |
| [`benchmarks/scripts/`](./benchmarks/scripts) | Module đánh giá thực nghiệm độc lập (`benchmark_runner.py`, `e2e_baseline.py`, `run_e2e_baseline.py`, `fault_injection_runner.py`, `solver_agent.py`, `verify_results.py`) |
| [`benchmarks/results/`](./benchmarks/results) | Thư mục duy nhất lưu toàn bộ kết quả JSON thô của các thực nghiệm |
| [`benchmark_evaluation.ipynb`](./benchmark_evaluation.ipynb) | Notebook kiểm chứng bảng số liệu và biểu đồ đối sánh thực nghiệm |
| [`Unity/My project/`](./Unity/My%20project) | Client trò chơi Unity 6 URP 2D (Desktop và WebGL) |
| [`docker-compose.yml`](./docker-compose.yml) | Khởi chạy backend bằng Docker |

## Kiến trúc

```text
[ Unity 6 URP 2D Client (Desktop / WebGL) ]
        │  REST (HTTP/JSON, chữ ký HMAC-SHA-256) + WebSocket phòng chơi LAN
        ▼
[ FastAPI + Pydantic v2 + SQLite ]
        ├── OutlineAgent    → cốt truyện, nạn nhân, chân lý gốc; cửa sổ TOD tính bằng Henssge (chia đôi)
        ├── CharacterAgent  → nghi phạm, lời khai ngoại phạm
        ├── ClueAgent       → vật chứng then chốt và nghi binh
        ├── DeductionAgent  → chuỗi suy luận
        └── validate_case_diagnostics → kiểm định cấu trúc; vi phạm được định tuyến về đúng tác tử để vá cục bộ
        ▼
[ LLM qua gateway tương thích OpenAI (GitHub Models / Ollama cục bộ) ]
```

Client chỉ nhận `ClientCaseDossier` (không có chân lý gốc và cờ đáp án); việc chấm điểm kết án thực hiện trên máy chủ (`POST /api/case/verify`).

## Cài đặt và chạy

Biến môi trường bắt buộc (đặt trong `detective-backend/.env`, xem `.env.example`):

| Biến | Ý nghĩa |
| :--- | :--- |
| `GAME_CLIENT_SECRET` | Khóa ký HMAC của client; máy chủ từ chối khởi động nếu thiếu |
| `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL` | Cấu hình gateway LLM; không có giá trị mặc định cho khóa |
| `INTERNAL_API_TOKEN` | (Tùy chọn) mở các endpoint nội bộ chứa đáp án `/api/case/{id}/internal`, `/graph`; nếu không đặt, các endpoint này bị tắt |
| `CORS_ORIGINS` | (Tùy chọn) danh sách origin được phép, phân tách bằng dấu phẩy |

```bash
# Docker
docker compose up --build -d          # API: http://localhost:8000/docs

# Thủ công
cd detective-backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Trên Windows có thể dùng `CHAY_GAME_TRON_GOI.bat` để chạy backend kèm bản build game.

## Kiểm thử

```bash
cd detective-backend
python -m pytest -q
```

Kết quả tại commit hiện tại: 89/89 kiểm thử đạt.

## Tái lập thực nghiệm (Chương 4)

```bash
# chạy từ thư mục gốc của kho mã nguồn
python benchmarks/scripts/benchmark_runner.py --mode benchmark --models gh/gpt-4o-mini --trials-per-theme 10 --no-fallback
python benchmarks/scripts/benchmark_runner.py --mode ablation --ablation-trials 1
python benchmarks/scripts/run_e2e_baseline.py --trials-per-theme 3
python benchmarks/scripts/fault_injection_runner.py
python benchmarks/scripts/solver_agent.py
python benchmarks/scripts/verify_results.py
```

| Thực nghiệm | Tệp kết quả (`benchmarks/results/`) | Cỡ mẫu | Kết quả chính |
| :--- | :--- | :---: | :--- |
| Benchmark `gh/gpt-4o-mini` (bản sạch không neo) | `benchmark_gpt-4o-mini.json` | 30 (3 chủ đề) | 30/30 vượt kiểm định (Wilson 95%: [88,6%; 100%]); P50 22,34 s, P95 28,05 s |
| Benchmark `gh/gpt-4o` (sau `id_shuffle`, tạm dừng tại 25 do 429) | `benchmark_gpt-4o.json` | 24 (3 chủ đề) | 24/24 vượt kiểm định (Wilson 95%: [86,2%; 100%]); P50 45,51 s, P95 54,78 s |
| Khảo sát cục bộ `gemma4:e4b-it-qat` (hệ lai) | `benchmark_gemma4_hybrid.json` | 23 | 23/23; ~20 phút/hồ sơ trên RTX 3050 Laptop 4 GB (CharacterAgent và ClueAgent fallback mây ở 23/23 lượt) |
| Khảo sát thuần ngoại tuyến `gemma4:e4b-it-qat` (`--no-fallback`) | `benchmark_gemma4.json` | 3 | 0/3 LLM tự sinh đạt (CharacterAgent lỗi JSON ở Q4_0; P50 540,39 s) |
| Nghiên cứu loại trừ (4 cấu hình) | `ablation_results.json` | 3/cấu hình | Prompt nguyên khối 0/3 hợp lệ; các cấu hình đa tác tử 3/3 |
| Đối chứng một lần gọi `E2E-plan` (Agents' Room, ICLR 2025) | `e2e_plan_baseline_results.json` | 9 | Cùng chỉ dẫn 4 tác tử + lược đồ JSON trong 1 lần gọi: hợp lệ cú pháp 5/9, vượt kiểm định 1/9 |
| Tiêm lỗi (vá cục bộ) | `fault_injection_results.json` | 80 | Vá thành công 63,8%; 4.227,6 token/lượt vá, P50 7,21 s |
| Tác tử phá án độc lập (bộ chuẩn `gh/gpt-4o-mini`) | `solver_benchmark_baseline.json` | 20 | Xác định đúng thủ phạm 19/20 |
| Tác tử phá án độc lập (bộ đề mới không neo, `gemini-3-flash-preview`) | `solver_benchmark.json` | 3 | 3/3 đạt 100/100 điểm (tạm dừng ở ca 4 do giới hạn 20 RPD Free Tier) |

## Hạn chế đã biết

- Bộ kiểm định chỉ kiểm tra bất biến cấu trúc (một thủ phạm, toàn vẹn tham chiếu, vật chứng then chốt, cửa sổ TOD), chưa kiểm định ngữ nghĩa lời khai.
- Độ trễ P50 (23,23 s) và chi phí vá (4.227,6 token) chưa đạt ngưỡng thiết kế (≤ 20 s, ≤ 500 token).
- LLM thiên lệch khi chọn thủ phạm ở đầu ra thô (`SUSP-02` ở 28/30 lượt `mini` và 5/6 lượt `gpt-4o` trước hoán vị). Khi tích hợp bước hoán vị kép mã nghi phạm và vật chứng (`id_shuffle.py`), 24 lượt cuối của `gpt-4o` phân bố đều (`9/8/7`) và người chơi gặp thủ phạm/hung khí phân bố đồng đều; đây là phép đổi tên, nội dung vụ án chưa đa dạng hơn.
- Chưa có thử nghiệm người chơi có quy trình; WebSocket phòng chơi chưa có xác thực phiên (chỉ dùng trong LAN tin cậy).
