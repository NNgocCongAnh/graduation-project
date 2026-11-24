# ADR-0003: Localized Patch Repair

## Status
Accepted

## Date
2026-10-06

## Summary
Implements "Localized Patch Repair" (ConWriter) to fix specific errors without regenerating the entire case.

## Decision
When a validator finds a contradiction, the system sends the specific error and the relevant snippet back to the agent for a targeted fix.

## Consequences
- **Positive**: Preserves the parts of the story that are already good.
- **Negative**: May introduce new contradictions if the patch is too large.
