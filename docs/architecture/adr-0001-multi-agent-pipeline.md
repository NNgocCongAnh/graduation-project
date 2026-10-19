# ADR-0001: Multi-Agent Sequential Pipeline

## Status
Accepted

## Date
2026-10-06

## Summary
Implements a 4-stage sequential pipeline (Outline $\rightarrow$ Character $\rightarrow$ Clue $\rightarrow$ Deduction) to decompose the complexity of mystery generation.

## Decision
Instead of a single prompt, we use specialized agents:
- **OutlineAgent**: Sets the ground truth and crime premise.
- **CharacterAgent**: Creates suspects and alibis.
- **ClueAgent**: Generates physical evidence.
- **DeductionAgent**: Verifies the reasoning chain.

## Consequences
- **Positive**: Higher quality, more consistent narratives.
- **Negative**: Increased API cost and latency due to multiple calls.
