# ACADEMIC THESIS WRITING & REFACTORING RULES (AGENTS.md)

## 1. FACTUAL GROUNDING & DATA INTEGRITY
- **Strict Codebase & DB Grounding:** Base all system descriptions strictly on the actual codebase (`detective-backend` FastAPI, Unity 6 URP 2D client) and real telemetry from the SQLite `benchmark_runs` table. Do NOT invent unimplemented features or hypothetical benchmarks.
- **Exact Identifiers & Hardware Specs:**
  - Fix all typos spelling `gpt-4o` as `gpt-40` (use `gh/gpt-4o`, `gh/gpt-4o-mini`, `ollama/gemma4:31b-cloud`).
  - State the exact hardware used for experiments: **Lenovo Legion 5, AMD Ryzen 5 5600H, NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)** (verify RAM/OS with the author: 24 GB RAM, Windows 11 Pro 64-bit).
- **Verified Citations Only:** Audit all references `[1]`–`[21]`. Fix mismatches (e.g., `[16]` cites *WHODUNIT* in-text but lists *DSPy* in the bibliography) and replace any fabricated arXiv IDs/papers (`[17]`, `[18]`) with real, verified papers or mark `[TODO: VERIFY CITATION]`.

## 2. VOICE, PRONOUNS & EPISTEMIC HUMILITY (CHUẨN VĂN PHONG KHOA HỌC)
- **Subject & Pronoun Discipline:**
  - Refer to the work impersonally as **"đồ án"** (e.g., *"Đồ án đề xuất..."*, *"Kết quả thực nghiệm của đồ án cho thấy..."*) or use **"tôi"** in personal sections (*Lời cam đoan*, *Lời cảm ơn*).
  - NEVER use **"chúng tôi"** or **"nhóm tác giả"** for the author's own work (reserve *"nhóm tác giả"* strictly for external cited papers).
- **Zero Marketing Hype:** Eliminate all dramatic, promotional, or self-praising adjectives.
  - *BANNED:* "đanh thép", "xuất sắc", "tối thượng", "vượt bậc", "cách mạng", "tuyệt đối", "hoàn hảo", "ngõ cụt kỹ thuật", "hố sâu ngăn cách".
  - *USE INSTEAD:* "kết quả cho thấy", "giảm đáng kể", "phù hợp với", "đáp ứng tiêu chí", "hạn chế rủi ro".
- **Honest Limitations & Negative Results:** Report edge-case failures, remaining error rates, and methodological limitations candidly (e.g., sample size limits, single-prompt variance, domain constraints of closed-room mysteries) rather than generic future-scaling wishes.

## 3. TERMINOLOGY, ABBREVIATIONS & FOOTNOTES (XỬ LÝ THUẬT NGỮ)
- **Ban Gratuitous Parenthetical Translations:** NEVER append English translations in parentheses after standard Vietnamese phrases (BANNED: *"nghệ thuật kể chuyện tương tác (Interactive Narrative)"*, *"độ trễ phản hồi (response latency)"*).
- **Direct Technical Loanwords:** Use established English computing terms directly in Vietnamese sentences without parentheses or dictionary footnotes where natural (e.g., *prompt*, *schema*, *token*, *pipeline*, *endpoint*, *latency*, *backend*, *client*).
- **No Dictionary Footnotes:** NEVER use `\footnote{Thuật ngữ tiếng Anh: ...}`. Use footnotes only for substantive explanations or data caveats.
- **Acronym Lifecycle:** Expand true abbreviations once on first occurrence (`Mô hình Ngôn ngữ Lớn (Large Language Model -- LLM)`), use only the acronym thereafter, and register 100% of used acronyms in `DANH MỤC CHỮ VIẾT TẮT VÀ THUẬT NGỮ` (columns: `Viết tắt | Thuật ngữ đầy đủ | Ý nghĩa`).

## 4. STRUCTURAL & LATEX HYGIENE (CẤU TRÚC & ĐỊNH DẠNG)
- **Traceability & Pre-defined Criteria:** Structure system requirements and architectural choices as a traceability table linking observed LLM failure modes (Chapter 1/2) -> quantitative readiness criteria -> system components (Chapter 3).
- **Chapter Bookends:** Begin every chapter with a 4–5 line roadmap paragraph outlining its sections, and end every chapter with a `Kết luận chương` summarizing key findings and bridging to the next chapter.
- **LaTeX & Chart Fixes:**
  - Fix broken math/text escaping (`0(1)` -> `\mathcal{O}(1)`, `SUSP-d{2}\$` -> `\texttt{SUSP-\textbackslash d\{2\}}`, broken Vietnamese accents like `Hoen $\hat{o}$`, `định $d\hat{e}$`).
  - Fix Figure 4.2 chart labels from `%` to seconds (`s`).
  - Include units in table headers and sample sizes / measurement conditions in table footnotes.
