# ADR-0002: Deterministic Validator (Henssge)

## Status
Accepted

## Date
2026-10-06

## Summary
Uses a deterministic rule-based validator to eliminate LLM hallucinations in the generated case.

## Decision
Every generated case must pass a hard-coded validation suite (forensics, timing, location) based on Henssge's laws of mystery.

## Consequences
- **Positive**: 100% guarantee that the case is logically sound.
- **Negative**: Requires manual definition of rules for every new type of evidence.
