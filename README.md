# ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC — UNSOLVED CASE FILES AI

**Đề tài:** *Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán*  
*(Hướng tiếp cận Neuro-Symbolic kết hợp Hệ đa tác tử và Bộ kiểm định hình thức)*

- **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh — MSSV: `22010201` — Lớp: `K16-KHMT`
- **Cán bộ hướng dẫn:** TS. Nguyễn Văn Tánh — Khoa Khoa học máy tính, Trường Đại học Phenikaa

---

## 📊 Danh mục Kết quả & Tài liệu Bàn giao

Dự án đã hoàn tất **100% các hạng mục nghiên cứu, phát triển phần mềm và đánh giá thực nghiệm**, phục vụ buổi bảo vệ khóa luận tốt nghiệp:

| Hạng mục | Tệp / Thư mục trên Kho chứa | Mô tả |
| :--- | :--- | :--- |
| **Bản mềm Luận văn (PDF)** | [`BAO_CAO_LUAN_VAN_TOT_NGHIEP_22010201.pdf`](./BAO_CAO_LUAN_VAN_TOT_NGHIEP_22010201.pdf) | Bản báo cáo hoàn chỉnh 5 chương theo quy chuẩn Đại học Phenikaa |
| **Slide Thuyết trình** | [`BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx`](./BAO_VE_KHOA_LUAN_TOT_NGHIEP.pptx) | Bộ slide báo cáo tiến độ và bảo vệ khóa luận tốt nghiệp |
| **Kết quả Thực nghiệm** | [`benchmark_evaluation.ipynb`](./benchmark_evaluation.ipynb) | Sổ tay Jupyter tổng hợp 30 phiên thực nghiệm đối sánh 3 mô hình LLM |
| **Mã nguồn Backend AI** | [`detective-backend/`](./detective-backend) | FastAPI ASGI, 4 Specialized Agents, Validator Henssge & Bipartite Matching |
| **Mã nguồn Game Client** | [`Unity/My project/`](./Unity/My%20project) | Unity 6 URP (Bàn trinh thám, Corkboard, Hồ sơ pháp y, Quy trình 3 phong bì) |
| **Khởi chạy Docker** | [`docker-compose.yml`](./docker-compose.yml) | Cấu hình Docker Compose khởi chạy trọn gói máy chủ chỉ với 1 lệnh |
| **Mẫu Biến môi trường** | [`.env.example`](./.env.example) | Mẫu cấu hình an toàn cho OpenRouter, 9Router, Google AI Studio hoặc Ollama |

---

## 🏗️ Kiến trúc Hệ thống (Neuro-Symbolic Multi-Agent)

Hệ thống kết hợp sức mạnh biểu đạt ngữ nghĩa của **Mô hình Ngôn ngữ Lớn (LLM)** với tính chính xác toán học của **Bộ kiểm định Biểu tượng (Symbolic Validator)**:

```text
[ Unity 6 URP 2D/3D Client (Desktop EXE / WebGL) ]
             │  REST API (HTTP/JSON + HMAC-SHA-256) & WebSocket (/ws/rooms/{room_id})
             ▼
[ FastAPI Backend (ASGI / Uvicorn) + Pydantic v2 + SQLite WAL ]
             │
             ├── 1. OutlineAgent   ──► Cốt truyện, Nạn nhân & Khóa giờ tử vong Henssge (Bisection)
             ├── 2. CharacterAgent ──► Nghi phạm & Lời khai ngoại phạm (Zero-spoiler, không sơ hở rẻ tiền)
             ├── 3. ClueAgent      ──► 5 vật chứng khách quan & Mâu thuẫn môi trường (EV-01..EV-05)
             ├── 4. Bộ kiểm định   ──► validate_case_diagnostics (Henssge + Đồ thị hai phía Bipartite)
             │                         └── Localized Patch Repair (Sửa cục bộ thành phần lỗi O(1))
             └── 5. DeductionAgent ──► Chuỗi suy luận đa chặng (4-Hop Reasoning Chain)
             │
             ▼
[ Cloud LLM Gateway (OpenAI GPT-4o-mini / Google AI Studio Gemini / 9Router / Ollama) ]
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### Cách 1: Khởi chạy bằng Docker Compose (Khuyến nghị cho Server / Tester)
Yêu cầu: Đã cài đặt Docker và Docker Compose.
```bash
# 1. Sao chép file cấu hình môi trường
cp .env.example .env

# 2. Khởi chạy toàn bộ dịch vụ backend bằng Docker
docker compose up --build -d
```
* Backend API hoạt động tại: `http://localhost:8000/docs`
* Kiểm tra trạng thái máy chủ: `http://localhost:8000/api/health`

---

### Cách 2: Khởi chạy 1-Click trên Windows (Cho người chơi Game)
1. Nhấp đúp chuột vào file:
   ```text
   CHAY_GAME_TRON_GOI.bat
   ```
2. Hệ thống sẽ tự động bật máy chủ Backend FastAPI chạy ngầm và mở game Unity `UnsolvedCaseFiles.exe`.

---

### Cách 3: Khởi chạy Thủ công bằng Python (Dành cho Lập trình viên)
```bash
# 1. Cài đặt môi trường Backend
cd detective-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Khởi chạy FastAPI Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎮 Cơ chế Chơi & Quy trình Điều tra Phá án

Game mô phỏng chân thực quy trình phá án của một tập hồ sơ vụ án lạnh (*Cold Case File*):
1. **📁 Tờ Giới thiệu Vụ án (Briefing Sheet - Phím B):** Đọc tóm tắt nhân thân nạn nhân, mốc thời gian và biên bản ghi chép của sĩ quan đầu tiên tiếp cận hiện trường.
2. **🩺 Báo cáo Pháp y Khám nghiệm Tử thi (Autopsy - Phím M):** Đọc nhiệt độ trực tràng, nhiệt độ môi trường và tính toán khung giờ tử vong thực tế theo định luật nguội lạnh Henssge ($t^*$) để phá hiện trường giả.
3. **📌 Bảng ghim Manh mối (Corkboard):** Soi ảnh chân dung nghi phạm, lời khai ngoại phạm (alibi) và đối chiếu 5 vật chứng hiện trường (EV-01 đến EV-05).
4. **✉️ Hệ thống 3 Phong bì Mục tiêu (Objective Envelopes - Phím A):**
   - **Phong bì 1:** Chứng minh nghi phạm vô tội (Exonerate) dựa trên alibi độc lập để mở khóa Phong bì 2.
   - **Phong bì 2:** Vạch trần hiện trường giả & Tìm hung khí thật sự (bẻ gãy alibi hung thủ).
   - **Phong bì 3:** Phát lệnh bắt giữ chính thức (Arrest Warrant) $\rightarrow$ Khởi tố hung thủ và xem phần **Tái hiện toàn cảnh vụ án (Bonus Solution)**.

---

## 🔬 Kết quả Đánh giá Thực nghiệm (Chương 4 Luận văn)

Thực nghiệm đo đạc 30 phiên độc lập trên phần cứng nghiên cứu:
* **Mô hình triển khai (`gh/gpt-4o-mini`):** Tỷ lệ hợp lệ logic đạt **100%**, độ trễ trung bình $10.98\text{ s}$.
* **Mô hình đối chuẩn (`ollama/gemma4:31b-cloud`):** Tỷ lệ hợp lệ logic **100%**, độ trễ trung bình $11.66\text{ s}$.
* **Sai số thời gian tử vong (Henssge):** Đạt **0%** nhờ tầng giải số vi phân bisection độc lập.
* **Cơ chế sửa lỗi cục bộ (Localized Patch Repair):** Tiết kiệm **65%** thời gian suy luận so với việc tạo sinh lại toàn bộ kịch bản khi phát hiện vi phạm ràng buộc.
Chi tiết số liệu đối sánh và biểu đồ có trong file [`benchmark_evaluation.ipynb`](./benchmark_evaluation.ipynb).
