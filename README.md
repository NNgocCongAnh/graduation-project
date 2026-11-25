# ĐỒ ÁN TỐT NGHIỆP — UNSOLVED CASE FILES AI

**Đề tài:** *Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán*

- **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh — MSSV `22010201` — Lớp `K16-KHMT`
- **Giảng viên hướng dẫn:** TS. Nguyễn Văn Tánh — Trường Công nghệ thông tin, Đại học Phenikaa

---

## Cấu trúc kho mã nguồn

| Thư mục / tệp | Nội dung |
| :--- | :--- |
| [`detective-backend/`](./detective-backend) | Máy chủ FastAPI: chuỗi 4 tác tử LLM (`agents.py`), bộ kiểm định ký hiệu và mô hình Henssge (`validator.py`), đồ thị hai phía (`case_graph.py`), bảo mật (`security.py`), SQLite (`database.py`), phòng chơi LAN (`rooms.py`) |
| [`detective-backend/tests/`](./detective-backend/tests) | 89 kiểm thử đơn vị và tích hợp (pytest) |
| [`detective-backend/*_runner.py`, `solver_agent.py`](./detective-backend) | Script thực nghiệm: benchmark, nghiên cứu loại trừ, tiêm lỗi, tác tử phá án độc lập |
| [`benchmarks/`](./benchmarks) | Thư mục kết quả thô tổng hợp của các phiên thực nghiệm (`benchmark_*.json`, `solver_benchmark.json`, `benchmark_summary.json`) |
| [`detective-backend/*_results*.json`](./detective-backend) | Tệp kết quả thô gốc đối chiếu trực tiếp với Chương 4 báo cáo |
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
python detective-backend/benchmark_runner.py --mode benchmark --models gh/gpt-4o-mini --trials-per-theme 10 --output-benchmark detective-backend/benchmark_results_gpt4o_mini.json
python detective-backend/benchmark_runner.py --mode ablation --ablation-trials 1 --output-ablation detective-backend/ablation_results.json
python detective-backend/run_e2e_baseline.py --trials-per-theme 3
python detective-backend/fault_injection_runner.py
python detective-backend/solver_agent.py
```

| Thực nghiệm | Tệp kết quả | Cỡ mẫu | Kết quả chính |
| :--- | :--- | :---: | :--- |
| Benchmark `gh/gpt-4o-mini` | `benchmark_results_gpt4o_mini.json` | 30 (3 chủ đề) | 30/30 vượt kiểm định (Wilson 95%: [88,6%; 100%]); P50 23,23 s, P95 30,90 s |
| Benchmark `gh/gpt-4o` | `benchmark_results_gpt4o_v2.json` | 30 | 30/30; P50 46,81 s, P95 59,77 s |
| Khảo sát cục bộ `gemma4:e4b-it-qat` | `benchmark_results_gemma4_local.json` | 23 | 23/23; ~20 phút/hồ sơ trên RTX 3050 Laptop 4 GB. CharacterAgent và ClueAgent chuyển sang mô hình dự phòng trên mây ở cả 23 lượt (hệ lai, không phải chạy hoàn toàn ngoại tuyến) |
| Nghiên cứu loại trừ (4 cấu hình) | `ablation_results.json` | 3/cấu hình | Prompt nguyên khối 0/3 hợp lệ; các cấu hình đa tác tử 3/3 |
| Đối chứng một lần gọi E2E-plan (theo Agents' Room, ICLR 2025) | `e2e_plan_baseline_results.json` | 9 | Cùng chỉ dẫn 4 tác tử + lược đồ JSON: hợp lệ cú pháp 5/9, vượt kiểm định 1/9 |
| Tiêm lỗi (vá cục bộ) | `fault_injection_results.json` | 80 | Vá thành công 63,8%; 4.227,6 token/lượt vá (giảm 77,0% so với sinh lại toàn bộ) |
| Tác tử phá án độc lập | `solver_benchmark_results.json` | 20 | Xác định đúng thủ phạm 19/20 |

## Hạn chế đã biết

- Bộ kiểm định chỉ kiểm tra bất biến cấu trúc (một thủ phạm, toàn vẹn tham chiếu, vật chứng then chốt, cửa sổ TOD), chưa kiểm định ngữ nghĩa lời khai.
- Độ trễ P50 (23,23 s) và chi phí vá (4.227,6 token) chưa đạt ngưỡng thiết kế (≤ 20 s, ≤ 500 token).
- LLM thiên lệch khi chọn thủ phạm ở đầu ra thô (`SUSP-02` ở 28/30 lượt `mini` và 5/6 lượt `gpt-4o` trước hoán vị). Khi tích hợp bước hoán vị kép mã nghi phạm và vật chứng (`id_shuffle.py`), 24 lượt cuối của `gpt-4o` phân bố đều (`9/8/7`) và người chơi gặp thủ phạm/hung khí phân bố đồng đều; đây là phép đổi tên, nội dung vụ án chưa đa dạng hơn.
- Chưa có thử nghiệm người chơi có quy trình; WebSocket phòng chơi chưa có xác thực phiên (chỉ dùng trong LAN tin cậy).
