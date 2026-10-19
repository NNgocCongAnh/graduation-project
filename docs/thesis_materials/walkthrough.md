# Báo cáo tiến độ triển khai Bộ Khung Backend & Docker Compose (Walkthrough)

Đã khởi tạo và hoàn thiện 5 file core theo đúng bản chốt định hướng kỹ thuật của dự án *Trò chơi trinh thám Web AI*:

---

## 📂 Danh sách 5 File Core đã được triển khai

### 1. `backend/app/core/config.py`
- [config.py](file:///d:/Work/%C4%90%E1%BB%93%20%C3%81n%20T%E1%BB%91t%20Nghi%E1%BB%87p/backend/app/core/config.py): Cấu hình Settings sử dụng Pydantic v2 `SettingsConfigDict`.
- Trỏ kết nối AI Gateway về 9Router Proxy cục bộ tại `http://localhost:20128/v1`.
- Cấu hình mặc định `LLM_MODEL = "if/kimi-k2-thinking"` và `LLM_TEMPERATURE = 0.0` đảm bảo tính định tính.
- Tự động nhận diện biến môi trường `DATABASE_URL` (hỗ trợ cả PostgreSQL Docker và SQLite dev local).

### 2. `backend/app/core/database.py`
- [database.py](file:///d:/Work/%C4%90%E1%BB%93%20%C3%81n%20T%E1%BB%91t%20Nghi%E1%BB%87p/backend/app/core/database.py): Khởi tạo SQLAlchemy 2.0 Engine và Session Factory.
- Tự động điều chỉnh `connect_args` phù hợp khi chuyển đổi giữa SQLite local và PostgreSQL.
- Cung cấp hàm dependency `get_db()` phục vụ FastAPI.

### 3. `backend/app/models/models.py`
- [models.py](file:///d:/Work/%C4%90%E1%BB%93%20%C3%81n%20T%E1%BB%91t%20Nghi%E1%BB%87p/backend/app/models/models.py): Định nghĩa đầy đủ 4 bảng CSDL chính với quan hệ `relationship`:
  - **`Case`**: Cột `culprit_id` (khóa ngoại trỏ tới `Character`) được đặt `nullable=True` để giải quyết triệt để lỗi xung đột Circular Foreign Key khi chèn dữ liệu ban đầu.
  - **`Character`**: Quản lý Nạn nhân (victim), Nghi phạm (suspect), và Hung thủ (culprit).
  - **`TimelineEvent`**: Lưu trữ chuỗi diễn biến mốc thời gian vụ án.
  - **`Evidence`**: Quản lý chứng cứ vật lý hiện trường và chứng cứ mấu chốt.

### 4. `backend/app/schemas/case_schema.py`
- [case_schema.py](file:///d:/Work/%C4%90%E1%BB%93%20%C3%81n%20T%E1%BB%91t%20Nghi%E1%BB%87p/backend/app/schemas/case_schema.py): Xây dựng các Pydantic Schemas v2 phục vụ LLM Structured Output:
  - `VictimSchema`: Thông tin nạn nhân và dữ kiện hiện trường/báo cáo pháp y (không ghi thẳng giờ chết).
  - `SuspectSchema`: Thông tin nghi phạm, động cơ, alibi giả.
  - `TimelineEventSchema`: Dòng thời gian mốc sự kiện.
  - `EvidenceSchema`: Danh sách chứng cứ hiện trường.
  - `GeneratedCaseSchema`: Schema tổng hợp kịch bản vụ án hoàn chỉnh.

### 5. `docker-compose.yml`
- [docker-compose.yml](file:///d:/Work/%C4%90%E1%BB%93%20%C3%81n%20T%E1%BB%91t%20Nghi%E1%BB%87p/docker-compose.yml): Đóng gói 4 dịch vụ chính:
  - **`db`**: PostgreSQL 16 (Port `5432:5432`, `POSTGRES_USER=detective_user`, `POSTGRES_DB=detective_db`).
  - **`pgadmin`**: pgAdmin 4 (Port `5050:80`, Email: `admin@detective.com`) để quản lý CSDL trực quan.
  - **`backend`**: FastAPI Server (Port `8000:8000`, kết nối 9Router Gateway qua `host.docker.internal:20128`).
  - **`frontend`**: React Web Client (Port `5173:80`).

---

## 🧪 Kết quả Kiểm thử (Pytest)
Đã chạy bộ unit test [test_backend.py](file:///d:/Work/%C4%90%E1%BB%93%20%C3%81n%20T%E1%BB%91t%20Nghi%E1%BB%87p/backend/tests/test_backend.py) kiểm chứng toàn bộ logic backend:
- `test_database_creation`: **PASSED**
- `test_mock_seed_case_generation_and_validation`: **PASSED**
- `test_circular_fk_case_character`: **PASSED**
