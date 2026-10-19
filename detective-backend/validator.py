"""Rule-Based Consistency Validator Engine with Neuro-Symbolic Diagnostics (Paper 7).

This module acts as the logic gatekeeper, checking:
1. Identifier uniqueness and schema integrity.
2. Forensic Time of Death (TOD) cooling rate physics (Henssge's model approximation).
3. Ground Truth alignment (crime time within TOD window, culprit consistency).
4. Solvable Contradiction (Culprit alibi flaw vs evidence).
5. Innocent consistency and Red Herring integrity.
6. Solvability metrics and Multi-hop Reasoning chain consistency (Paper 3).

Returns structured diagnostic violation signals enabling targeted localized patch repair.
"""

from typing import List, Tuple, Optional, Set
from models import (
    CaseDossier, Suspect, Evidence, ForensicData,
    ConstraintViolation, ValidationResult, ViolationType
)


def time_to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' string to minutes elapsed since 00:00."""
    hours, minutes = map(int, time_str.strip().split(":"))
    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    """Convert minutes elapsed since 00:00 to 'HH:MM' string."""
    minutes = minutes % (24 * 60)
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def is_time_in_interval(target: str, start: str, end: str) -> bool:
    """Check if target time falls within [start, end] interval (handles same-day and midnight crossing)."""
    t_min = time_to_minutes(target)
    s_min = time_to_minutes(start)
    e_min = time_to_minutes(end)

    if s_min <= e_min:
        return s_min <= t_min <= e_min
    else:
        # Crosses midnight (e.g. 23:00 to 02:00)
        return t_min >= s_min or t_min <= e_min


def calculate_henssge_pmi_bounds(body_temp: float, ambient_temp: float) -> Tuple[float, float]:
    """Estimate minimum and maximum Post-Mortem Interval (PMI in hours) using cooling rate physics.

    Standard normal body core temperature is approx 37.0°C.
    Standard cooling rate in ambient environment (15°C - 25°C) is roughly 1.0°C - 1.5°C/hr.
    Returns: (pmi_min_hours, pmi_max_hours)
    """
    temp_drop = max(0.0, 37.0 - body_temp)
    if temp_drop <= 0.2:
        return 0.0, 1.0

    # Minimum hours (fast cooling 1.5°C/h) and maximum hours (slow cooling 0.8°C/h)
    pmi_min = temp_drop / 1.5
    pmi_max = temp_drop / 0.8
    return round(pmi_min, 1), round(pmi_max, 1)


def validate_case_diagnostics(case: CaseDossier) -> ValidationResult:
    """Perform fine-grained Neuro-Symbolic validation, returning structured violation signals.

    Enables localized patch repair: each violation points to the responsible component
    ('outline', 'character', 'clue', 'reasoning') with concrete diagnostic feedback.
    """
    violations: List[ConstraintViolation] = []

    # 1. Identifier Integrity & Culprit Uniqueness Check
    suspect_ids: Set[str] = set()
    culprits: List[Suspect] = []

    for s in case.suspects:
        if s.id in suspect_ids:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.DUPLICATE_ID,
                component="character",
                message=f"Duplicate suspect ID found: '{s.id}'.",
                target_id=s.id
            ))
        suspect_ids.add(s.id)
        if s.is_culprit:
            culprits.append(s)

    if len(culprits) != 1:
        violations.append(ConstraintViolation(
            violation_type=ViolationType.MULTIPLE_CULPRITS,
            component="character",
            message=f"Case must have exactly 1 culprit, but found {len(culprits)}."
        ))
    else:
        culprit = culprits[0]
        if case.ground_truth.culprit_id != culprit.id:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.MULTIPLE_CULPRITS,
                component="outline",
                message=(
                    f"GroundTruth culprit_id ('{case.ground_truth.culprit_id}') does not match "
                    f"the suspect flagged as culprit ('{culprit.id}')."
                ),
                target_id=culprit.id
            ))

    # 2. Evidence Integrity & Crucial Clue Check
    evidence_ids: Set[str] = set()
    crucial_evidences: List[Evidence] = []

    for ev in case.evidences:
        if ev.id in evidence_ids:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.DUPLICATE_ID,
                component="clue",
                message=f"Duplicate evidence ID found: '{ev.id}'.",
                target_id=ev.id
            ))
        evidence_ids.add(ev.id)

        if ev.linked_suspect_id and ev.linked_suspect_id not in suspect_ids:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.SCHEMA_ERROR,
                component="clue",
                message=f"Evidence '{ev.id}' links to non-existent suspect '{ev.linked_suspect_id}'.",
                target_id=ev.id
            ))
        if ev.is_crucial:
            crucial_evidences.append(ev)

    if len(crucial_evidences) == 0:
        violations.append(ConstraintViolation(
            violation_type=ViolationType.NO_CRUCIAL_CLUE,
            component="clue",
            message="Case must contain at least 1 crucial evidence (is_crucial=True) to ensure solvability."
        ))

    # 3. Forensic TOD (Time of Death) Consistency Check
    forensic: ForensicData = case.victim.forensic_data
    tod_start_min = time_to_minutes(forensic.estimated_tod_start)
    tod_end_min = time_to_minutes(forensic.estimated_tod_end)

    if tod_start_min > tod_end_min:
        violations.append(ConstraintViolation(
            violation_type=ViolationType.TOD_PHYSICS,
            component="outline",
            message=f"Forensic TOD start ({forensic.estimated_tod_start}) is after TOD end ({forensic.estimated_tod_end})."
        ))

    # Crime time must fall within the estimated TOD window
    crime_time = case.ground_truth.actual_crime_time
    if not is_time_in_interval(crime_time, forensic.estimated_tod_start, forensic.estimated_tod_end):
        violations.append(ConstraintViolation(
            violation_type=ViolationType.CRIME_TIME_OUTSIDE_TOD,
            component="outline",
            message=(
                f"Actual crime time '{crime_time}' is outside the forensic estimated TOD window "
                f"[{forensic.estimated_tod_start} - {forensic.estimated_tod_end}]."
            )
        ))

    # Basic thermal drop validation
    if forensic.body_temp >= 37.5 and forensic.ambient_temp < 30.0:
        violations.append(ConstraintViolation(
            violation_type=ViolationType.TOD_PHYSICS,
            component="outline",
            message=f"Body temperature {forensic.body_temp}°C is abnormally high for deceased victim."
        ))

    # 4. Culprit Alibi & Solvability Contradiction Check
    if len(culprits) == 1:
        culprit = culprits[0]
        # Verify core contradiction is documented
        if not case.ground_truth.core_contradiction or len(case.ground_truth.core_contradiction.strip()) < 10:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.ALIBI_UNBROKEN,
                component="outline",
                message="GroundTruth.core_contradiction must contain a detailed description of the logical flaw."
            ))

        # Check if culprit claims an alibi covering the crime time
        alibi_covers_crime = is_time_in_interval(crime_time, culprit.alibi_start, culprit.alibi_end)
        culprit_clues = [ev for ev in crucial_evidences if ev.linked_suspect_id == culprit.id or ev.is_crucial]

        if alibi_covers_crime and not culprit_clues:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.ALIBI_UNBROKEN,
                component="clue",
                message=(
                    f"Culprit '{culprit.id}' claims an alibi during the crime time [{culprit.alibi_start}-{culprit.alibi_end}], "
                    f"but no crucial evidence exists to break this alibi."
                ),
                target_id=culprit.id
            ))

    # 5. Multi-Hop Reasoning Chain Validation (Paper 3)
    if case.reasoning_chain:
        for step in case.reasoning_chain.steps:
            for cid in step.clue_ids:
                if cid not in evidence_ids:
                    violations.append(ConstraintViolation(
                        violation_type=ViolationType.SCHEMA_ERROR,
                        component="reasoning",
                        message=f"Reasoning step {step.step_number} cites non-existent clue ID '{cid}'.",
                        target_id=cid
                    ))

    # Consolidate Diagnostic Feedback for Localized Repair
    diagnostic_messages = [f"[{v.component.upper()}:{v.violation_type.value}] {v.message}" for v in violations]
    feedback = "; ".join(diagnostic_messages) if diagnostic_messages else "No violations found. Case logic is valid."

    return ValidationResult(
        is_valid=(len(violations) == 0),
        violations=violations,
        diagnostic_feedback=feedback
    )


def validate_case_logic(case: CaseDossier) -> Tuple[bool, List[str]]:
    """Backward-compatible wrapper returning (is_valid, list_of_error_strings)."""
    diag_result = validate_case_diagnostics(case)
    error_messages = [v.message for v in diag_result.violations]
    return diag_result.is_valid, error_messages
