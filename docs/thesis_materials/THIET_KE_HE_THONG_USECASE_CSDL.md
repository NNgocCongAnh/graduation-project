# THIẾT KẾ KIẾN TRÚC HỆ THỐNG: SƠ ĐỒ USE CASE & CƠ SỞ DỮ LIỆU (ERD)
**Đồ án Tốt nghiệp: Hệ thống Game Trinh thám Tạo sinh bằng AI Neuro-Symbolic**
*Sinh viên: Nguyễn Ngọc Công Anh | MSSV: 22010201 | Phenikaa University*

---

## PHẦN 1: SƠ ĐỒ USE CASE (USE CASE DIAGRAM)

### 1.1. Hình ảnh Sơ đồ Use Case
> 🖼️ **Ảnh xuất bản độ phân giải cao (300 DPI):**  
> [detective-backend/figures/so_do_usecase.png](file:///d:/Work/Đồ%20Án%20Tốt%20Nghiệp/detective-backend/figures/so_do_usecase.png)

```mermaid
graph LR
    subgraph Actors [Tác tử ngoài hệ thống]
        Player((👤 Người chơi<br>Player / Detective))
        AI((🤖 Multi-Agent AI<br>Gemma / LLMs))
        Validator((⚖️ Symbolic Validator<br>Henssge / Logic Engine))
    end

    subgraph SystemBoundary [HỆ THỐNG GAME TRINH THÁM AI]
        UC1([UC01: Khởi tạo vụ án theo chủ đề])
        UC2([UC02: Sinh kịch bản & nhân vật tự động])
        UC3([UC03: Thẩm định vật lý & vá lỗi cục bộ])
        UC4([UC04: Khám nghiệm thi thể & đọc Alibi])
        UC5([UC05: Thu thập & nối dây manh mối])
        UC6([UC06: Buộc tội hung thủ & nộp án])
        UC7([UC07: Xem lời giải chân tướng])
    end

    Player --> UC1
    Player --> UC4
    Player --> UC5
    Player --> UC6
    Player --> UC7

    AI -.-> UC1
    AI -.-> UC2
    AI -.-> UC3

    Validator -.-> UC3
    Validator -.-> UC6
```

### 1.2. Bảng Phân tích Chi tiết Các Ca Sử Dụng (Use Cases)

| Mã UC | Tên Use Case | Tác tử (Actors) | Mô tả chi tiết |
| :---: | :--- | :--- | :--- |
| **UC01** | Khởi tạo vụ án | Người chơi, AI | Người chơi chọn chủ đề mong muốn (VD: *Du thuyền sông Nile, Phòng máy chủ AI*) hoặc chọn sinh ngẫu nhiên. |
| **UC02** | Sinh kịch bản tự động | Multi-Agent AI | 4 Agent (`Outline`, `Character`, `Clue`, `Deduction`) tự động sinh bối cảnh, nạn nhân, 3 nghi phạm và 3-4 manh mối. |
| **UC03** | Thẩm định & Vá lỗi | Symbolic Validator, AI | Kiểm định công thức Henssge và đồ thị phá án. Nếu sai lệch, gửi phản hồi bắt đúng Agent liên quan vá cục bộ (Patch Repair). |
| **UC04** | Khám nghiệm hiện trường | Người chơi | Người chơi xem xét nhiệt độ phòng, thân nhiệt nạn nhân, vết thương và nghe lời khai Alibi của từng nghi phạm. |
| **UC05** | Nối dây manh mối (Corkboard) | Người chơi | Người chơi tương tác trên bảng điều tra, nối dây đỏ giữa lời khai nghi phạm và chứng cứ gián tiếp (dao, thẻ từ, ly trà). |
| **UC06** | Buộc tội hung thủ (Verify) | Người chơi, Validator | Người chơi chọn 1 nghi phạm là hung thủ + chọn chứng cứ mấu chốt để bẻ gãy Alibi. Hệ thống tự động chấm điểm. |
| **UC07** | Xem lời giải chân tướng | Người chơi | Khi phá án thành công (hoặc kết thúc lượt chơi), hệ thống mở khóa toàn bộ Bản án ngầm (Ground Truth) và chuỗi suy luận đa bước. |

---

## PHẦN 2: THIẾT KẾ CƠ SỞ DỮ LIỆU (DATABASE ERD SCHEMA)

### 2.1. Hình ảnh Sơ đồ Thực thể Liên kết (ERD)
> 🖼️ **Ảnh xuất bản độ phân giải cao (300 DPI):**  
> [detective-backend/figures/so_do_co_so_du_lieu_erd.png](file:///d:/Work/Đồ%20Án%20Tốt%20Nghiệp/detective-backend/figures/so_do_co_so_du_lieu_erd.png)

```mermaid
erDiagram
    CASES ||--|| VICTIMS : "has (1:1)"
    CASES ||--|| GROUND_TRUTHS : "has (1:1)"
    CASES ||--|{ SUSPECTS : "contains (1:N)"
    CASES ||--|{ EVIDENCES : "contains (1:N)"
    CASES ||--|{ DEDUCTION_STEPS : "proves (1:N)"
    SUSPECTS ||--o{ EVIDENCES : "linked_to (1:N)"

    CASES {
        string case_id PK "Mã vụ án duy nhất (VD: CASE-2026-001)"
        string title "Tiêu đề kịch bản"
        text summary "Tóm tắt bối cảnh"
        timestamp created_at "Thời điểm sinh"
        string model_name "Model AI sinh (Gemma / GPT)"
        float validator_score "Điểm logic (1.0 = Đạt chuẩn)"
        boolean is_solved "Trạng thái người chơi đã phá án chưa"
    }

    VICTIMS {
        string victim_id PK "Mã nạn nhân"
        string case_id FK "Thuộc vụ án nào"
        string name "Họ tên nạn nhân"
        int age "Tuổi"
        string occupation "Nghề nghiệp"
        float ambient_temp "Nhiệt độ môi trường (°C)"
        float body_temp "Thân nhiệt lúc tìm thấy (°C)"
        string wound_description "Mô tả vết thương tử vong"
        string livor_mortis_state "Trạng thái hoen ố tử thi"
        string estimated_tod_start "Giờ chết sớm nhất (HH:MM)"
        string estimated_tod_end "Giờ chết muộn nhất (HH:MM)"
    }

    GROUND_TRUTHS {
        string gt_id PK "Mã bản án"
        string case_id FK "Thuộc vụ án nào"
        string culprit_id FK "Mã nghi phạm hung thủ thực sự"
        string actual_crime_time "Thời điểm gây án thực tế (HH:MM)"
        string murder_weapon "Hung khí thực sự"
        text core_contradiction "Mâu thuẫn mấu chốt phá án"
    }

    SUSPECTS {
        string suspect_id PK "Mã nghi phạm (VD: SUSP-01)"
        string case_id FK "Thuộc vụ án nào"
        string name "Tên nghi phạm"
        int age "Tuổi"
        string occupation "Nghề nghiệp"
        text motive "Động cơ gây án"
        string alibi_start "Giờ bắt đầu Alibi (HH:MM)"
        string alibi_end "Giờ kết thúc Alibi (HH:MM)"
        text alibi_statement "Lời khai ngoại phạm"
        text secret_innocent_fact "Bí mật mờ ám vô tội (Red Herring)"
        boolean is_culprit "Có phải hung thủ không"
    }

    EVIDENCES {
        string evidence_id PK "Mã chứng cứ (VD: EV-01)"
        string case_id FK "Thuộc vụ án nào"
        string title "Tên manh mối"
        string location "Vị trí tìm thấy tại hiện trường"
        text description "Mô tả chi tiết"
        string linked_suspect_id FK "Liên đới tới nghi phạm nào"
        boolean is_crucial "Có phải manh mối then chốt bẻ Alibi không"
        boolean is_red_herring "Có phải chứng cứ tung hỏa mù không"
    }

    DEDUCTION_STEPS {
        string step_id PK "Mã bước suy luận"
        string case_id FK "Thuộc vụ án nào"
        int step_number "Thứ tự bước (1, 2, 3)"
        json clue_ids "Danh sách mã manh mối sử dụng"
        string target_suspect_id FK "Nghi phạm bị chỉ trích"
        text inference "Lập luận suy diễn trung gian"
    }
```

---

### 2.2. Chi tiết Các Bảng & Toàn Vẹn Dữ Liệu (Integrity Constraints)

1. **Bảng `CASES` (Bảng cha trung tâm):**
   - Đóng vai trò gốc để quản lý vòng đời của mọi vụ án.
   - Khi xóa 1 Case $\rightarrow$ Tự động xóa (Cascade Delete) toàn bộ Nạn nhân, Nghi phạm, Chứng cứ liên quan.
2. **Quan hệ 1:1 (`VICTIMS` và `GROUND_TRUTHS`):**
   - Mỗi vụ án bắt buộc có đúng 1 Nạn nhân và 1 Bản án bí mật.
   - `GROUND_TRUTHS.culprit_id` là khóa ngoại trỏ thẳng tới `SUSPECTS.suspect_id` đảm bảo hung thủ luôn tồn tại trong danh sách nghi phạm.
3. **Quan hệ 1:N (`SUSPECTS`, `EVIDENCES`, `DEDUCTION_STEPS`):**
   - Mỗi vụ án có từ $3 - 5$ nghi phạm và $3 - 6$ manh mối.
   - Ràng buộc toàn vẹn: Bắt buộc phải có **ít nhất 1 bản ghi `EVIDENCES` có `is_crucial = True`** để bảo đảm tính giải được.
4. **Cơ chế lưu trữ linh hoạt:**
   - Trong môi trường phát triển & kiểm thử: Dữ liệu được ánh xạ 1:1 sang JSON file trong thư mục `cases/{case_id}.json`.
   - Trong môi trường production: Schema trên sẵn sàng triển khai trên **PostgreSQL / SQLite** qua SQLAlchemy/SQLModel mà không cần thay đổi bất kỳ trường dữ liệu nào.
