# Bàn giao: các vấn đề còn tồn đọng, hướng xử lý và cách kiểm tra

Cập nhật: 25/11/2026 — nhánh `v1-clean`. Tài liệu này dành cho người/agent tiếp tục đồ án
(Antigravity, Gemini, Claude…). **Đọc hết mục 0 trước khi sửa bất cứ thứ gì.**

---

## 0. Quy tắc bắt buộc (vi phạm là hỏng đồ án)

1. **Không bao giờ viết số liệu không có trong file kết quả thô.** Mọi con số ở Chương 4, slide,
   README, bảng giải trình phải tính lại được từ `detective-backend/*_results*.json`.
   Trước đây báo cáo từng có số bịa ("22 sinh viên/44 phiên", "285 token", "N=30" khi chỉ có 9 lượt,
   "lệch 15,8 h", "91,3%", SUS 88,6…) — đều đã bị gỡ. GVHD tự tính lại số liệu từ JSON.
2. **Mọi thay đổi số liệu đi kèm cập nhật `detective-backend/verify_results.py`** (bảng `EXPECTED`)
   và chạy lại script; script phải in toàn `OK`.
3. **Kết quả chưa đạt thì ghi là chưa đạt.** L1 (P50 ≤ 20 s) và C1 (≤ 500 token/lượt vá) hiện CHƯA ĐẠT.
4. **Không trộn dữ liệu của hai phiên bản code** vào một dòng bảng. Mỗi file kết quả phải chạy liên tục
   trên một phiên bản; khi sửa prompt/agents thì chạy lại từ đầu vào file mới.
5. **Không để hai agent cùng chạy/ghi file một lúc.** Ngày 24/11 một agent khác chạy song song đã ghi đè
   `benchmark_results.json` và sửa lén Chương 4 → phải khôi phục.
6. **Kiểm tra `agent_models` sau mỗi lần chạy.** Khi API bị giới hạn (HTTP 429), code tự chuyển sang mô hình
   dự phòng mà vẫn ghi tên mô hình chính ở cột `model`. Lượt nào có `agent_models` khác mô hình chính
   thì không được tính vào dòng của mô hình đó.
7. **Sửa LaTeX bằng shell heredoc rất dễ hỏng**: `\\` bị nuốt thành `\`, `\t` trong `\texttt` biến thành
   ký tự TAB. Dùng file script riêng (hoặc công cụ Edit), sau đó chạy `grep -c $'\t' chapters/*.tex` (phải = 0)
   và biên dịch lại.
8. Văn phong theo `AGENTS.md`: không "tuyệt đối/hoàn hảo/vượt trội/triệt để/chúng tôi", dùng dấu phẩy thập phân.

### Vị trí tài liệu (thesis không nằm trong git)

| Thứ | Đường dẫn (máy tác giả) | Trong git? |
|---|---|---|
| Mã LaTeX báo cáo | `thesis_latex/` (`chapters/*.tex`, `references.bib`, `figures/`) | Không (bị ignore) |
| PDF báo cáo nộp | `BAO_CAO_DO_AN_TOT_NGHIEP_22010201.pdf` (= `thesis_latex/main.pdf`) | Không |
| Slide bảo vệ | `BAO_VE_DO_AN_TOT_NGHIEP.pptx` | Không |
| Bảng giải trình GVHD | `GIAI_TRINH_GOP_Y_GVHD_22010201.docx` | Không |
| Bản cũ để đối chiếu | `_ban_cu/` | Không |
| File `BAO_CAO_LUAN_VAN_TOT_NGHIEP_22010201.pdf` | bản CŨ, tên sai "luận văn" — **không gửi** | Không |

Biên dịch: `cd thesis_latex && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`,
rồi `cp main.pdf ../BAO_CAO_DO_AN_TOT_NGHIEP_22010201.pdf`. Biểu đồ: `python thesis_latex/generate_thesis_charts.py`
(đọc trực tiếp JSON — không gõ số tay vào script).

---

## 1. Kiểm tra nhanh toàn bộ (chạy trước và sau mỗi lần sửa)

```bash
# 1) Kiểm thử phần mềm — kỳ vọng: 89 passed
cd detective-backend && python -m pytest -q && cd ..

# 2) Số liệu báo cáo khớp dữ liệu thô — kỳ vọng: toàn OK, exit 0
python detective-backend/verify_results.py

# 3) Không còn bí mật trong mã nguồn — kỳ vọng: không in gì
git grep -nE "hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{10,}|github_pat_" -- . ':!*.md'

# 4) Không còn cụm từ/số liệu cũ trong báo cáo — kỳ vọng: không in gì
grep -nE "82/82|DETECTIVE_HMAC|15[.,]8 ?h|91[.,]3|2\.5D|O\(1\)|97[.,]7|N=44|20[.,]45|285[.,]0|76[.,]84|64[.,]74|khóa luận|Cán bộ hướng dẫn|X-Detective|NetworkX|tuyệt đối|hoàn hảo|vượt trội|triệt để" thesis_latex/chapters/*.tex
#    (chỉ được phép còn: "độ chính xác tuyệt đối" ở mục Wilson — dùng theo nghĩa kỹ thuật)

# 5) LaTeX sạch — kỳ vọng: 0 lỗi, không có "undefined"
cd thesis_latex && pdflatex -interaction=nonstopmode main.tex >/dev/null; grep -cE "^! " main.log; grep undefined main.log; cd ..

# 6) Không có ký tự TAB lạc trong LaTeX — kỳ vọng: toàn :0
grep -c $'\t' thesis_latex/chapters/*.tex
```

Slide: mở bằng PowerPoint hoặc xuất ảnh từng trang (COM `Slide.Export`) và **nhìn** — nhiều khung chữ
không đặt cỡ chữ nên khi đổi nội dung dài hơn sẽ tràn/đè lên hình (đã sửa slide 4, 9, 15, 17, 18, 19, 21).

---

## 2. Vấn đề còn tồn đọng

Mức độ: **[Cao]** = ảnh hưởng điều kiện bảo vệ (GVHD yêu cầu A1, A2, B2, C1), **[Vừa]** = nên làm,
**[Thấp]** = cải thiện.

### 2.1 [Cao] GPT-4o chưa chạy lại đủ 30 lượt trên mã nguồn hiện tại
- **Hiện trạng:** Bảng 4.1 dùng `benchmark_results_gpt4o.json` (30 lượt, chạy TRƯỚC khi sửa lỗi prompt
  ClueAgent — báo cáo đã ghi rõ). Lượt chạy lại `benchmark_results_gpt4o_v2.json` dừng ở 18/30 (thiếu chủ đề
  CyberTech 10 lượt, Tàu đêm 2 lượt) vì GitHub Models trả 429 cho `gh/gpt-4o`.
- **Xử lý:** khi hạn mức hồi (thường sau 24 h), chạy tiếp — script tự đọc file và chỉ chạy phần thiếu:
  ```bash
  python detective-backend/benchmark_runner.py --mode benchmark --models gh/gpt-4o \
      --trials-per-theme 10 --delay 10 --output-benchmark detective-backend/benchmark_results_gpt4o_v2.json
  ```
  Nếu log in `Rate limited (429) … attempt 5/8` thì **dừng tiến trình ngay** (trước attempt 8, code sẽ
  chuyển sang mô hình dự phòng và làm bẩn file).
- **Sau khi đủ 30 lượt sạch:** thay dòng gpt-4o trong Bảng 4.1 (Mục 4.3), dòng "Tổng hợp đám mây (N=60)",
  câu ghi chú phiên bản ở đầu Mục 4.3, slide 18/19, README, bảng giải trình (mục A2) và `EXPECTED` trong
  `verify_results.py`. Vẽ lại biểu đồ: `generate_thesis_charts.py` đang đọc `benchmark_results_gpt4o.json` —
  đổi sang file v2.
- **Kiểm tra:** `verify_results.py` in `gpt4o_v2 agent_models: {('gh/gpt-4o',): 30}`; đủ 10 lượt mỗi chủ đề.

### 2.2 [Cao] Solver Agent (mục A4) đo khi tác tử còn thấy cờ `is_weapon`
- **Hiện trạng:** `solver_benchmark_results.json` (19/20) được đo khi `ClientEvidence` còn trường
  `is_weapon` (đánh dấu hung khí) và prompt solver in ra trường này. Đã gỡ cả hai (commit `d16e47e`),
  báo cáo Mục 4.8 có ghi chú "kết quả có thể lạc quan". Lượt chạy lại ngày 25/11 đang/đã chạy — kiểm tra
  `solver_run.log`.
- **Xử lý:** `python detective-backend/solver_agent.py --cases 20` (gpt-4o-mini). Script lấy hồ sơ hợp lệ
  trong `detective.db`, thiếu thì tự sinh thêm.
- **Kiểm tra kết quả mới trước khi dùng:**
  - `cases` trong JSON không có `case_id` trùng nhau, không có hồ sơ mẫu `CASE-2026-001` lặp lại
    (khi sinh lỗi, `generate_case` trả hồ sơ mẫu dự phòng);
  - hồ sơ sinh mới không dùng mô hình dự phòng (xem `metadata.agent_models` trong `detective.db`).
- **Cập nhật:** Mục 4.8 (Bảng `tab:solvability_comparison`, phân tích ca thất bại), slide 20, README,
  giải trình A4, `EXPECTED`. Bỏ câu "kết quả có thể lạc quan" khi đã có kết quả mới. Nếu tỷ lệ giảm thì
  báo cáo đúng con số mới — đó là kết quả trung thực hơn.

### 2.3 [Vừa] gemma4 cục bộ thực chất là hệ lai cục bộ–đám mây
- **Hiện trạng:** cả 23 lượt `benchmark_results_gemma4_local.json` có `CharacterAgent` và `ClueAgent`
  chuyển sang `gh/gpt-3.5-turbo` (22) / `gh/gpt-4o-mini` (1). Báo cáo đã ghi đúng là "hệ lai, chưa chứng minh
  chạy hoàn toàn ngoại tuyến". Dữ liệu chạy trước khi sửa prompt ClueAgent.
- **Xử lý (nếu muốn có kết quả cục bộ thật):** tìm vì sao gemma4 lỗi ở hai tác tử (thường do JSON dài/timeout):
  tăng `num_ctx` của Ollama, tăng timeout, hoặc tạm tắt chuỗi dự phòng khi benchmark cục bộ
  (`BaseAgent.FALLBACK_CANDIDATES` trong `agents.py`) để lượt lỗi được ghi là lỗi thay vì bị thay mô hình.
  Mỗi lượt ~20 phút; 30 lượt ≈ 10 giờ.
- **Kiểm tra:** `agent_models` của mọi lượt chỉ chứa `gemma4:e4b-it-qat`. **Tuyệt đối không bịa số gemma.**

### 2.4 [Vừa] Thủ phạm luôn là "nhân vật thứ hai" và giờ gây án dồn về 21:30
- **Hiện trạng:**
  - LLM chọn `SUSP-02` làm thủ phạm 28/30 (mini), 26/30 (gpt-4o). Đã thêm `id_shuffle.py`: ở
    `POST /api/case/generate`, code hoán vị ngẫu nhiên mọi mã `SUSP-xx` (thuần code, `random.SystemRandom`)
    nên người chơi gặp thủ phạm phân bố đều. **Nhưng đây chỉ là đổi tên** — nội dung vẫn là nhân vật thứ hai
    do LLM viết. Benchmark vẫn đo đầu ra thô (đúng, không sửa).
  - Câu ví dụ "(ví dụ 21:30)" trong `_get_mystery_style_mechanic` (agents.py) và giá trị mặc định
    `mid_str = "21:30"` trong `repair_tod` khiến 23/30 hồ sơ mini có giờ gây án 21:30.
- **Xử lý (làm cùng lúc, rồi chạy lại toàn bộ benchmark):**
  1. Xóa mốc giờ ví dụ cụ thể khỏi `_get_mystery_style_mechanic` (thay bằng "một mốc giờ muộn hơn giờ tử vong").
  2. Trong `OutlineAgent.generate`, để code chọn trước `culprit_id = random.choice([...])` và một khung giờ
     gây án ngẫu nhiên trong [19:30; 23:00], đưa vào prompt như ràng buộc; sau khi LLM trả về, nếu lệch thì
     ghi đè. Ghi rõ trong báo cáo đây là lựa chọn của mã nguồn (không phải "LLM tự sinh").
  3. Chạy lại mini 30 lượt (và gpt-4o nếu có hạn mức) vào file mới; cập nhật Mục 4.3.3, 5.3, slide 12/23.
- **Kiểm tra:** `verify_results.py` in phân bố thủ phạm ≈ 10/10/10 và giờ gây án trải đều; ≥ 28/30 vẫn hợp lệ.

### 2.5 [Vừa] Chưa có nhánh vá cho phân hệ suy luận (reasoning)
- **Hiện trạng:** validator phát hiện "Reasoning step N cites non-existent clue ID" nhưng `llm_service.py`
  không định tuyến vi phạm `component == "reasoning"` tới tác tử nào. Toàn bộ 11/11 ca thất bại nhóm 3 và
  8/8 ca thất bại nhóm 4 trong tiêm lỗi là do lỗi này. Đây là lý do tỷ lệ vá chung chỉ 63,8%.
- **Xử lý:** sau khi `repair_clues` chạy, gọi lại `DeductionAgent.generate` (hoặc thêm `repair_reasoning`)
  để sinh lại chuỗi suy luận theo danh sách vật chứng mới; thêm nhánh `elif violation.component == "reasoning"`.
  Chạy lại `python detective-backend/fault_injection_runner.py --trials 20` vào file mới.
- **Kiểm tra:** tỷ lệ vá nhóm 3/4 tăng; cập nhật Bảng 4.5, Hình 4.4 (vẽ lại), Mục 4.7, 5.3, slide 14/20/21.

### 2.6 [Vừa] Hàm chấm điểm có thể bị lạm dụng bằng từ khóa
- **Hiện trạng:** `evaluate_player_deduction` (validator.py ~dòng 532–620): nếu người chơi không chọn vật chứng
  then chốt nhưng lập luận văn bản khớp ≥ 2 nhóm từ khóa ("giờ", "lời khai", "vật chứng"…) thì vẫn được
  `crucial_score = 35` và có thể thành SOLVED. Báo cáo đã ghi là hạn chế (Mục 3.4, Bảng Knox Điều 6, Mục 5.3).
- **Xử lý:** yêu cầu ít nhất một vật chứng then chốt được chọn để đạt SOLVED; điểm lập luận chỉ là thưởng.
  Thêm test: chọn đúng thủ phạm + 0 vật chứng + văn bản nhồi từ khóa ⇒ không SOLVED.
- **Kiểm tra:** `pytest test_validator.py`; sửa lại công thức Verdict ở Mục 3.4 cho khớp code.

### 2.7 [Vừa] Kiểm tra đồ thị hai phía không thêm thông tin
- **Hiện trạng:** cạnh `contradicts` được suy ra từ cờ `is_crucial` (case_graph.py ~dòng 115), nên khi đã qua
  `NO_CRUCIAL_CLUE` thì kiểm tra đồ thị không thể thất bại. Báo cáo đã ghi đúng (Mục 3.8, 5.3); ST-CSP ở
  Mục 2.4.4 chỉ là định hướng.
- **Xử lý (nếu muốn nâng cấp):** hình thức hóa lời khai thành khoảng thời gian–địa điểm, vật chứng thành
  ràng buộc loại trừ, kiểm tra tính duy nhất của thủ phạm bằng Z3. Hoặc giữ nguyên và chỉ trình bày như hạn chế.
- **Kiểm tra:** không viết "chứng minh tính giải được" ở bất kỳ đâu khi chưa có bộ giải.

### 2.8 [Vừa] Nghiên cứu loại trừ cỡ mẫu nhỏ
- **Hiện trạng:** `ablation_results.json` chỉ 3 lượt/cấu hình (chạy trước khi sửa prompt ClueAgent);
  đối chứng một lần gọi E2E-plan 9 lượt (`e2e_plan_baseline_results.json`, mã nguồn mới). Có thêm
  `ablation_results_n9.json` (36 lượt, do agent khác chạy, KHÔNG có trong git, không dùng trong báo cáo).
- **Xử lý:** chạy lại ≥ 10 lượt/cấu hình trên mã nguồn hiện tại:
  `python detective-backend/benchmark_runner.py --mode ablation --ablation-trials 4 --output-ablation detective-backend/ablation_results_v2.json`
  và `python detective-backend/run_e2e_baseline.py --trials-per-theme 4`.
- **Kiểm tra:** cập nhật Bảng 4.2, Wilson CI, `EXPECTED`. Ghi chú: cấu hình 2–4 khó phân biệt vì không phát sinh lỗi tự nhiên.

### 2.9 [Thấp] Tiêu chí L1, C1 chưa đạt
- L1: P50 23,23 s > 20 s. Hướng: chạy song song `CharacterAgent` và phần dựng khung vật chứng; sinh trước kho hồ sơ.
- C1: 4.227,6 token/lượt vá > 500. Hướng: chỉ gửi phần hồ sơ liên quan tới vi phạm cho hàm vá.
- **Không đổi ngưỡng thiết kế để "đạt"** — ngưỡng đã ghi trong Bảng 3.2 trước khi đo.

### 2.10 [Thấp] Chưa có thử nghiệm người chơi
- Bảng `deduction_logs` chỉ chứa bản ghi của bộ test và Solver. Nếu làm: ≥ 10 người, mỗi người 2 vụ,
  ghi `session_id` thật, đo tỷ lệ giải đúng, thời gian, khảo sát SUS; lưu file kết quả riêng có ngày giờ.
  Chưa làm thì giữ nguyên câu "chưa có thử nghiệm người chơi" trong báo cáo.

### 2.11 [Thấp] Bảo mật còn hở khi phát hành công khai
- WebSocket `/ws/rooms/{id}` không xác thực và đi ngoài middleware HMAC; CORS mặc định cho mọi origin
  (không kèm credentials) khi chưa đặt `CORS_ORIGINS`. Đã ghi trong Mục 3.11. Khi đưa lên Internet:
  thêm token phiên cho WebSocket, đặt `ALLOW_ALL_ORIGINS=false` và `CORS_ORIGINS`, dùng WSS/TLS.

### 2.12 [Thấp] Dữ liệu cũ trong `detective.db`
- 16/23 hồ sơ trong bảng `cases` không còn hợp lệ theo bộ kiểm định hiện tại (lời khai nghi phạm < 6 từ,
  hồ sơ ngày 7–16/11). Không ảnh hưởng báo cáo; nếu Solver thiếu hồ sơ thì nó tự sinh thêm.
  `detective.db` không nằm trong git.

### 2.13 [Thấp] LaTeX
- 5 cảnh báo `Overfull \hbox` (bảng rộng). Không phải lỗi; chỉnh độ rộng cột nếu muốn.
- Dấu thập phân: phần văn bản đã đổi sang dấu phẩy ở các bảng/đoạn đã sửa; công thức toán giữ dấu chấm.

---

## 3. Trạng thái các mục GVHD yêu cầu (phiếu 19/11/2026)

| Mục | Trạng thái | Bằng chứng |
|---|---|---|
| C1 bí mật | Xong | Lịch sử git sạch (`git log --all -p -S hf_` rỗng), token HF đã thu hồi, không còn khóa mặc định |
| B2 tách đáp án | Xong | `ClientCaseDossier` (không `ground_truth`, `is_culprit`, `is_crucial`, `is_red_herring`, `is_weapon`), `/internal` & `/graph` cần `INTERNAL_API_TOKEN`, HTTP 422 cho hồ sơ lỗi; `test_client_isolation.py` |
| A2 thống kê | Xong một phần | mini 30 lượt mã mới; gpt-4o 30 lượt mã cũ + 18 lượt mã mới (mục 2.1) |
| A1 đối chứng | Xong một phần | Ablation N=3 + E2E-plan 9 lượt; đa dạng nội dung còn yếu (mục 2.4, 2.8) |
| A3 vá lỗi | Xong | Tiêm lỗi 80 ca; C1 ghi CHƯA ĐẠT; còn thiếu nhánh vá reasoning (mục 2.5) |
| A4 khả giải | Xong một phần | Solver 19/20 có ghi chú lạc quan; đang chạy lại (mục 2.2) |
| B1, B3, C2, D1, E | Xong | Xem `GIAI_TRINH_GOP_Y_GVHD_22010201.docx` |

## 4. Thứ tự đề xuất cho phiên làm việc tiếp theo

1. Chạy mục 1 (kiểm tra nhanh) — mọi thứ phải xanh trước khi bắt đầu.
2. Hoàn tất 2.2 (Solver) và 2.1 (gpt-4o) khi có hạn mức → cập nhật báo cáo/slide/giải trình → mục 1 lại.
3. Nếu còn thời gian trước bảo vệ: 2.5 (nhánh vá reasoning) rồi 2.4 (bỏ mốc 21:30, code chọn thủ phạm/giờ),
   mỗi việc kèm chạy lại benchmark tương ứng.
4. Sau mỗi thay đổi: commit riêng, ghi mã commit vào Phụ lục A.3 của báo cáo và bảng giải trình
   Bảng giải trình được sinh bằng `python tools/make_giai_trinh.py "<thư mục repo>" <mã commit>`: script đọc
   số liệu mini/gpt-4o trực tiếp từ JSON, phần văn bản các mục nằm trong script — sửa ở đó rồi chạy lại.
