# ĐỒ ÁN TỐT NGHIỆP: NGHIÊN CỨU ỨNG DỤNG AGENT TẠO KỊCH BẢN TRÒ CHƠI TRINH THÁM (UNSOLVED CASE FILES AI)

## 📌 Giới thiệu đề tài
Đề tài đồ án tốt nghiệp tập trung nghiên cứu và ứng dụng **Large Language Models (LLM) & Agentic Architecture** nhằm tự động sinh kịch bản và hồ sơ vụ án trinh thám tương tác theo phong cách **"Unsolved Case Files"**.

Hệ thống cho phép người chơi hóa thân thành thám tử, tiếp cận hồ sơ vụ án gồm: thông tin nạn nhân, danh sách nghi phạm với động cơ/alibi, báo cáo pháp y hiện trường, chứng cứ vật lý và chuỗi sự kiện timeline. Người chơi thu thập manh mối, xâu chuỗi thông tin trên bảng điều tra (Corkboard) và đưa ra phán đoán hung thủ.

---

## 🏗️ Kiến trúc Hệ thống

Dự án được xây dựng theo mô hình Client-Server phân tầng kết hợp AI Generation Pipeline & Validation:

```
[ Frontend (React + Vite) ] <---> [ Backend API (FastAPI) ] <---> [ Database (PostgreSQL / SQLite) ]
                                            │
                                            ▼
                                  [ AI Agent Pipeline ]
                                  ├── 1. Khởi tạo cốt truyện & Nạn nhân
                                  ├── 2. Sinh nghi phạm & Động cơ / Alibi
                                  ├── 3. Sinh dòng thời gian (Timeline)
                                  ├── 4. Sinh chứng cứ & Báo cáo pháp y
                                  └── 5. Validator Engine (Kiểm tra logic & tính nhất quán)
                                            │
                                            ▼
                                  [ LLM Gateway (9Router / OpenAI / OpenRouter) ]
```

### 1. Backend (FastAPI & Python 3.11+)
- **FastAPI**: Cung cấp RESTful API hiệu năng cao quản lý game state, tạo vụ án mới, tra cứu hồ sơ và kiểm tra giả thuyết phá án.
- **SQLAlchemy 2.0 & Pydantic v2**: Quản lý ORM models (`Case`, `Character`, `TimelineEvent`, `Evidence`) và Structured Output validation cho LLM.
- **Case Generation Pipeline**: Quy trình tuần tự nhiều bước (Multi-step Agentic Pipeline) với các prompt chuyên biệt để sinh hồ sơ vụ án chặt chẽ.
- **Consistency Validator Engine**: Bộ kiểm tra luật cứng (Rule-based) và logic giúp loại bỏ mâu thuẫn về thời gian tử vong, ngoại phạm (alibi), hung khí và lời khai.

### 2. Frontend (React 18 & TailwindCSS)
- **Interactive Corkboard UI**: Bảng điều tra trinh thám trực quan với các thẻ ghim nghi phạm, chứng cứ, ghi chú và dây nối đỏ liên kết manh mối.
- **Detective Notebook & Documents**: Xem báo cáo pháp y (Autopsy report), hồ sơ thẩm vấn, chi tiết vật chứng.
- **Accusation System**: Form đối chất và đưa ra cáo buộc hung thủ kèm lập luận phá án.

### 3. Container & Hạ tầng (Docker & Docker Compose)
- **PostgreSQL 16**: Cơ sở dữ liệu quan hệ lưu trữ trạng thái vụ án.
- **pgAdmin 4**: Giao diện trực quan quản lý CSDL.
- **Docker Compose**: Đóng gói và chạy toàn bộ hệ thống với một câu lệnh.

---

## 📁 Cấu trúc Thư mục

```text
├── backend/
│   ├── app/
│   │   ├── api/          # API Routers (case_router.py, ...)
│   │   ├── core/         # Config biến môi trường, kết nối Database
│   │   ├── models/       # SQLAlchemy ORM Models (Case, Character, Evidence, Timeline)
│   │   ├── schemas/      # Pydantic Schemas định dạng JSON cho LLM
│   │   ├── services/     # LLM Pipeline Service & Consistency Validator Service
│   │   └── main.py       # Điểm khởi chạy ứng dụng FastAPI
│   ├── tests/            # Unit tests (Pytest)
│   ├── Dockerfile        # Dockerfile cho Backend
│   └── requirements.txt  # Danh sách thư viện Python
├── frontend/
│   ├── public/           # Tài nguyên tĩnh & hình ảnh minh họa (Mugshots, Evidence)
│   ├── src/
│   │   ├── components/   # Các thành phần UI (CorkBoard, Modals, Notebook, Cards)
│   │   ├── App.jsx       # Component chính quản lý trạng thái trò chơi
│   │   ├── App.css       # Custom styles
│   │   └── main.jsx      # Điểm khởi chạy React Vite
│   ├── Dockerfile        # Dockerfile cho Frontend
│   ├── package.json      # Danh sách dependencies Frontend
│   └── vite.config.js    # Cấu hình Vite
├── .env.example          # Mẫu cấu hình biến môi trường
├── docker-compose.yml    # Cấu hình khởi chạy toàn bộ dịch vụ Docker
└── README.md             # Tài liệu dự án
```

---

## 🚀 Hướng dẫn Cài đặt & Chạy ứng dụng

### 1. Yêu cầu hệ thống
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (tùy chọn nhưng khuyến nghị)

### 2. Cấu hình biến môi trường
Sao chép file `.env.example` thành `.env` và cập nhật thông tin:
```bash
cp .env.example .env
```

Các thông số cấu hình chính:
- `DATABASE_URL`: Đường dẫn kết nối CSDL (SQLite local hoặc PostgreSQL).
- `LLM_API_BASE`: Endpoint OpenAI-compatible gateway (ví dụ: `http://localhost:20128/v1` hoặc OpenRouter).
- `LLM_API_KEY`: Khóa xác thực API LLM.
- `LLM_MODEL`: Model LLM sử dụng (ví dụ: `openrouter/nvidia/nemotron-3-super-120b-a12b:free`, `gpt-4o`, ...).

---

### 3. Khởi chạy bằng Docker Compose (Khuyến nghị)
Chạy toàn bộ Backend, Frontend, PostgreSQL và pgAdmin:
```bash
docker-compose up -d --build
```
- Frontend: `http://localhost:5173`
- Backend Swagger Docs: `http://localhost:8000/docs`
- pgAdmin: `http://localhost:5050` (Email: `admin@detective.com`, Pass: `admin`)

---

### 4. Khởi chạy thủ công (Development Mode)

#### Chạy Backend:
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Chạy Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 🕵️ Chơi co-op trong mạng LAN (tối đa 3 người)

**Máy chủ (1 máy):**
1. Chạy backend cho phép máy khác kết nối:
   ```bash
   cd detective-backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. Lần đầu, cho phép Python qua Windows Firewall ở mạng **Private**: TCP 8000 (game) và UDP 47777 (tự tìm máy chủ).
3. Mở game, nhấn **L** → **TỰ LÀM MÁY CHỦ**. Modal hiện "IP của máy này" để đọc cho bạn chơi.

**Máy khách (tối đa 2 máy):** mở game, nhấn **L** → **TÌM MÁY CHỦ** (hoặc gõ IP máy chủ) → nhập cùng **Mã phòng** → **KẾT NỐI**.

| Phím | Chức năng |
|---|---|
| giữ **V** | Nói (voice, nên đeo tai nghe) |
| **T** | Chat chữ |
| **L** | Phòng LAN |
| **Esc** | Đóng chat / modal |

Đồng bộ trong phòng: vụ án đang điều tra, vị trí thẻ trên bảng, chat và voice. Người vào sau nhận đúng trạng thái hiện tại. Người thứ 4 bị từ chối ("phòng đầy"). Voice là PCM 16 kHz qua WebSocket (≈32 KB/s mỗi người nói), không cần tài khoản hay dịch vụ ngoài. Có thể dùng Discord thay thế bằng cách đơn giản là không giữ V.

---

## 🧪 Kiểm thử (Testing)
Chạy bộ kiểm thử backend với Pytest:
```bash
cd backend
pytest tests/
```
