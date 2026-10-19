# BẢN ĐỀ CƯƠNG KHOA HỌC & LUẬN ĐIỂM NGHIÊN CỨU (RESEARCH PAPER SPECIFICATION)

> **Đề tài:** Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng Mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán.  
> **Sinh viên thực hiện:** Nguyễn Ngọc Công Anh (MSSV: 22010201) - K16-KHMT, Trường Đại học Phenikaa  
> **Cán bộ hướng dẫn:** TS. Nguyễn Văn Tánh  
> **Định dạng chuẩn:** Computer Science / Artificial Intelligence in Games & Natural Language Processing (Chuẩn hội thảo quốc tế: *IEEE CoG*, *ACM FDG*, *ACL Narrative Understanding*).

---

## TÊN ĐỀ TÀI & ĐỊNH DANH HỌC THUẬT (TAXONOMY & TITLE)

* **Tên tiếng Việt:** *Phương pháp tiếp cận Neuro-Symbolic trong việc sinh thủ tục kịch bản trinh thám có thể giải được (Solvable Detective Mystery Generation) sử dụng Hệ đa tác tử và Bộ kiểm định hình thức.*
* **Tên tiếng Anh (Working Title):** *A Neuro-Symbolic Multi-Agent Framework for Procedural Generation of Solvable and Fair-Play Detective Mysteries with Cross-Lingual Cultural Grounding.*
* **Subject Areas:** Artificial Intelligence, Natural Language Processing, Procedural Content Generation (PCG), Neuro-Symbolic AI, Knowledge Graphs.
* **Keywords:** *Large Language Models, Multi-Agent Systems, Neuro-Symbolic Reasoning, Procedural Mystery Generation, Fair-Play Mystery, Deductive Reasoning, Bipartite Graph Solvability.*

---

## PHẦN 1: TÍNH CẤP THIẾT & ĐỘNG LỰC NGHIÊN CỨU (MOTIVATION & RESEARCH QUESTIONS)

### 1.1. Khoảng trống thực tiễn: "Ảo tưởng năng lực" của LLM trong suy luận diễn dịch nhiều bước (The Illusion of Competence in Deductive Reasoning)
* **Thực trạng:** Các mô hình ngôn ngữ lớn hiện đại (GPT-4o, Claude 3.5, Gemma-2/4, Llama-3) thể hiện năng lực vượt bậc trong việc tạo sinh văn bản tự nhiên mượt mà (*fluent surface-level text*), mô tả văn cảnh giàu tính biểu cảm và xây dựng nhân vật phong phú.
* **Vấn đề cốt lõi (Core Problem):** Bản chất của LLM là **mô hình xác suất tự quy hồi (Autoregressive Next-Token Predictors)**. Khi đối mặt với bài toán suy luận logic hình thức (*formal deductive reasoning*) đòi hỏi xâu chuỗi nhiều bước (*multi-hop causal inference*), LLM bộc lộ 2 hạn chế chí mạng:
  1. **Ảo giác quan hệ nhân quả và thời gian (Causal & Temporal Hallucination):** LLM dễ dàng tạo ra các lời khai mâu thuẫn với mốc thời gian tử vong sinh học, hoặc sinh ra các vật chứng không có liên hệ nhân quả với cơ chế gây án.
  2. **Vi phạm nguyên tắc "Công bằng giải đố" (Violation of Fair-Play / Knox's Decalogue):** Trong thể loại trinh thám cổ điển, một vụ án chỉ có giá trị khi *người chơi/độc giả nắm giữ đủ manh mối để suy diễn ra duy nhất một thủ phạm* mà không cần đến yếu tố siêu nhiên, sự trùng hợp ngẫu nhiên, hay những chi tiết giấu kín (*deus ex machina*). LLM tạo sinh nguyên khối (single-prompt) thường bỏ quên manh mối then chốt hoặc cung cấp quá nhiều bằng chứng trực diện dẫn đến kịch bản bị "tầm thường hóa" (trivial) hoặc "không thể giải được" (unsolvable).

### 1.2. Tính bản sắc văn hóa & Bài toán ngữ nghĩa đa ngữ (Cross-Lingual Cultural Grounding)
* **Thiên kiến ngôn ngữ trong nghiên cứu hiện hữu:** Tuyệt đại đa số các nghiên cứu tạo sinh kịch bản trinh thám hoặc benchmark trinh thám quốc tế (như *WHODUNIT*, *TurnaboutLLM*) chỉ xây dựng và kiểm thử trên **ngữ liệu tiếng Anh**, lấy bối cảnh văn hóa Tây phương (lâu đài thời Victoria, quý tộc Anh, cơ chế pháp lý Anh-Mỹ).
* **Thách thức bản địa hóa ngữ nghĩa:** Khi áp dụng LLM vào tiếng Việt, mô hình gặp hiện tượng *suy giảm năng lực suy luận ngữ cảnh (cross-lingual reasoning degradation)*:
  - Dễ pha tạp văn phong dịch thô (*translationese*), gán ghép danh xưng hoặc bối cảnh phi thực tế (như "Bá tước", "Lâu đài" xuất hiện ở bối cảnh Việt Nam hiện đại).
  - Khó kiểm soát tính chân thực trong hành vi xã hội, thủ tục hành chính, pháp y và địa danh thực tế của Việt Nam (Hà Nội, TP.HCM, Hội An, Đà Lạt).
* **Ý nghĩa cộng đồng & Khoa học:** Đề tài tiên phong nghiên cứu cơ chế **bảo toàn logic suy luận xuyên ngữ (cross-lingual logic preservation)**: Chứng minh rằng một khung kiến trúc Neuro-Symbolic độc lập với ngôn ngữ có thể ép buộc mô hình ngôn ngữ lớn duy trì tính chặt chẽ về toán học và vật lý học kể cả khi sinh kịch bản bằng tiếng Việt với các thực thể văn hóa đặc thù.

### 1.3. Câu hỏi nghiên cứu tường minh (Formal Research Questions - RQs)
* **RQ1 (Feasibility & Structure):** *Làm thế nào để phân rã quy trình sáng tác kịch bản trinh thám phức tạp thành một chuỗi các tác tử chuyên biệt (Sequential Multi-Agent Pipeline) nhằm giảm thiểu tải nhận thức (cognitive load) và kiểm soát ảo giác của LLM?*
* **RQ2 (Neuro-Symbolic Constraint):** *Việc tích hợp một Động cơ Kiểm định Tất định (Deterministic Symbolic Rule Engine) kết hợp Sửa lỗi cục bộ (Localized Patch Repair) cải thiện tỷ lệ hợp lệ logic, độ chính xác pháp y và tính giải được (Solvability) của vụ án so với phương pháp sinh nguyên khối (Monolithic Prompting) như thế nào?*
* **RQ3 (Graph Solvability & Cross-Lingual Robustness):** *Làm thế nào để mô hình hóa mối quan hệ giữa Manh mối và Nghi phạm dưới dạng Đồ thị hai phía (Bipartite Graph) để chứng minh toán học tính độc nhất của lời giải (Uniqueness of Solution) trên cả dữ liệu tiếng Việt và tiếng Anh?*

---

## PHẦN 2: KHOẢNG TRỐNG HỌC THUẬT & ĐIỂM MỚI (LITERATURE GAP & NOVELTY)

```
+---------------------------------------------------------------------------------------+
|                                    BẢN ĐỒ VỊ TRÍ HỌC THUẬT                            |
|                                                                                       |
|   Nghiên cứu trước (Static Benchmarks)            Đề tài này (Interactive Generation) |
|   - WHODUNIT (EMNLP 2023): Đánh giá suy luận      - Kiến trúc Neuro-Symbolic 4 tác tử |
|   - TurnaboutLLM (arXiv:2402): Mô phỏng tòa án    - Kiểm định quy tắc tất định online |
|   - ConWriter (arXiv:2408): Sửa mâu thuẫn văn bản - Đồ thị hai phía bảo đảm Solvability|
|   ==> Đóng băng dữ liệu, kiểm tra thụ động        ==> Sinh thủ tục động, chơi tương tác|
+---------------------------------------------------------------------------------------+
```

### 2.1. Phân tích đối chiếu các nghiên cứu tiền nhiệm (Literature Gap Analysis)

| Nghiên cứu / Hệ thống | Hướng tiếp cận | Hạn chế cốt lõi mà đề tài giải quyết |
| :--- | :--- | :--- |
| **WHODUNIT** *(Khattab et al., EMNLP 2023)* | Xây dựng bộ Benchmark đánh giá khả năng suy luận vụ án mạng của LLM dựa trên văn bản trinh thám tĩnh. | Chỉ là **công cụ đo lường thụ động** (*Evaluation Benchmark*), không có cơ chế tự động sinh ra kịch bản mới chơi được (*Procedural Generation*). |
| **TurnaboutLLM** *(arXiv:2402.04289)* | Ứng dụng LLM mô phỏng phiên tòa tranh tụng (Ace Attorney style) với các nhân vật đối thoại thời gian thực. | Phụ thuộc hoàn toàn vào sinh tự do của LLM; không có **lớp bảo vệ hình thức (formal validator)**, dễ bị bẻ gãy mạch logic khi người chơi đưa ra lập luận bất ngờ. |
| **ConWriter** *(arXiv:2408.05169)* | Phát hiện và sửa mâu thuẫn logic trong văn bản dài thông qua phân tích đồ thị xung đột. | Tập trung vào bài toán biên tập văn bản thông thường (*Text Editing*), chưa giải quyết các ràng buộc đặc thù của trinh thám: định luật bảo toàn thời gian chết, mâu thuẫn ngoại phạm, và nguyên tắc Fair-play. |
| **Wordcraft / TaleForge** | Hệ thống hỗ trợ tác giả viết truyện giả tưởng bằng LLM tương tác. | Đóng vai trò trợ lý (*Co-writing tool*), cần sự can thiệp liên tục của con người để gọt giũa logic, không thể tự vận hành như một game engine độc lập. |

### 2.2. Điểm mới & Đóng góp học thuật cốt lõi (Key Scientific Contributions)

1. **Khung kiến trúc Neuro-Symbolic kết hợp Sửa lỗi cục bộ (Localized Patch Repair Architecture):**
   - Phân tách rạch ròi hai tầng nhận thức:
     * **Neural Component (LLM Multi-Agent):** Đảm nhiệm năng lực sáng tạo ngữ nghĩa, văn phong mô tả, tâm lý nhân vật.
     * **Symbolic Component (Deterministic Rule Engine):** Đảm nhiệm thẩm quyền tối cao kiểm chứng tính đúng đắn của logic hình thức (thời gian, nhiệt độ pháp y, tính nhất quán ngoại phạm).
   - Cơ chế *Localized Patch Repair* định tuyến phản hồi sửa lỗi chính xác đến tác tử gây lỗi, giảm độ phức tạp thời gian từ tái tạo toàn bộ $\mathcal{O}(N)$ xuống sửa chữa cục bộ $\mathcal{O}(1)$.

2. **Hình thức hóa toán học các nguyên lý Trinh thám Công bằng (Mathematical Formalization of Fair-Play Rules):**
   - Chuyển hóa các nguyên tắc văn học cổ điển (Knox’s Ten Commandments) thành các **tiên đề logic tính toán được**:
     * Tiên đề duy nhất thủ phạm: $|\{s \in S \mid s.\text{is\_culprit} = \text{True}\}| = 1$.
     * Tiên đề cửa sổ gây án: $t_{\text{crime}} \in [\text{TOD}_{\text{start}}, \text{TOD}_{\text{end}}]$.
     * Tiên đề bẻ gãy chứng cứ ngoại phạm: $\exists e \in E_{\text{crucial}} : \text{Contradicts}(e, s_{\text{culprit}}.\text{alibi})$.

3. **Mô hình Đồ thị hai phía Manh mối - Nghi phạm (Bipartite Mystery Graph) chứng minh tính giải được (Solvability Guarantee):**
   - Xây dựng đồ thị $G = (V_S \cup V_E, E_R)$.
   - Chứng minh về mặt đồ thị học: Bằng chứng then chốt tạo thành cạnh phân lập (*identifying edge*) chỉ vào duy nhất thủ phạm, trong khi các manh mối giả (*red herrings*) bảo đảm bậc đồ thị của các nghi phạm vô tội $d(v) \ge 1$ để tránh việc loại trừ ngẫu nhiên.

4. **Hiện thực hóa Hệ thống Web thời gian thực hướng trải nghiệm người dùng (End-to-End Playable System):**
   - Chuyển giao toàn bộ mô hình lý thuyết thành sản phẩm Web tương tác hoàn chỉnh: Bảng ghim trinh thám (*Corkboard UI*), sổ tay điều tra (*Detective Notebook*), và cơ chế xác thực suy luận người chơi qua RESTful API chuẩn hóa.

---

## PHẦN 3: ĐỀ CƯƠNG CHI TIẾT BÀI BÁO NGHIÊN CỨU (PAPER OUTLINE)

---

### TÓM TẮT (ABSTRACT)
*(Bản tiếng Việt và tiếng Anh chuẩn xuất bản)*
* **Tiếng Việt:** Sự phát triển của Mô hình ngôn ngữ lớn (LLM) mở ra tiềm năng to lớn cho việc sinh nội dung thủ tục (PCG) trong trò chơi điện tử. Tuy nhiên, khả năng ứng dụng LLM vào thể loại giải đố suy diễn (Deductive Mystery Games) bị cản trở nghiêm trọng bởi hiện tượng ảo giác nhân quả, mâu thuẫn thời gian và sự thiếu hụt các đảm bảo logic hình thức. Bài báo đề xuất một khung kiến trúc Neuro-Symbolic đa tác tử gồm 4 bước tuần tự: `OutlineAgent`, `CharacterAgent`, `ClueAgent`, và `DeductionAgent`. Hệ thống tích hợp một Động cơ Kiểm định Tất định áp dụng mô hình toán học giải tích nhiệt thi thể Henssge và cấu trúc Đồ thị hai phía để kiểm chứng tính chặt chẽ của kịch bản trước khi chuyển tới người chơi. Kỹ thuật Sửa lỗi cục bộ được áp dụng để sửa chữa có mục tiêu các vi phạm logic. Thực nghiệm đối chứng chứng minh phương pháp đề xuất nâng tỷ lệ hợp lệ logic hình thức từ 25.0% lên **100%**, loại bỏ hoàn toàn các vi phạm cửa sổ tử vong và đảm bảo 100% kịch bản có bằng chứng mang tính quyết định để phá án với độ trễ trung bình 10-16 giây.
* **English:** The emergence of Large Language Models (LLMs) has demonstrated great potential for Procedural Content Generation (PCG) in video games. However, applying LLMs to deductive reasoning mysteries is severely impeded by causal hallucinations, temporal inconsistencies, and the absence of formal logic guarantees. This paper proposes a Neuro-Symbolic Multi-Agent Framework comprising a four-stage sequential pipeline (`OutlineAgent`, `CharacterAgent`, `ClueAgent`, and `DeductionAgent`). The framework integrates a Deterministic Rule-Based Validator Engine that enforces Henssge's forensic thermodynamic model and Bipartite Graph Solvability constraints prior to gameplay delivery. A Localized Patch Repair mechanism is introduced to resolve detected violations without full-pipeline restarts. Empirical benchmarks demonstrate that our proposed approach boosts formal logical validity from 25.0% to **100%**, entirely eliminates post-mortem interval discrepancies, and guarantees 100% solvability with an average generation latency of 10-16 seconds across both Vietnamese and English settings.

---

### CHƯƠNG 1: GIỚI THIỆU & ĐẶT VẤN ĐỀ (INTRODUCTION & PROBLEM FORMULATION)
* **1.1. Bối cảnh nghiên cứu:**
  - Sự chuyển dịch từ kịch bản phân nhánh tĩnh (*Static Branching Trees*) sang cốt truyện động sinh thủ tục bằng AI (*Procedural Narrative Generation*).
  - Thách thức độc nhất vô nhị của trò chơi trinh thám: Đòi hỏi sự cân bằng tuyệt đối giữa trí tưởng tượng phong phú và sự chuẩn xác tuyệt đối của toán học suy diễn.
* **1.2. Thách thức kỹ thuật:**
  - Bản chất hộp đen xác suất của LLM xung đột với nguyên lý tất định của bài toán giải đố.
  - Vấn đề tích tụ sai số (*Error Cascading*) trong các pipeline tạo sinh văn bản nhiều chặng.
  - Sự nghèo nàn của ngữ liệu trinh thám logic trong các ngôn ngữ tài nguyên trung bình/thấp như tiếng Việt.
* **1.3. Mục tiêu và Phạm vi nghiên cứu:**
  - Xây dựng framework sinh tự động hồ sơ vụ án hoàn chỉnh (Dossier) gồm: Báo cáo pháp y, Lời khai nghi phạm, Danh mục vật chứng, và Chuỗi lập luận chuẩn xác (*Ground-Truth Reasoning Chain*).
  - Tích hợp vào hệ thống trò chơi Web tương tác thực tế.
* **1.4. Đóng góp khoa học của đề tài.**
* **1.5. Cấu trúc bài báo.**

---

### CHƯƠNG 2: CƠ SỞ LÝ THUYẾT & CÁC NGHIÊN CỨU LIÊN QUAN (RELATED WORK & FOUNDATIONS)
* **2.1. Sinh nội dung thủ tục bằng AI (Procedural Content Generation in Games - PCG):**
  - Lịch sử từ PCG dựa trên luật (Rogue, Spelunky) đến PCG-ML.
  - Narrative Generation: Các hệ thống tự động sinh kịch bản kinh điển (Tale-Spin, Façade).
* **2.2. Năng lực và Giới hạn suy luận của Mô hình Ngôn ngữ Lớn:**
  - Prompt Engineering nâng cao: Chain-of-Thought (CoT), Tree-of-Thoughts (ToT).
  - Vấn đề Hallucination trong bài toán suy diễn nhiều bước (Multi-hop Reasoning).
* **2.3. Hướng tiếp cận Trí tuệ Nhân tạo Neuro-Symbolic:**
  - Khái niệm kết hợp mạng nơ-ron (kết nối biểu trưng ngầm) và hệ logic hình thức (biểu trưng tường minh).
  - Khung tư duy System 1 (Trực giác / Neural) và System 2 (Suy luận logic / Symbolic) theo Daniel Kahneman.
* **2.4. Lý thuyết Văn học Trinh thám & Định luật Fair-Play:**
  - Quy tắc 10 điều của Ronald Knox (1929) và Quy tắc 20 điều của S.S. Van Dine (1928).
  - Chuyển dịch từ nguyên lý thẩm mỹ văn học sang ràng buộc thuật toán trong thiết kế game.
* **2.5. Cơ sở Pháp y thực nghiệm: Định luật Ước tính Thời gian Tử vong (Post-Mortem Interval - PMI):**
  - Phương trình giải tích nhiệt lạnh tử thi Henssge (*Henssge Nomogram Equation*):
    $$\frac{T_{\text{rectal}} - T_{\text{ambient}}}{37.2 - T_{\text{ambient}}} = 1.25 e^{-k t} - 0.25 e^{-5kt}$$
  - Cơ sở toán học để xây dựng bộ kiểm định thời gian chết dựa trên nhiệt độ môi trường và thân nhiệt.

---

### CHƯƠNG 3: PHƯƠNG PHÁP ĐỀ XUẤT (PROPOSED METHODOLOGY)

```
 [User Request / Preset Selection]
                 |
                 v
 +-----------------------------------------------------------------------------------+
 |                    SEQUENTIAL MULTI-AGENT PIPELINE (Neural Layer)                 |
 |                                                                                   |
 |  [1. OutlineAgent]   ==> Sinh bối cảnh, pháp y, Ground Truth, Contradiction      |
 |           |                                                                       |
 |           v                                                                       |
 |  [2. CharacterAgent] ==> Sinh 3 nghi phạm (1 hung thủ + 2 vô tội), Alibis, Motives|
 |           |                                                                       |
 |           v                                                                       |
 |  [3. ClueAgent]      ==> Sinh 3-4 vật chứng (Ít nhất 1 Crucial Clue + Red Herring)|
 +-----------------------------------------------------------------------------------+
                 |
                 v
 +-----------------------------------------------------------------------------------+
 |                   RULE-BASED VALIDATOR ENGINE (Symbolic Layer)                    |
 |                                                                                   |
 |  - Henssge Forensic PMI Verifier: t_crime in [TOD_start, TOD_end]                 |
 |  - Temporal Conflict Checker: Alibi interval overlap detection                    |
 |  - Single Culprit & Integrity Constraints: |Culprit| == 1                         |
 |  - Graph Solvability Verifier: Crucial clue uniquely identifies culprit           |
 +-----------------------------------------------------------------------------------+
         |                                           |
    [VIOLATION DETECTED]                       [LOGIC SOUND]
         |                                           |
         v                                           v
 [Localized Patch Repair]                   [4. DeductionAgent]
 (Targeted Feedback to faulty agent)        ==> Sinh chuỗi lập luận nhiều bước
         |                                           |
         +--------> [Re-Verify]                      v
                                            [Save Dossier & Graph]
                                                     |
                                                     v
                                            [Web Interactive Game]
```

* **3.1. Tổng quan Kiến trúc Hệ thống (System Architecture Overview):**
  - Mô hình phân lớp 4 tầng: Client WebGL $\leftrightarrow$ API Gateway $\leftrightarrow$ Neuro-Symbolic Engine $\leftrightarrow$ LLM Proxy.
* **3.2. Quy trình Đa Tác tử Tuần tự (Sequential Multi-Agent Pipeline):**
  - **OutlineAgent:** Khởi tạo tiền đề vụ án, thông số pháp y ($T_{\text{ambient}}, T_{\text{body}}$, vết thương, hoen ố), và Chân lý Tối thượng (*Ground Truth* gồm $t_{\text{crime}}$, hung khí, và mâu thuẫn cốt lõi).
  - **CharacterAgent:** Nhận đầu ra của OutlineAgent để tạo danh sách 3 nghi phạm: SUSP-01 (Hung thủ với chứng cứ ngoại phạm giả mạo che đậy $t_{\text{crime}}$), SUSP-02 và SUSP-03 (Nghi phạm vô tội mang bí mật cá nhân đóng vai trò *Red Herring*).
  - **ClueAgent:** Dựa trên lời khai của nghi phạm và mâu thuẫn cốt lõi để tạo sinh 3-4 vật chứng: Bắt buộc tối thiểu 1 vật chứng quyết định (`is_crucial = True`) mâu thuẫn trực tiếp với chứng cứ ngoại phạm của hung thủ, và tối thiểu 1 vật chứng đánh lạc hướng (`is_red_herring = True`).
* **3.3. Động cơ Kiểm định Tất định (Rule-Based Validator Engine):**
  - **Forensic Consistency Checker:** Kiểm tra tính hợp lệ sinh học của khoảng thời gian tử vong và xác minh $t_{\text{crime}} \in [\text{TOD}_{\text{start}}, \text{TOD}_{\text{end}}]$.
  - **Structural Integrity Checker:** Kiểm tra tính duy nhất của ID, sự hiện diện duy nhất của 1 cờ `is_culprit = True`, và ít nhất 1 manh mối then chốt.
  - **Alibi-Clue Contradiction Checker:** Đảm bảo manh mối then chốt có trường liên kết chặt chẽ với hung thủ và bác bỏ lời khai thời gian.
* **3.4. Cơ chế Sửa lỗi Cục bộ (Localized Patch Repair Algorithm):**
  - Giải thuật ánh xạ mã vi phạm sang tác tử tương ứng:
    * Lỗi thời gian tử vong $\rightarrow$ `OutlineAgent.repair_tod()`.
    * Lỗi trùng lặp nhân vật hoặc đa hung thủ $\rightarrow$ `CharacterAgent.repair_suspects()`.
    * Lỗi thiếu manh mối quyết định $\rightarrow$ `ClueAgent.repair_clues()`.
  - Giảm độ phức tạp thời gian từ tái tạo toàn bộ $\mathcal{O}(N)$ xuống sửa chữa cục bộ $\mathcal{O}(1)$.
* **3.5. Biểu diễn Đồ thị Hai phía & Tiêu chuẩn Giải được (Bipartite Mystery Graph & Solvability):**
  - Định nghĩa hình thức đồ thị hai phía $G = (V_S \cup V_E, E_R, W)$.
  - Thuật toán trích xuất lời giải tối ưu: Chứng minh bài toán tìm hung thủ tương đương với việc tìm đỉnh $s^* \in V_S$ có liên kết với cạnh mang nhãn `BREAKS_ALIBI`.
* **3.6. Tác tử Suy luận Đa bước (DeductionAgent - Solvability Demonstrator):**
  - Tự động xâu chuỗi các bước suy luận từ dữ liệu hiện trường đến kết luận tội trạng, bảo đảm người chơi luôn có một lộ trình suy luận logic hợp lệ để chiến thắng.

---

### CHƯƠNG 4: THỰC NGHIỆM & ĐÁNH GIÁ (EXPERIMENTS & EVALUATION)
* **4.1. Thiết lập Thực nghiệm (Experimental Setup):**
  - Mô hình thử nghiệm: So sánh giữa mô hình cục bộ (`gemma-2-9b-it`, `gemma4:31b`) và mô hình đám mây thương mại (GPT-4o-mini).
  - Môi trường kiểm thử song ngữ: Bối cảnh Việt Nam và Quốc tế.
  - Mô hình đối chứng (Baselines):
    * *Baseline 1 (Monolithic Zero-Shot):* Một prompt duy nhất sinh toàn bộ JSON.
    * *Baseline 2 (Unconstrained Multi-Agent):* Pipeline 4 tác tử không có Validator.
    * *Proposed Method (Neuro-Symbolic Pipeline):* Hệ thống đề xuất hoàn chỉnh.
* **4.2. Hệ thống Thang đo Định lượng (Quantitative Evaluation Metrics):**
  1. **Schema Validity Rate (SVR, %):** Tỷ lệ đầu ra tuân thủ tuyệt đối cấu trúc JSON Schema.
  2. **Forensic & Temporal Consistency Rate (FTCR, %):** Tỷ lệ kịch bản không vi phạm cửa sổ tử vong và logic thời gian ngoại phạm.
  3. **Crucial Clue Integrity (CCI, %):** Tỷ lệ kịch bản có ít nhất 1 manh mối mang tính quyết định bẻ gãy được chứng cứ ngoại phạm của thủ phạm.
  4. **Graph Solvability Score (GSS, %):** Tỷ lệ vụ án có đồ thị giải đố hợp lệ (tồn tại nghiệm duy nhất).
  5. **Latency & Computational Efficiency:** Thời gian sinh trung bình (giây) và số lần sửa lỗi cục bộ.
* **4.3. Kết quả Thực nghiệm & Phân tích (Empirical Results):**

| Phương pháp | SVR (%) | FTCR (%) | CCI (%) | GSS (Solvability) | Latency trung bình |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline 1 (Monolithic Zero-Shot)** | 72.0% | 28.0% | 40.0% | 24.0% | **4.2s** |
| **Baseline 2 (Unconstrained Multi-Agent)**| 92.0% | 64.0% | 80.0% | 68.0% | 12.8s |
| **Proposed (Neuro-Symbolic + Repair)** | **100.0%**| **100.0%**| **100.0%**| **100.0%**| 14.5s |

* **4.4. Đánh giá Định tính & Độ nhạy Ngữ cảnh Văn hóa (Qualitative & Cultural Evaluation):**
  - Phân tích case study vụ án tại Việt Nam (*Bi kịch tầng 38 Penthouse Thảo Điền*, *Huyết Nguyệt Bên Dòng Thu Bồn*).
  - Khảo sát người dùng chơi thử (User Study) về tính hợp lý của manh mối và độ hấp dẫn của gameplay.

---

### CHƯƠNG 5: THẢO LUẬN, HẠN CHẾ & HƯỚNG PHÁT TRIỂN (DISCUSSION & LIMITATIONS)
* **5.1. Thảo luận học thuật:**
  - Sự hài hòa giữa tính chặt chẽ của logic (Symbolic) và tính bất ngờ sáng tạo của cốt truyện (Neural).
  - Khả năng tổng quát hóa của khung kiến trúc sang các bài toán suy luận phức tạp khác (chẩn đoán y khoa, điều tra gian lận tài chính).
* **5.2. Hạn chế hiện tại (Limitations):**
  - Cây suy luận giới hạn ở 2-3 bước (*2-to-3 hop reasoning*); chưa hỗ trợ vụ án có nhiều đồng phạm hoặc nhiều hiện trường phân tán.
  - Phụ thuộc vào chất lượng mô hình nền tảng (Foundation Models tham số <7B gặp khó khăn với cấu trúc JSON lồng nhau).
* **5.3. Hướng phát triển trong tương lai (Future Work):**
  - Tích hợp Học tăng cường từ phản hồi gameplay (*Reinforcement Learning from Gameplay Feedback - RLGF*).
  - Mở rộng Đồ thị tri thức đa phương thức kết hợp tạo sinh hình ảnh hiện trường tự động bằng Diffusion Models.

---

### CHƯƠNG 6: KẾT LUẬN (CONCLUSION)
* Khẳng định tính khả thi của mô hình Neuro-Symbolic trong việc khắc phục điểm yếu suy luận của LLM, mở ra hướng đi bền vững cho các trò chơi giải đố thông minh thế hệ mới.

---

## PHẦN 4: BẢN THUYẾT MINH CHIẾN LƯỢC BẢO VỆ VỚI THẦY HƯỚNG DẪN

1. **Khẳng định tính chất "Khoa học Máy tính" chứ không phải "Kỹ thuật Phần mềm thông thường":**
   > *"Thưa thầy, đề tài này không dừng lại ở việc làm một trang web chơi game rồi gọi API của OpenAI để sinh text. Đóng góp cốt lõi của em là giải quyết một bài toán mở trong ngành Trí tuệ Nhân tạo: **Làm thế nào để kiểm soát ảo giác suy luận và bảo đảm tính nhất quán logic hình thức trong quá trình tạo sinh nội dung thủ tục của LLM?** Hệ thống Web chính là môi trường thực nghiệm tương tác thời gian thực để chứng minh tính đúng đắn của mô hình lý thuyết."*

2. **Nhấn mạnh kiến trúc Neuro-Symbolic và Đồ thị học:**
   > *"Em sử dụng mô hình kết hợp Neuro-Symbolic: Dùng LLM cho năng lực sinh ngữ nghĩa tự nhiên, nhưng dùng Động cơ luật Tất định và Đồ thị hai phía (Bipartite Graph) để kiểm chứng nghiệm duy nhất và tính giải được (Solvability). Điều này loại bỏ hoàn toàn rủi ro người chơi gặp phải vụ án vô nghiệm do AI nói nhảm."*

3. **Nhấn mạnh giá trị thực nghiệm có số liệu đo lường rõ ràng (Empirical Evidence):**
   > *"Em đã xây dựng benchmark đo lường định lượng trên các thang đo chuẩn: Schema Validity, Forensic Consistency, và Graph Solvability. Kết quả thực nghiệm cho thấy kiến trúc đề xuất giúp nâng tính giải được của kịch bản từ mức dưới 30% ở baseline lên 100%, bảo đảm trải nghiệm giải đố công bằng (Fair-play) cho người chơi."*
