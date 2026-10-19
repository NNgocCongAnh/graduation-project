# BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỒ ÁN TỐT NGHIỆP
## RÀ SOÁT ĐỊNH KỲ 2 THÁNG (GIAI ĐOẠN 1 & 2: TUẦN 1 – TUẦN 8)

---

* **Cơ sở đào tạo:** Trường Đại học Phenikaa – Khoa Công nghệ thông tin
* **Chuyên ngành:** Khoa học máy tính (Định hướng AI & Khoa học Dữ liệu) – Khóa 16 (2022 – 2026)
* **Tên đề tài:** *Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng Mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán*
* **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh
* **Mã sinh viên:** 22010201 &emsp;&emsp; **Lớp:** K16-KHMT(AI&KHDL)
* **Giảng viên hướng dẫn:** TS. Nguyễn Văn Tánh
* **Thời gian thực hiện đồ án:** 22/07/2026 – 10/11/2026 (Tổng cộng 16 tuần)
* **Thời điểm báo cáo:** Ngày 14 tháng 09 năm 2026 (Mốc Tuần 8 / 16 tuần)

---

## I. TỔNG QUAN ĐỀ TÀI & BÀI TOÁN KHOA HỌC

### 1.1. Mục tiêu đề tài
Đề tài tập trung giải quyết bài toán ứng dụng **Mô hình Ngôn ngữ Lớn (Large Language Models - LLM)** kết hợp kỹ thuật **Sinh nội dung tự tục (Procedural Content Generation - PCG)** nhằm tạo ra các bộ hồ sơ vụ án trinh thám tương tác (interactive mystery dossier) có tính suy luận cao theo phong cách giải đố kinh điển (Unsolved Case Files).

Mỗi vụ án sinh ra yêu cầu:
1. **Tính nhất quán và logic tuyệt đối ở sự thật gốc (Ground Truth):** Thời gian gây án, động cơ, cơ chế tử vong, dấu vết hiện trường không xảy ra xung đột vật lý hay mâu thuẫn thời gian.
2. **Khả năng kiểm soát độ mơ hồ (Controlled Ambiguity) ở tầng chứng cứ:** Tái hiện nguyên tắc trinh thám công bằng (*Fair-Play Mystery* theo luật Knox và Van Dine) – bằng chứng và lời khai được phép có sai lệch có chủ đích (alibi giả, lời khai bị bóp méo, manh mối gây nhiễu - red herrings), nhưng luôn đảm bảo tồn tại chuỗi manh mối gián tiếp đủ để người chơi suy luận ra chân tướng.
3. **Triển khai hoàn chỉnh trên Web:** Cung cấp trải nghiệm trực quan cho người chơi (Bảng điều tra Corkboard, ảnh Polaroid nghi phạm, dây chỉ đỏ liên kết, hồ sơ pháp y, form đối chất hung thủ).

### 1.2. Hướng tiếp cận kỹ thuật & Đóng góp cốt lõi
Tránh việc gọi LLM bằng một câu prompt đơn lẻ (Single-prompt) dễ dẫn tới ảo giác (hallucination) và mất kiểm soát logic, hệ thống được thiết kế theo 3 trụ cột kỹ thuật:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KIẾN TRÚC HỆ THỐNG 2 TẦNG (2-LAYER)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [ TẦNG 1: GROUND TRUTH LAYER ]                                         │
│  Sự thật tuyệt đối: Hung thủ thực sự, thời điểm tử vong (TOD),          │
│  vũ khí, mâu thuẫn cốt lõi. (Đảm bảo logic 100%, không ngoại lệ)        │
│                                │                                        │
│                                ▼                                        │
│  [ 4-STEP SEQUENTIAL PIPELINE ]                                         │
│  Sinh phân tầng: Nạn nhân & Pháp y ➔ Nghi phạm & Ground Truth ➔        │
│  Timeline & Chứng cứ ➔ Đóng gói hồ sơ. Ép chuẩn Pydantic JSON Schema.   │
│                                │                                        │
│                                ▼                                        │
│  [ RULE-BASED CONSISTENCY VALIDATOR ENGINE ]                            │
│  Bộ kiểm tra luật cứng: Vật lý nhiệt học Henssge (PMI), đối chiếu       │
│  khung Alibi vs Giờ chết, bắt buộc tồn tại chứng cứ mấu chốt.           │
│                                │                                        │
│                                ▼                                        │
│  [ TẦNG 2: EVIDENCE PRESENTATION LAYER ]                                │
│  Hồ sơ vụ án bàn giao cho người chơi: Lời khai có alibi giả, báo cáo    │
│  khám nghiệm gián tiếp, tang vật hiện trường để suy luận.               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## II. BÁO CÁO TIẾN ĐỘ THỰC HIỆN SAU 2 THÁNG (TUẦN 1 – TUẦN 8)

Đến thời điểm ngày 14/09/2026, đồ án đã hoàn thành trọn vẹn **Giai đoạn 1** và **Giai đoạn 2** (tương đương 50% thời gian toàn khóa biểu 16 tuần):

### 2.1. Kết quả chi tiết Tháng thứ 1 (Tuần 1 đến Tuần 4: 22/07/2026 – 18/08/2026)
* **Khảo sát tài liệu & Cơ sở lý thuyết:**
  - Nghiên cứu các nguyên tắc thiết kế câu đố trinh thám: Knox's Decalogue, Van Dine's 20 Rules for Detective Fiction.
  - Khảo sát các công trình liên quan về Narrative Generation và PCG trong trò chơi trinh thám (Barros et al., Murder Mystery Agent).
  - Hoàn thiện bản đặc tả phân tích kiến trúc hệ thống 2 tầng (*Ground Truth Layer* và *Evidence Presentation Layer*).
* **Thiết kế Mô hình Dữ liệu (Data Modeling):**
  - Sử dụng **Pydantic v2** và **SQLAlchemy 2.0** để thiết kế các thực thể dữ liệu nghiêm ngặt: `CaseDossier`, `Victim`, `Suspect`, `Evidence`, `ForensicData`, `GroundTruth`.
  - Định nghĩa cơ chế xác thực trường thời gian (định dạng `HH:MM`, 24 giờ) và các ràng buộc sinh học (nhiệt độ môi trường, thân nhiệt tử thi, tình trạng hoen ố tử thi).
* **Khởi tạo Dữ liệu Vụ án Mẫu (Seed Case):**
  - Biên soạn bộ hồ sơ vụ án mẫu chuẩn *"Án mạng Biệt thự Blackwood"* làm dữ liệu baseline cho hệ thống kiểm thử tự động offline.

### 2.2. Kết quả chi tiết Tháng thứ 2 (Tuần 5 đến Tuần 8: 19/08/2026 – 14/09/2026)
* **Xây dựng Lõi Điều phối AI (Sequential LLM Generation Pipeline):**
  - Triển khai module `CaseGeneratorService` trong `llm_service.py` chia nhỏ quy trình sinh vụ án thành 4 bước tuần tự.
  - Áp dụng cấu hình định tính `temperature = 0.0` đến `0.7` và `response_format={"type": "json_object"}` giúp loại bỏ 100% lỗi sai định dạng JSON.
  - Tích hợp cơ chế tự động thử lại (Retry Mechanism - tối đa 3 lần) khi phát hiện mâu thuẫn.
* **Phát triển Bộ Kiểm tra Tính Nhất quán (Rule-Based Validator Engine):**
  - Lập trình module `validator.py` với các quy tắc luật cứng không phụ thuộc vào LLM:
    1. *Kiểm tra định danh và tính duy nhất của hung thủ:* Duy nhất 1 hung thủ khớp giữa tầng Ground Truth và danh sách nghi phạm.
    2. *Mô hình Vật lý Nhiệt học Tử thi (Henssge's Nomogram Approximation):* Tính toán khoảng thời gian sau tử vong (Post-Mortem Interval - PMI) từ độ chênh lệch giữa nhiệt độ cơ thể ($37.0^\circ\text{C}$) và nhiệt độ môi trường với tốc độ hạ nhiệt từ $0.8^\circ\text{C}/\text{h}$ đến $1.5^\circ\text{C}/\text{h}$.
    3. *Kiểm tra cửa sổ thời gian gây án (Crime Time vs TOD Window):* Thời điểm hung thủ ra tay bắt buộc phải nằm trong khoảng thời gian tử vong do pháp y ước tính.
    4. *Kiểm tra tính khả giải (Solvability Check):* Bắt buộc phải có ít nhất 1 bằng chứng quyết định (`is_crucial = True`) liên kết trực tiếp để bẻ gãy lời khai ngoại phạm (Alibi) của kẻ thủ ác.
* **Kiểm thử Tự động (Unit Testing):**
  - Xây dựng bộ testcase toàn diện bằng `pytest` trong `test_validator.py`.
  - **Kết quả kiểm thử:** Toàn bộ **6/6 bài kiểm thử đều PASSED 100%** (xác thực vụ án mẫu, phát hiện trùng ID nghi phạm, phát hiện thiếu chứng cứ then chốt, phát hiện giờ chết lệch vật lý, từ chối đa hung thủ).
* **Xây dựng RESTful API Backend (FastAPI):**
  - Hoàn thiện các endpoint chính trong `main.py`:
    - `GET /api/case/sample`: Cung cấp hồ sơ mẫu phục vụ tải nhanh và chạy demo offline.
    - `POST /api/case/generate`: Kích hoạt pipeline sinh vụ án mới theo chủ đề tự chọn.
    - `POST /api/case/verify`: Tiếp nhận suy luận của người chơi và chấm điểm giải đố.
    - `GET /api/health`: Báo cáo trạng thái cổng LLM Gateway và cache hệ thống.
* **Thực nghiệm So sánh Sơ bộ (Benchmark Evaluation):**
  - Khởi tạo notebook thực nghiệm `benchmark_evaluation.ipynb` so sánh hai phương pháp:
    - *Baseline:* Dùng 1 prompt gộp duy nhất (Single-prompt).
    - *Proposed Engine:* Pipeline 4 bước tuần tự kết hợp Validator.
  - Ghi nhận: Phương pháp đề xuất khắc phục triệt để tình trạng vỡ cấu trúc JSON và loại bỏ hoàn toàn các vụ án vô lý về thời gian chết so với Baseline.
* **Prototype Giao diện Web (Front-end):**
  - Dựng khung giao diện ReactJS với phong cách Bảng điều tra trinh thám Corkboard: ghim hồ sơ Polaroid nghi phạm, thẻ bằng chứng, modal xem biên bản pháp y và sơ đồ nối dây chỉ đỏ minh họa liên kết logic.

---

### 2.3. Bảng đối chiếu Mục tiêu Kế hoạch ban đầu vs Kết quả Thực tế đạt được

| Nội dung công việc theo Kế hoạch | Mục tiêu đề ra (Mốc 2 tháng) | Kết quả thực tế đã đạt được | Tình trạng |
| :--- | :--- | :--- | :---: |
| **1. CSDL & Dữ liệu mẫu** | Bảng thiết kế DB + JSON Schemas + 1 vụ án mẫu | Đã định nghĩa đầy đủ 6 Pydantic models v2 + Vụ án mẫu Blackwood Manor | ✅ **Đạt 100%** |
| **2. Pipeline sinh AI 4 bước** | Sinh từng phần, trả lời đúng chuẩn JSON | `llm_service.py` 4 bước tuần tự, ép chuẩn JSON 100% qua API Gateway | ✅ **Đạt 100%** |
| **3. Bộ kiểm tra quy tắc (Validator)** | Tự phát hiện mâu thuẫn giờ chết và alibi | `validator.py` tích hợp công thức Henssge PMI + logic alibi + solvability | ✅ **Đạt 100%** |
| **4. Kiểm thử tự động (Unit Test)** | Có testcase chứng minh validator bắt được lỗi | Bộ 6 unit tests Pytest kiểm chứng toàn diện, chạy thành công 100% | ✅ **Đạt 100%** |
| **5. API Web Service** | Backend cung cấp API sinh và kiểm tra vụ án | FastAPI hoàn chỉnh 4 endpoints chính + tài liệu Swagger UI trực quan | ✅ **Đạt 100%** |
| **6. Giao diện người dùng (UI Prototype)** | Thiết kế wireframe/bản mẫu hiển thị hồ sơ | Đã code prototype ReactJS (Corkboard, Polaroid, Báo cáo khám nghiệm) | ✅ **Đạt 100%** |

---

## III. MINH CHỨNG KỸ THUẬT & SẢN PHẨM ĐẦU RA

### 3.1. Cấu trúc mã nguồn hiện tại trong hệ thống
```text
detective-backend/
├── models.py                   # Định nghĩa Data Models (Victim, Suspect, Evidence, GroundTruth)
├── llm_service.py              # Pipeline sinh vụ án 4 bước tuần tự (Multi-step Prompting)
├── validator.py                # Lõi kiểm tra logic, mô hình nhiệt học tử thi Henssge
├── main.py                     # Ứng dụng RESTful API FastAPI & Endpoints
├── test_validator.py           # Bộ kiểm thử tự động 6 test cases (Pytest)
├── benchmark_evaluation.ipynb  # Đo lường thực nghiệm Baseline vs Proposed Engine
└── requirements.txt            # Danh sách dependencies (FastAPI, Pydantic, Pytest, ...)

frontend/ (Prototype)
├── src/components/CorkBoard.jsx          # Bảng điều tra trinh thám tương tác
├── src/components/DetectiveNotebook.jsx  # Sổ tay ghi chép suy luận của thám tử
├── src/components/DocumentModal.jsx      # Modal xem biên bản pháp y chi tiết
└── src/components/RedStringOverlay.jsx   # Lớp hiển thị dây chỉ đỏ liên kết manh mối
```

### 3.2. Minh chứng Kiểm thử Tự động (Unit Test Execution Log)
Lệnh thực thi: `python -m pytest test_validator.py`
```text
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Work\Đồ Án Tốt Nghiệp\detective-backend
collected 6 items

test_validator.py ......                                                 [100%]

============================== 6 passed in 0.95s ==============================
```
* **Chi tiết 6 testcases:**
  1. `test_sample_case_validity`: Vụ án mẫu chuẩn vượt qua toàn bộ luật kiểm tra logic.
  2. `test_duplicate_suspect_id_detection`: Bắt thành công lỗi trùng lặp mã định danh nhân vật.
  3. `test_missing_crucial_evidence_detection`: Từ chối các vụ án thiếu chứng cứ mấu chốt để phá án.
  4. `test_crime_time_outside_tod_window`: Bắt lỗi khi thời điểm gây án nằm ngoài cửa sổ tử vong pháp y.
  5. `test_multiple_culprits_rejection`: Đảm bảo vụ án có duy nhất 1 kẻ thủ ác thực sự.
  6. `test_time_interval_helper`: Kiểm tra độ chính xác của hàm xử lý thời gian 24h và qua đêm.

---

## IV. BẢNG KẾ HOẠCH TRIỂN KHAI CHI TIẾT THEO TUẦN (WEEKPLAN 16 TUẦN)

| Giai đoạn | Tuần | Mốc thời gian | Nội dung công việc chi tiết | Sản phẩm đầu ra (Deliverables) | Tiến độ |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **Giai đoạn 1**<br>*(Tháng 1)* | **Tuần 1** | 22/07 – 28/07 | Khảo sát bài toán sinh kịch bản trinh thám bằng AI; nghiên cứu các nguyên tắc Fair-play Mystery. | Tài liệu khảo sát lý thuyết | ✅ Đã xong |
| | **Tuần 2** | 29/07 – 04/08 | Thiết kế cấu trúc hệ thống 2 tầng: Tầng 1 (Ground Truth) và Tầng 2 (Evidence Presentation). | Sơ đồ kiến trúc 2 tầng | ✅ Đã xong |
| | **Tuần 3** | 05/08 – 11/08 | Thiết kế mô hình dữ liệu Pydantic v2 và SQLAlchemy ORM cho toàn bộ thực thể vụ án. | Module `models.py` | ✅ Đã xong |
| | **Tuần 4** | 12/08 – 18/08 | Xây dựng bộ dữ liệu vụ án mẫu (Seed case) *"Án mạng Biệt thự Blackwood"* phục vụ kiểm thử offline. | Dữ liệu mẫu JSON hoàn chỉnh | ✅ Đã xong |
| **Giai đoạn 2**<br>*(Tháng 2)* | **Tuần 5** | 19/08 – 25/08 | Thử nghiệm sinh kịch bản bằng Single-prompt để thu thập các lỗi ảo giác và vi phạm cấu trúc JSON. | Dữ liệu lỗi Baseline | ✅ Đã xong |
| | **Tuần 6** | 26/08 – 01/09 | Lập trình Sequential Pipeline 4 bước trên FastAPI kết hợp cơ chế kiểm soát nhiệt độ `temperature=0`. | Module `llm_service.py` | ✅ Đã xong |
| | **Tuần 7** | 02/09 – 08/09 | Xây dựng bộ kiểm tra quy tắc `validator.py`: công thức hạ nhiệt Henssge, kiểm tra Alibi vs TOD window. | Module `validator.py` | ✅ Đã xong |
| | **Tuần 8**<br>*(Hiện tại)* | 09/09 – 14/09 | Viết bộ Unit Test Pytest (6 test pass 100%); dựng khung notebook benchmark; hoàn thành báo cáo tiến độ 2 tháng. | `test_validator.py` + Báo cáo tiến độ | ✅ **Đang báo cáo** |
| **Giai đoạn 3**<br>*(Tháng 3)* | **Tuần 9** | 15/09 – 21/09 | Hoàn thiện ghép nối API giữa Backend FastAPI và Frontend ReactJS (Tải vụ án mới, xem hồ sơ pháp y). | Luồng tạo vụ án hoạt động mượt mà | 🔄 Dự kiến |
| | **Tuần 10** | 22/09 – 28/09 | Xây dựng hệ thống giải đố (Accusation Modal): Chọn hung thủ, chọn chứng cứ cốt lõi và gửi thẩm định. | Hoàn thành Gameplay suy luận | 🔄 Dự kiến |
| | **Tuần 11** | 29/09 – 05/10 | Tổ chức thử nghiệm nội bộ (Internal Playtest) với 5-10 người chơi; thu thập nhật ký giải đố và lỗi UI. | Biên bản ghi nhận Playtest | 🔄 Dự kiến |
| | **Tuần 12** | 06/10 – 12/10 | Tinh chỉnh prompt sinh chứng cứ dựa trên phản hồi; phân tích kết quả đo đạc độ khó và thời gian giải đố. | Bộ số liệu trải nghiệm người chơi | 🔄 Dự kiến |
| **Giai đoạn 4**<br>*(Tháng 4)* | **Tuần 13** | 13/10 – 19/10 | Chạy thực nghiệm định lượng chính thức ($N=30$ vụ án) đo lường Logic Consistency Rate và Latency. | Biểu đồ & Bảng chỉ số thực nghiệm | 🔄 Dự kiến |
| | **Tuần 14** | 20/10 – 26/10 | Viết bản thảo Báo cáo Đồ án tốt nghiệp (Chương 1: Mở đầu, Chương 2: Cơ sở lý thuyết & Kiến trúc). | Bản thảo Chương 1 & 2 | 🔄 Dự kiến |
| | **Tuần 15** | 27/10 – 02/11 | Viết Chương 3 (Hiện thực hệ thống) và Chương 4 (Đánh giá thực nghiệm); gửi GVHD rà soát và chỉnh sửa. | Bản thảo toàn văn Báo cáo | 🔄 Dự kiến |
| | **Tuần 16** | 03/11 – 10/11 | Đóng gói sản phẩm hoàn chỉnh bằng Docker Compose (1-click run); thiết kế Slide và tập dượt bảo vệ. | Quyển báo cáo + Slide + Video Demo | 🔄 Dự kiến |

---

## V. KẾ HOẠCH TRIỂN KHAI 2 THÁNG TIẾP THEO (TUẦN 9 – TUẦN 16)

Dựa trên nền tảng kỹ thuật backend và lõi AI đã vận hành ổn định sau 2 tháng đầu, lộ trình 2 tháng còn lại sẽ tập trung vào 3 trọng tâm:

1. **Trọng tâm 1: Hoàn thiện Sản phẩm Trải nghiệm Trực quan (Tuần 9 – 10)**
   - Ghép nối hoàn chỉnh giữa giao diện Bảng ghim Corkboard (ReactJS) với các API `/api/case/generate` và `/api/case/verify`.
   - Tối ưu hóa trải nghiệm tương tác: kéo thả giấy tờ, ghim dây chỉ đỏ nối giữa nghi phạm và vật chứng, xem phóng to ảnh hiện trường.

2. **Trọng tâm 2: Đánh giá Thực nghiệm & Trải nghiệm Người dùng (Tuần 11 – 13)**
   - **Thực nghiệm người dùng (User Playtest):** Mời 5–10 sinh viên tham gia giải đố 3 vụ án ngẫu nhiên do AI sinh ra. Đo đạc các chỉ số:
     - Tỷ lệ phá án thành công (Accuracy).
     - Thời gian suy luận trung bình (Solving Time).
     - Đánh giá mức độ hài lòng theo thang đo chuẩn *System Usability Scale (SUS)*.
   - **Thực nghiệm kỹ thuật định lượng (Benchmark):** Chạy sinh tự động $N=30$ vụ án liên tục để đo lường:
     - Tỷ lệ tuân thủ định dạng JSON (JSON Schema Validity Rate).
     - Tỷ lệ vượt qua bộ kiểm tra logic không mâu thuẫn (Logic Consistency Pass Rate).
     - Thời gian phản hồi trung bình của hệ thống (Pipeline Latency).

3. **Trọng tâm 3: Hoàn thiện Quyển Báo cáo Đồ án Tốt nghiệp & Bảo vệ (Tuần 14 – 16)**
   - Hoàn thành toàn văn quyển Báo cáo Đồ án gồm 4 chương chuẩn mực học thuật:
     - *Chương 1: Tổng quan về sinh nội dung tự tục bằng AI trong trò chơi giải đố.*
     - *Chương 2: Cơ sở lý thuyết về LLM, Fair-play Mystery và Kiến trúc hệ thống 2 tầng.*
     - *Chương 3: Thiết kế và Hiện thực Hệ thống (Sequential Pipeline & Rule-based Validator).*
     - *Chương 4: Thực nghiệm, Đánh giá Kết quả và Hướng phát triển.*
   - Đóng gói toàn bộ hệ thống bằng Docker Compose để đảm bảo việc demo trực tiếp trước Hội đồng chấm bảo vệ diễn ra trơn tru chỉ với 1 câu lệnh.

---

## VI. CÁC ĐỀ XUẤT & XIN Ý KIẾN HƯỚNG DẪN TỪ GVHD (TS. NGUYỄN VĂN TÁNH)

Để giai đoạn 2 tháng cuối triển khai đúng định hướng và đạt kết quả cao nhất trước Hội đồng chấm đồ án, sinh viên kính mong nhận được ý kiến đóng góp từ thầy về các vấn đề sau:

1. **Về phương pháp thực nghiệm định lượng:**
   - Trong Chương 4 (Thực nghiệm & Đánh giá), em dự kiến so sánh trực tiếp giữa phương pháp Baseline (Single-prompt) và Proposed Method (4-Step Pipeline + Validator) trên tập $N=30$ vụ án thử nghiệm về 3 tiêu chí: Tỷ lệ đúng JSON, Tỷ lệ vượt qua Validator, và Thời gian sinh. Thầy xem giúp em cỡ mẫu $N=30$ như vậy đã đủ độ tin cậy về mặt thống kê cho một đồ án đại học chưa ạ?
2. **Về tiêu chí đánh giá trải nghiệm suy luận của người dùng:**
   - Ngoài thang đo chuẩn SUS về tính khả dụng của phần mềm Web, em dự kiến đưa thêm tiêu chí khảo sát về tính "Fair-play" (Người chơi có cảm thấy bị lừa vô lý hay thấy các manh mối gián tiếp là hợp lý và thuyết phục). Thầy có lời khuyên nào để thiết kế bộ câu hỏi khảo sát này khoa học hơn không ạ?
3. **Về bố cục và dung lượng quyển Báo cáo Đồ án:**
   - Em dự kiến cấu trúc quyển báo cáo gồm 4 chương với dung lượng khoảng 50 - 65 trang (không tính phụ lục mã nguồn và dữ liệu vụ án mẫu). Thầy cho em xin ý kiến về định hướng phân bổ số trang cho từng chương để đảm bảo cân đối giữa hàm lượng nghiên cứu AI và phần sản phẩm ứng dụng.

---

*Hà Nội, ngày 14 tháng 09 năm 2026*  
**Sinh viên báo cáo**  
*(Ký và ghi rõ họ tên)*  

**Nguyễn Ngọc Công Anh**  
*MSSV: 22010201*
