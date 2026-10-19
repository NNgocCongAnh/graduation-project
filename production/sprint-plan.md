# Sprint Plan: Game Demo & Academic Benchmarking

**Rigor**: Standard | **Automation**: Guided
**Goal**: Deliver a playable Unity demo and a comprehensive experimental dataset for the thesis.

## Epic 1: Unity Client (Game UI/UX)
*Objective: Create a professional investigative interface that connects to the Neuro-Symbolic Backend.*

### User Stories
- **S1.1: API Integration**
  - As a player, I want the game to fetch generated cases from the backend so I can start investigating.
  - **Acceptance**: `DetectiveAPIManager.cs` implements REST calls to `/api/case/generate` and `/api/case/verify`.
- **S1.2: Interactive Corkboard**
  - As a player, I want to drag and drop suspect photos and evidence cards on a board to organize my thoughts.
  - **Acceptance**: Implemented drag-and-drop system with persistent positions.
- **S1.3: Red String Connection**
  - As a player, I want to draw "red strings" between clues and suspects to build my theory.
  - **Acceptance**: Visual links using LineRenderer/UI Canvas that can be created/deleted.
- **S1.4: Forensic & Accusation Modals**
  - As a player, I want to read detailed forensic reports and submit my final deduction.
  - **Acceptance**: Modal UI for forensic data and a submission form that triggers the `/verify` endpoint.

## Epic 2: Automated Test & Benchmark Suite
*Objective: Provide mathematical and empirical proof of the Neuro-Symbolic approach for the thesis.*

### User Stories
- **S2.1: Validator Stress Test**
  - As a researcher, I want to verify that the Validator catches 100% of forensic/timing contradictions.
  - **Acceptance**: Pytest suite covering Henssge's laws and Bipartite Graph solvability.
- **S2.2: Baseline vs Proposed Benchmark**
  - As a researcher, I want to compare the "Single-Prompt" vs "Multi-Agent" approach in terms of logical validity and solve-rate.
  - **Acceptance**: `benchmark_runner.py` outputs a CSV/JSON file comparing Baseline vs Proposed.
- **S2.3: Data Export for Thesis**
  - As a researcher, I want the benchmark results to be easily convertible to charts for the thesis.
  - **Acceptance**: Automation script to export results into format ready for Matplotlib/Excel.
