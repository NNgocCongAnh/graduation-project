# THESIS CONTEXT & ARCHITECTURAL INVARIANTS: AI DETECTIVE GAME ENGINE

## 1. Project Overview & Core Concept
* **Topic:** Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng Mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán.
* **Format:** Web-based Detective Noir Game (Locked-room mystery). Người chơi đóng vai thám tử phân tích hồ sơ hiện trường, đối chiếu lời khai và dữ kiện pháp y trên Bảng điều tra (Corkboard) để tìm ra hung thủ.
* **Target Platforms:**
  * Backend: Python 3.11+ (FastAPI, Pydantic v2, Uvicorn, PostgreSQL/SQLite, Docker).
  * Client: Unity (Build Target: WebGL) / React kết nối REST API Backend.

---

## 2. Core Problem & Technical Innovation
* **Anti-Pattern (Single-Prompt Baseline):** Sinh toàn bộ vụ án bằng 1 prompt đơn lẻ dẫn đến: vỡ định dạng JSON (~70% lỗi cú pháp), ảo giác phi logic (sai lệch mốc thời gian chết, vật chứng mâu thuẫn vô lý), kịch bản quá dễ hoặc không thể giải được.
* **Proposed Solution (Sequential 4-Step Pipeline):**
  1. **Step 1 - Victim & Forensics:** Sinh nạn nhân, hiện tượng sinh học (nhiệt độ tử thi, hoen ố, co cứng). *Lưu ý: KHÔNG sinh trực tiếp giờ chết.*
  2. **Step 2 - Suspects & Alibis:** Sinh 2-3 nghi phạm, nghề nghiệp, động cơ, alibi thời gian; âm thầm gắn cờ 1 hung thủ (`is_culprit: true`).
  3. **Step 3 - True Timeline:** Sinh dòng thời gian thực tế xảy ra án mạng.
  4. **Step 4 - Evidences:** Sinh vật chứng hiện trường ăn khớp với vết thương/cơ chế tử vong và mốc thời gian thực.

* **Rule-based Validator (`validator.py`):**
  * Kiểm tra tính hợp lệ JSON Schema (100% Pydantic validation).
  * Tính toán khoảng thời gian tử vong sinh học từ dữ kiện pháp y Step 1.
  * Cố tình cài cắm **mâu thuẫn gián tiếp (Indirect Ambiguity / Solvable Contradiction)**: Alibi của hung thủ lệch pha so với kết quả pháp y / vật chứng then chốt; các nghi phạm vô tội có alibi hợp lệ hoặc chỉ có thông tin gây nhiễu (Red Herrings).
  * Tự động gọi lại LLM sửa lỗi (Retry qua `tenacity`) nếu phát hiện mâu thuẫn phi logic trước khi trả về Client.

---

## 3. Thesis Objectives & Evaluation Metrics
1. **Objective 1 (Baseline & Infrastructure):** Dựng Docker, FastAPI, CSDL, tập vụ án mẫu (Seed Cases) và chạy đánh giá benchmark phương pháp Single-Prompt cũ (đo tỷ lệ lỗi JSON & mâu thuẫn logic).
2. **Objective 2 (Pipeline, Validator & Game Client):** Hoàn thiện Sequential Pipeline, Rule-based Validator và Client Game (Unity WebGL / React) với các tính năng:
   * Interactive Corkboard (Bảng ghim điều tra).
   * Thẻ nghi phạm Polaroid & Thẻ tang vật có hiệu ứng tương tác.
   * Dây chỉ đỏ nối liên kết logic giữa các manh mối.
   * Modal hồ sơ chi tiết độc lập từng đối tượng.
3. **Objective 3 (Quantitative Evaluation):**
   * **JSON Validity Rate:** Baseline (~60-70%) vs Proposed Pipeline (100%).
   * **Logic Contradiction Rate:** Baseline (~30-40%) vs Proposed Engine (~0%).
   * **Solvability Rate:** Vụ án sinh ra có thể phá án bằng logic đạt >85%.

---

## 4. API Endpoints & Schemas Invariant
Backend cung cấp các REST API endpoints chính:
* `GET /api/case/sample` -> Trả về JSON vụ án mẫu (Seed case) để test offline.
* `POST /api/case/generate` -> Kích hoạt Sequential Pipeline + Validator để tạo vụ án mới.
* `POST /api/case/verify` -> Nhận `{ case_id, suspect_id, reasoning_evidence_ids }` để kiểm tra kết quả phá án của người chơi.

### Case Dossier Schema Standard:
```json
{
  "case_id": "CASE-2026-001",
  "title": "Bí ẩn Biệt thự Blackwood",
  "summary": "Vụ án mạng trong phòng kín tầng 2 biệt thự cổ.",
  "victim": {
    "name": "Arthur Blackwood",
    "age": 62,
    "occupation": "Doanh nhân",
    "forensic_notes": "Tử thi hạ nhiệt độ còn 31.2°C (môi trường 22°C), hoen tử thi cố định ở lưng. Vết đâm ngực."
  },
  "suspects": [
    {
      "id": "SUSP-01",
      "name": "Quản gia William",
      "age": 55,
      "occupation": "Quản gia",
      "alibi": "Khai rằng từ 21:00 đến 22:30 ở dưới bếp một mình.",
      "is_culprit": true
    }
  ],
  "evidences": [
    {
      "id": "EV-01",
      "title": "Mặt kính đồng hồ vỡ",
      "location": "Gầm bàn làm việc",
      "description": "Đồng hồ bỏ túi bị vỡ, kim dừng lại ở mốc 21:40.",
      "is_crucial": true
    }
  ]
}
```
