# CONSENSUS AGENT — FINAL LITERATURE REVIEW PROMPT

## 1. Research Context

I am conducting a thesis/project on:

**“Nghiên cứu và xây dựng trò chơi trinh thám giải đố trên nền tảng Web, ứng dụng Mô hình ngôn ngữ lớn (LLM) để sinh tự động các bộ hồ sơ vụ án có tính logic và nhất quán.”**

The system generates structured locked-room murder mystery case dossiers for a web-based detective deduction game.

The current system uses:

* LLM-based generation
* Multiple specialized generation agents
* Deterministic validation
* Targeted/localized repair of detected inconsistencies
* A bipartite graph representation for the generated case structure

The detailed project architecture, current implementation, proposed methods, claims, research questions, and uncertainties are provided in the attached research brief.

**Important:** Treat the research brief as the description of the current project state. Do not assume that proposed/planned components have already been implemented or experimentally validated.

---

# 2. Main Objective

Conduct a rigorous literature review to determine:

1. What research already exists that is directly or indirectly relevant to this problem.
2. Which techniques have been demonstrated to improve logical, temporal, causal, factual, or structural consistency in LLM-generated content.
3. What evidence exists for multi-agent versus single-agent/monolithic generation.
4. What evidence exists for combining LLM generation with deterministic, symbolic, constraint-based, graph-based, or formal verification.
5. What approaches exist for detecting and repairing inconsistencies after generation.
6. What methods exist for formally representing or verifying the solvability and fairness of mystery/deduction problems.
7. What benchmarks and evaluation metrics are appropriate for evaluating this type of system.
8. Whether cross-lingual generation/reasoning introduces relevant problems.
9. Most importantly, identify **research gaps that genuinely remain**, rather than trying to prove that the proposed approach is novel.

---

# 3. Critical Evidence Policy

Be strictly evidence-based.

Do NOT assume that a claim is true merely because it sounds theoretically reasonable.

For every research question or claim, distinguish between:

* **Direct evidence:** The paper explicitly studies the relevant problem and provides experimental/theoretical evidence.
* **Indirect evidence:** The paper studies a closely related problem but not the exact task.
* **Weak/analogical evidence:** The connection is plausible but not directly demonstrated.
* **No evidence found:** Relevant evidence could not be identified.
* **Conflicting evidence:** Different studies report different conclusions.

**“No evidence found” is an acceptable and useful result.**

Do not force the literature to support the proposed architecture.

If a paper does NOT actually demonstrate that method A is better than method B, do not describe it as evidence that A is superior.

---

# 4. Research Questions

Investigate the following questions.

### RQ1 — Procedural Generation of Mystery / Deduction Content

What existing research has investigated automatic or procedural generation of:

* murder mysteries
* detective stories
* mystery narratives
* logical deduction problems
* crime scenarios
* locked-room puzzles
* investigation games
* interactive narrative structures

Determine which systems actually **generate** such content and which merely **evaluate, classify, or reason over** existing mystery content.

Do not classify a benchmark as a mystery-generation benchmark unless the original paper supports that interpretation.

---

### RQ2 — Multi-Agent vs. Monolithic LLM Generation

What empirical evidence exists comparing:

* single-agent / monolithic prompting
* multi-agent generation
* role-specialized agents
* planning + generation architectures
* agent decomposition

with respect to:

* consistency
* factual correctness
* logical validity
* temporal consistency
* controllability
* diversity
* generation quality
* computational cost

Do not assume that multi-agent systems outperform monolithic systems.

If direct evidence for this specific type of narrative generation is limited, explicitly state that limitation.

---

### RQ3 — LLM + Symbolic / Deterministic Verification

What evidence exists for combining LLM generation with:

* symbolic reasoning
* constraint satisfaction
* rule-based verification
* deterministic validators
* formal methods
* programmatic checks
* graph-based consistency checking
* neuro-symbolic approaches

Investigate whether these approaches improve:

* logical consistency
* factual consistency
* temporal consistency
* structural validity
* constraint satisfaction
* controllability

Be precise about terminology.

Do not automatically describe an LLM + deterministic validator architecture as “neuro-symbolic” unless the cited literature supports that classification.

---

### RQ4 — Error Detection and Localized Repair

Investigate methods for detecting and repairing errors in LLM-generated structured or narrative content.

Focus particularly on:

* post-hoc validation
* targeted error detection
* localized repair
* iterative refinement
* self-correction
* constrained regeneration
* patch-based repair
* verifier-guided generation

Compare, where evidence exists:

* regenerating the entire output
* repairing only the inconsistent component
* iterative generation/verification loops

Look for evidence concerning:

* repair success rate
* preservation of already-valid content
* computational/token cost
* convergence
* introduction of new errors

Do not claim localized repair is more efficient unless the literature provides evidence.

---

### RQ5 — Formal Solvability and Fairness of Mystery Problems

Investigate research concerning formal representation and verification of:

* puzzle solvability
* uniqueness of solutions
* deductive completeness
* clue sufficiency
* consistency of clues
* fairness
* ambiguity
* constraint satisfaction
* graph-based reasoning
* knowledge representation for detective/mystery problems

Determine whether existing work provides methods that could be adapted to verify whether a generated mystery has:

* at least one valid solution
* exactly one intended solution
* sufficient evidence/clues
* no contradictory clues
* no unintended alternative explanations

Clearly distinguish between:

* formal guarantees
* heuristic checks
* human evaluation

---

### RQ6 — Cross-Lingual LLM Reasoning and Generation

Investigate evidence concerning differences between languages in:

* logical reasoning
* temporal reasoning
* causal reasoning
* factual consistency
* narrative generation
* instruction following
* hallucination/error rates

Pay particular attention to multilingual and low-resource settings where relevant.

Do not assume that Vietnamese necessarily performs worse unless evidence specifically supports that conclusion.

---

### RQ7 — Evaluation and Benchmarking

Identify evaluation methodologies suitable for this project.

Look for metrics covering:

* factual consistency
* logical consistency
* temporal consistency
* structural validity
* constraint satisfaction
* solvability
* uniqueness
* diversity
* narrative quality
* human preference
* controllability

For every benchmark mentioned in the research brief, verify its actual purpose from the original paper.

In particular, determine whether benchmarks such as WHODUNIT, Sherlock, MuSR, or other related datasets are actually suitable for:

* mystery generation
* mystery reasoning
* LLM evaluation
* narrative consistency evaluation
* logical deduction

Do not assume they are generation benchmarks merely because they contain mystery/deduction content.

---

# 5. Claims Requiring Verification

Investigate the following claims independently.

### Claim 1

LLMs have difficulties maintaining causal, temporal, or logical consistency across long generated narratives.

### Claim 2

Monolithic prompting becomes less reliable as the number of interacting constraints increases.

### Claim 3

Decomposing generation into specialized agents can improve controllability or consistency.

### Claim 4

Combining LLM generation with symbolic/deterministic constraint verification can improve the validity of generated structured content.

Do NOT interpret this as the claim that “neuro-symbolic methods are necessarily superior.”

### Claim 5

Localized repair can be preferable to complete regeneration when only a small portion of a generated structure is invalid.

### Claim 6

Graph-based representations can help reason about relationships and constraints in generated mystery structures.

### Claim 7

Formal constraint checking can be used to establish or approximate puzzle solvability and fairness.

### Claim 8

LLM performance can vary across languages, particularly for reasoning-heavy tasks.

### Claim 9

Mystery-generation systems face computational or combinatorial constraints when attempting to enforce classical mystery-writing rules such as the Ronald Knox principles.

For each claim, report whether the literature provides:

* direct support
* indirect support
* contradictory evidence
* insufficient evidence

---

# 6. Required Information for Each Important Paper

For each highly relevant paper, provide:

1. **Title**
2. **Authors**
3. **Year**
4. **Publication venue**
5. **Publication status**

   * peer-reviewed
   * conference
   * journal
   * workshop
   * preprint
   * technical report
6. **Research problem**
7. **Method / architecture**
8. **Dataset / benchmark**
9. **Evaluation metrics**
10. **Main experimental results**
11. **Important limitations**
12. **Relevance to my project**
13. **Whether the evidence directly or indirectly supports any of my claims/RQs**

Prefer original research papers over secondary summaries.

Do not fabricate missing experimental details.

---

# 7. Evidence Table

Create a structured table similar to:

| Paper | Problem | Method | Dataset | Metrics | Main Result | Limitation | Direct/Indirect Evidence | Relevance |
| ----- | ------- | ------ | ------- | ------- | ----------- | ---------- | ------------------------ | --------- |

Prioritize papers with actual experiments.

---

# 8. Research Gap Analysis

After reviewing the literature, identify research gaps.

For each potential gap, explain:

1. What existing research already solves.
2. What existing research only partially solves.
3. What has not been adequately studied.
4. Why the gap is relevant to this project.
5. Whether my proposed approach actually addresses the gap.
6. Whether the gap is genuinely novel or merely an engineering combination of existing techniques.

Avoid claiming novelty unless the literature provides sufficient evidence.

---

# 9. Proposed Architecture vs. Prior Work

Compare my project's approach with related approaches in the literature.

The comparison should cover:

* monolithic LLM generation
* multi-agent generation
* planning-based generation
* constraint-guided generation
* symbolic verification
* graph-based verification
* post-hoc validation
* iterative self-correction
* localized repair
* formal puzzle verification

Do not automatically treat my architecture as superior.

Instead, identify:

* similarities
* differences
* demonstrated advantages
* demonstrated disadvantages
* unresolved questions

---

# 10. Important Distinction: Current vs. Proposed System

The research brief contains both implemented/current components and proposed/planned components.

When discussing literature, explicitly distinguish:

**CURRENT / IMPLEMENTED**
from
**PROPOSED / PLANNED**

Do not cite literature as validation of an experimental result that has not yet been conducted.

If the research brief contains hypothetical performance numbers or placeholder citations, treat them only as planning assumptions and do not use them as empirical evidence.

---

# 11. Search Strategy

Search across relevant research areas, including:

* procedural content generation
* computational narrative
* interactive storytelling
* mystery generation
* detective game generation
* LLM-based narrative generation
* multi-agent LLM systems
* structured text generation
* constrained generation
* neuro-symbolic AI
* symbolic verification
* constraint satisfaction
* programmatic verification
* LLM self-correction
* LLM iterative refinement
* graph-based reasoning
* puzzle generation
* puzzle solvability
* game fairness
* multilingual reasoning
* narrative consistency

Use combinations of keywords rather than relying on a single query.

---

# 12. Source Quality

Prioritize:

1. Peer-reviewed journal/conference papers
2. Highly cited established research
3. Recent strong papers
4. Important preprints when peer-reviewed evidence is unavailable

For preprints, clearly label them as preprints.

Do not exclude an important recent paper solely because it has not yet been peer-reviewed, but do not present it as peer-reviewed evidence.

Prefer primary sources and original experiments.

---

# 13. Final Deliverable

Produce a literature review organized into:

## A. Executive Summary

What is already known and what remains uncertain.

## B. State of the Art

Relevant existing approaches and systems.

## C. Evidence for Each Research Question

Answer RQ1–RQ7 separately.

## D. Claim Verification

Evaluate Claims 1–9 using the evidence categories above.

## E. Method Comparison

Compare major approaches relevant to the proposed architecture.

## F. Evaluation Methodology

Recommend evidence-based metrics and evaluation designs appropriate for this project.

## G. Research Gaps

Identify genuine gaps supported by the literature.

## H. Relevance to My Project

Explain which findings directly inform the current implementation and which only inform future/planned components.

## I. Recommended Key Papers

Provide a prioritized reading list of the most relevant papers, but **do not rank them by scientific quality**. Instead, categorize them by relevance, such as:

* Directly relevant
* Methodologically relevant
* Evaluation relevant
* Background/theoretical

## J. References

Provide complete bibliographic information and links/DOIs where available.

---

# 14. Final Rules

The goal is **not to prove that my proposed architecture is correct**.

The goal is to determine what the existing scientific literature actually supports.

Therefore:

* Do not manufacture evidence.
* Do not infer experimental results that papers did not report.
* Do not treat assumptions as facts.
* Do not treat engineering intuition as empirical evidence.
* Do not claim novelty without sufficient literature comparison.
* Explicitly report negative findings.
* Explicitly report conflicting findings.
* Distinguish direct evidence from analogy.
* Distinguish peer-reviewed work from preprints.
* Verify the actual purpose of every benchmark.
* Use the original paper whenever possible.
* If an RQ cannot be answered confidently from the literature, state that clearly.

**Absence of evidence is an acceptable research finding.**

The final result should help determine whether the proposed research direction is:

1. already well studied,
2. a known technique applied to a new domain,
3. a combination of existing techniques,
4. partially novel,
5. or genuinely underexplored.

Do not decide this in advance. Let the literature determine the conclusion.
