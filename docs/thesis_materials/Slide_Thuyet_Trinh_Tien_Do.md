---
marp: true
theme: default
paginate: true
header: "Đồ án Tốt nghiệp K16 - ĐH Phenikaa | Báo cáo Tiến độ 2 Tháng"
footer: "SV: Nguyễn Ngọc Công Anh (22010201) | GVHD: TS. Nguyễn Văn Tánh"
---

# BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỒ ÁN TỐT NGHIỆP
## (Rà soát định kỳ sau 2 tháng - Tuần 8 / 16)

**Đề tài:** Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng Mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán

* **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh (MSSV: 22010201)
* **Lớp:** K16-KHMT(AI&KHDL) – Khoa Công nghệ thông tin
* **Giảng viên hướng dẫn:** TS. Nguyễn Văn Tánh
* **Thời gian:** 14/09/2026

---

# 1. BỐI CẢNH & BÀI TOÁN KHOA HỌC

* **Vấn đề của phương pháp truyền thống (Single-prompt LLM):**
  * Dễ sinh lỗi ảo giác (Hallucination), mâu thuẫn thời gian và lời khai.
  * Thất bại trong việc tuân thủ cấu trúc JSON phức tạp (JSON syntax error).
  * Câu chuyện hoặc quá dễ (lộ ngay hung thủ), hoặc vô lý đến mức "bất khả giải" (*Unsolvable*).
* **Mục tiêu đề tài:**
  * Xây dựng hệ thống sinh kịch bản trinh thám tự tục (**PCG**) có kiểm soát logic.
  * Tái hiện nguyên tắc trinh thám công bằng (**Fair-Play Mystery**): Lời khai có thể nói dối (Alibi giả, Red herrings), nhưng luôn có đường dây manh mối gián tiếp đủ để người chơi phá án.

---

# 2. HƯỚNG TIẾP CẬN: KIẾN TRÚC 2 TẦNG (2-LAYER)

Hệ thống tách bạch rõ ràng giữa hai tầng dữ liệu:

* **Tầng 1: Ground Truth Layer (Sự thật tuyệt đối)**
  * Ai giết, vào lúc nào, ở đâu, bằng vũ khí gì, mâu thuẫn quyết định là gì.
  * **Nguyên tắc:** Nhất quán 100%, tuân thủ vật lý và thời gian nghiêm ngặt.
* **Tầng 2: Evidence Presentation Layer (Tầng hồ sơ trao cho người chơi)**
  * Lời khai nghi phạm (có alibi giả, che giấu động cơ).
  * Biên bản pháp y hiện trường (ẩn giờ chết trực tiếp, chỉ cho thông số sinh học).
  * Vật chứng thu thập tại hiện trường.

---

# 3. GIẢI PHÁP KỸ THUẬT CỐT LÕI

Hệ thống được thiết kế dựa trên 2 thành phần chủ chốt:

1. **4-Step Sequential Pipeline (Quy trình sinh tuần tự):**
   * *Bước 1:* Sinh nạn nhân & Dữ kiện pháp y.
   * *Bước 2:* Sinh nghi phạm & Sự thật gốc (Ground Truth).
   * *Bước 3:* Sinh timeline & Bằng chứng hiện trường.
   * *Bước 4:* Đóng gói Case Dossier hoàn chỉnh (Ép chuẩn Pydantic v2 JSON Schema).
2. **Rule-Based Consistency Validator Engine:**
   * Bộ kiểm tra quy tắc độc lập bằng Python thuần (không phụ thuộc vào LLM) để bắt lỗi logic trước khi lưu trữ và gửi cho người chơi.

---

# 4. TRỌNG TÂM NGHIÊN CỨU: VALIDATOR ENGINE

* **Ứng dụng Định luật Hạ thân nhiệt Henssge (Henssge's Nomogram):**
  * Tính toán khoảng thời gian sau tử vong ($PMI$) dựa trên nhiệt độ thi thể ($37.0^\circ\text{C} \rightarrow T_{body}$) và môi trường ($T_{ambient}$) với tốc độ làm nguội $0.8 - 1.5^\circ\text{C}/\text{h}$.
  * Bắt buộc thời điểm gây án của hung thủ phải rơi vào khoảng $TOD$ pháp y.
* **Kiểm tra Tính duy nhất:** Duy nhất 1 hung thủ thực sự khớp với Ground Truth.
* **Kiểm tra Khả giải (Solvability Check):**
  * Bắt buộc phải có ít nhất 1 chứng cứ quyết định (`is_crucial = True`) bẻ gãy lời khai ngoại phạm của hung thủ.

---

# 5. KẾT QUẢ KỸ THUẬT ĐẠT ĐƯỢC (SAU 2 THÁNG)

* ✅ **Data Models & Schemas:** Hoàn thành 6 schemas Pydantic v2 nghiêm ngặt tại `models.py`.
* ✅ **Pipeline AI:** Hoàn thành `CaseGeneratorService` (`llm_service.py`) tích hợp cơ chế tự động thử lại (Retry) khi phát hiện mâu thuẫn.
* ✅ **Validator Engine:** Hoàn thành `validator.py` kiểm tra logic Henssge và Alibi.
* ✅ **Unit Testing:** **6/6 Tests PASSED 100%** bằng Pytest (`test_validator.py`).
* ✅ **RESTful API Backend:** FastAPI hoàn chỉnh các endpoints:
  * `GET /api/case/sample` (Hồ sơ mẫu chuẩn phục vụ test offline).
  * `POST /api/case/generate` (Sinh vụ án mới theo chủ đề).
  * `POST /api/case/verify` (Thẩm định suy luận của người chơi).

---

# 6. MINH CHỨNG SẢN PHẨM & GIAO DIỆN WEB

* **Bộ kiểm thử Pytest:**
  ```text
  test_validator.py ......                                    [100%]
  ====================== 6 passed in 0.95s =========================
  ```
* **Prototype Giao diện Web (ReactJS):**
  * Bảng điều tra Corkboard ghim ảnh Polaroid nghi phạm và thẻ vật chứng.
  * Dây chỉ đỏ nối trực quan các manh mối khả nghi.
  * Modal xem chi tiết Biên bản khám nghiệm tử thi và Sổ tay suy luận của Thám tử.

---

# 7. ĐỐI CHIẾU TIẾN ĐỘ 16 TUẦN (WEEKPLAN)

* **Tuần 1 - 4 (Tháng 1):** Khảo sát lý thuyết, thiết kế kiến trúc 2 tầng, mô hình CSDL & Vụ án mẫu $\rightarrow$ **Đã hoàn thành 100%**.
* **Tuần 5 - 8 (Tháng 2 - Hiện tại):** Lập trình Pipeline 4 bước, phát triển Validator Henssge, viết Unit Test, dựng khung benchmark $\rightarrow$ **Đã hoàn thành 100%**.
* **Tuần 9 - 12 (Tháng 3):** Tích hợp Web Fullstack, hoàn thiện Gameplay đối chất, tổ chức Playtest (5-10 người) $\rightarrow$ *Kế hoạch sắp tới*.
* **Tuần 13 - 16 (Tháng 4):** Chạy Benchmark định lượng ($N=30$), viết hoàn thiện Quyển Báo cáo Đồ án, đóng gói Docker Compose và bảo vệ $\rightarrow$ *Kế hoạch sắp tới*.

---

# 8. KẾ HOẠCH TRIỂN KHAI 2 THÁNG TIẾP THEO

* **Tháng 3 (Tuần 9 – 12):**
  * Ghép nối Frontend ReactJS với API FastAPI hoàn chỉnh.
  * Triển khai form Cáo buộc (`/api/case/verify`) chấm điểm suy luận dựa trên việc chọn đúng hung thủ và bằng chứng then chốt.
  * Mời 5–10 người chơi thử (Playtest) và khảo sát theo thang đo chuẩn **SUS**.
* **Tháng 4 (Tuần 13 – 16):**
  * Chạy thực nghiệm định lượng ($N=30$ vụ án) đo tỷ lệ vượt lỗi logic.
  * Viết toàn văn Báo cáo Đồ án tốt nghiệp (4 chương).
  * Chuẩn bị Slide và kịch bản Demo trực tiếp trước Hội đồng.

---

# 9. ĐỀ XUẤT & XIN Ý KIẾN HƯỚNG DẪN CỦA GVHD

Sinh viên kính mong Thầy Tánh cho ý kiến định hướng về:

1. **Cỡ mẫu thực nghiệm định lượng:** So sánh Baseline vs Pipeline trên $N=30$ vụ án có đủ tính thuyết phục về mặt thống kê cho Hội đồng không ạ?
2. **Bộ tiêu chí đánh giá trải nghiệm:** Thầy có gợi ý thêm tiêu chí nào về tính "Fair-play" và tính tự nhiên của kịch bản ngoài thang đo khả dụng SUS không ạ?
3. **Cấu trúc quyển báo cáo:** Định hướng phân bổ số trang cho 4 chương để cân đối giữa hàm lượng nghiên cứu AI và sản phẩm ứng dụng.

---

# XIN TRÂN TRỌNG CẢM ƠN THẦY!
### Kính chúc Thầy nhiều sức khỏe và công tác tốt.

**Nguyễn Ngọc Công Anh** – Lớp K16-KHMT(AI&KHDL)
*Trường Đại học Phenikaa*
