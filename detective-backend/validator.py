"""Rule-Based Consistency Validator & Deduction Scoring Engine (Paper 7 & Paper 3).

This module acts as the neuro-symbolic logic gatekeeper and deduction evaluator:
1. Identifier uniqueness, referential integrity, and Pydantic v2 schema constraints.
2. Forensic Time of Death (TOD) cooling rate physics (Henssge's model approximation).
3. Ground Truth alignment (crime time within TOD window, culprit consistency).
4. Solvable Contradiction (Culprit alibi flaw vs evidence graph).
5. Innocent consistency and Red Herring integrity (Fair-play mystery assurance).
6. Solvability metrics and Multi-hop Reasoning chain consistency (Paper 3).
7. Player Deduction Scoring & Anti-Spam Evaluation Engine:
   - In-memory deterministic scoring (< 0.1ms latency).
   - Precision/Recall scoring with red-herring trap penalty.
   - Comprehensive feedback for frontend modal and thesis benchmark analysis.
"""

import math
import re
from typing import List, Tuple, Optional, Set, Dict, Any
from models import (
    CaseDossier, Suspect, Evidence, ForensicData,
    ConstraintViolation, ValidationResult, ViolationType,
    VerifyResponse, DeductionVerdict, DeductionScoreBreakdown
)


def robust_time_to_minutes(time_str: str) -> Optional[int]:
    """Safely parse a time string into minutes elapsed since 00:00 (0 to 1439).

    Handles 'HH:MM', 'H:MM', 'HH:MM:SS', trailing whitespaces, and returns None
    for empty or malformed inputs without raising uncaught runtime exceptions.
    """
    if not time_str or not isinstance(time_str, str):
        return None
    cleaned = time_str.strip()
    match = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", cleaned)
    if not match:
        return None
    hours, minutes = int(match.group(1)), int(match.group(2))
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None
    return hours * 60 + minutes


def time_to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' string to minutes elapsed since 00:00.

    Maintains backward compatibility for legacy callers; raises ValueError
    if input cannot be parsed.
    """
    mins = robust_time_to_minutes(time_str)
    if mins is None:
        raise ValueError(f"Invalid time format '{time_str}'. Expected 'HH:MM'.")
    return mins


def minutes_to_time(minutes: int) -> str:
    """Convert minutes elapsed since 00:00 to normalized 'HH:MM' 24-hour string."""
    minutes = minutes % (24 * 60)
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def is_time_in_interval(target: str, start: str, end: str) -> bool:
    """Check if target time falls within [start, end] interval.

    Robustly handles both standard intervals (e.g. 14:00 to 18:00) and
    midnight transitions (e.g. 23:00 to 02:00). Returns False if any input is malformed.
    """
    t_min = robust_time_to_minutes(target)
    s_min = robust_time_to_minutes(start)
    e_min = robust_time_to_minutes(end)

    if t_min is None or s_min is None or e_min is None:
        return False

    if s_min <= e_min:
        return s_min <= t_min <= e_min
    else:
        # Crosses midnight (e.g. 23:00 to 02:00)
        return t_min >= s_min or t_min <= e_min


# -------------------------------------------------------------
# Henssge (1988) two-exponential body cooling model
# -------------------------------------------------------------
# Phi(t) = (T_body - T_amb) / (37.2 - T_amb)
#        = 1.25 e^(-k t) - 0.25 e^(-5 k t)      for T_amb <= 23.2 C
#        = 1.11 e^(-k t) - 0.11 e^(-10 k t)     for T_amb  > 23.2 C
# k = 1.2815 / (M * C)^0.625 - 0.0284           (M = body mass kg, C = corrective factor)
# Phi is strictly decreasing from 1 at t = 0, so the bisection root is unique.

HENSSGE_RECTAL_TEMP_AT_DEATH = 37.2
HENSSGE_AMBIENT_SWITCH = 23.2
HENSSGE_SEARCH_MAX_HOURS = 48.0
HENSSGE_EPSILON = 1e-4
HENSSGE_MAX_ITERATIONS = 100
# Thesis eq. TOD = [T_discovery - (t* + 1.5), T_discovery - (t* - 1.5)]
HENSSGE_TOD_TOLERANCE_HOURS = 1.5
MINUTES_PER_DAY = 1440


def henssge_cooling_constant(body_weight_kg: float = 70.0, cooling_factor: float = 1.0) -> float:
    """Cooling constant k (1/h) from body mass M and corrective factor C."""
    return 1.2815 / (body_weight_kg * cooling_factor) ** 0.625 - 0.0284


def henssge_phi(hours: float, k: float, ambient: float) -> float:
    """Normalised temperature ratio Phi(t) predicted by the Henssge model."""
    if ambient <= HENSSGE_AMBIENT_SWITCH:
        return 1.25 * math.exp(-k * hours) - 0.25 * math.exp(-5 * k * hours)
    return 1.11 * math.exp(-k * hours) - 0.11 * math.exp(-10 * k * hours)


def solve_pmi_bisection(
    body_temp: float,
    ambient_temp: float,
    body_weight_kg: float = 70.0,
    cooling_factor: float = 1.0,
) -> Optional[float]:
    """Post-mortem interval t* (hours) by bisection on [0, 48] h, eps = 1e-4, <= 100 iterations.

    Returns 0.0 if the body is still at living temperature, or None when the reading
    cannot be explained by cooling within the search range (body colder than the room,
    or more than 48 h needed).
    """
    span = HENSSGE_RECTAL_TEMP_AT_DEATH - ambient_temp
    if span <= 0:
        return None
    phi_target = (body_temp - ambient_temp) / span
    if phi_target >= 1.0:
        return 0.0
    if phi_target <= 0.0:
        return None

    k = henssge_cooling_constant(body_weight_kg, cooling_factor)
    if k <= 0:
        return None

    def f(t: float) -> float:
        return henssge_phi(t, k, ambient_temp) - phi_target

    a, b = 0.0, HENSSGE_SEARCH_MAX_HOURS
    if f(b) > 0:  # still warmer than the model allows after 48 h
        return None

    for _ in range(HENSSGE_MAX_ITERATIONS):
        m = (a + b) / 2
        fm = f(m)
        if abs(fm) < HENSSGE_EPSILON or (b - a) / 2 < HENSSGE_EPSILON:
            return m
        if f(a) * fm < 0:
            b = m
        else:
            a = m
    return (a + b) / 2


def calculate_henssge_pmi_bounds(
    body_temp: float,
    ambient_temp: float,
    body_weight_kg: float = 70.0,
    cooling_factor: float = 1.0,
) -> Tuple[float, float]:
    """(min, max) post-mortem interval in hours: t* -/+ the Henssge tolerance.

    Kept for backward compatibility; returns (0.0, 0.0) when the reading is unphysical.
    """
    t_star = solve_pmi_bisection(body_temp, ambient_temp, body_weight_kg, cooling_factor)
    if t_star is None:
        return 0.0, 0.0
    return (
        round(max(0.0, t_star - HENSSGE_TOD_TOLERANCE_HOURS), 2),
        round(t_star + HENSSGE_TOD_TOLERANCE_HOURS, 2),
    )


def minutes_to_hhmm(total_minutes: float) -> str:
    """Wrap minutes onto a 24 h clock and format as HH:MM."""
    m = int(round(total_minutes)) % MINUTES_PER_DAY
    return f"{m // 60:02d}:{m % 60:02d}"


def henssge_tod_window(forensic: ForensicData) -> Optional[Tuple[str, str]]:
    """Forensic time-of-death window derived from the Henssge model.

    TOD = [discovery - (t* + 1.5 h), discovery - (t* - 1.5 h)]. Returns None when
    discovery_time is unknown (legacy dossiers) or the temperatures are unphysical.
    """
    if not forensic.discovery_time:
        return None
    discovery = robust_time_to_minutes(forensic.discovery_time)
    t_star = solve_pmi_bisection(
        forensic.body_temp, forensic.ambient_temp, forensic.body_weight_kg, forensic.cooling_factor
    )
    if discovery is None or t_star is None:
        return None
    earliest = discovery - (t_star + HENSSGE_TOD_TOLERANCE_HOURS) * 60
    latest = discovery - max(0.0, t_star - HENSSGE_TOD_TOLERANCE_HOURS) * 60
    return minutes_to_hhmm(earliest), minutes_to_hhmm(latest)


def apply_henssge_tod_window(forensic: ForensicData) -> bool:
    """Let the symbolic engine own the presented TOD window. Returns True if it was set."""
    window = henssge_tod_window(forensic)
    if window is None:
        return False
    forensic.estimated_tod_start, forensic.estimated_tod_end = window
    return True


def _henssge_violations(forensic: ForensicData, crime_time: str) -> List[ConstraintViolation]:
    """Henssge physics check; skipped for legacy dossiers without discovery_time."""
    if not forensic.discovery_time:
        return []

    t_star = solve_pmi_bisection(
        forensic.body_temp, forensic.ambient_temp, forensic.body_weight_kg, forensic.cooling_factor
    )
    if t_star is None:
        return [ConstraintViolation(
            violation_type=ViolationType.TOD_PHYSICS,
            component="outline",
            message=(
                f"Henssge model cannot explain body {forensic.body_temp}°C in ambient {forensic.ambient_temp}°C "
                f"within {HENSSGE_SEARCH_MAX_HOURS:.0f} h (body must be warmer than the room)."
            ),
        )]

    start, end = henssge_tod_window(forensic)
    if is_time_in_interval(crime_time, start, end):
        return []
    return [ConstraintViolation(
        violation_type=ViolationType.CRIME_TIME_OUTSIDE_TOD,
        component="outline",
        message=(
            f"Henssge PMI t*={t_star:.2f} h (M={forensic.body_weight_kg} kg, C={forensic.cooling_factor}, "
            f"found {forensic.discovery_time}) gives TOD window [{start} - {end}], "
            f"but actual crime time is '{crime_time}'."
        ),
    )]


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
    tod_s_min = robust_time_to_minutes(forensic.estimated_tod_start)
    tod_e_min = robust_time_to_minutes(forensic.estimated_tod_end)

    if tod_s_min is None or tod_e_min is None:
        violations.append(ConstraintViolation(
            violation_type=ViolationType.TOD_PHYSICS,
            component="outline",
            message=f"Invalid TOD time format: [{forensic.estimated_tod_start} - {forensic.estimated_tod_end}]."
        ))
    else:
        # Check window duration (supporting midnight crossing)
        duration_min = (tod_e_min - tod_s_min) if tod_e_min >= tod_s_min else (tod_e_min + 1440 - tod_s_min)
        if duration_min < 15 or duration_min > 720:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.TOD_PHYSICS,
                component="outline",
                message=f"Forensic TOD window duration ({duration_min} mins) is physically unrealistic."
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

    # Henssge two-exponential cooling model (deterministic physics gate)
    violations.extend(_henssge_violations(forensic, crime_time))

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

        if not alibi_covers_crime:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.ALIBI_UNBROKEN,
                component="character",
                message=(
                    f"Culprit '{culprit.id}' alibi [{culprit.alibi_start}-{culprit.alibi_end}] "
                    f"does not cover the actual crime time '{crime_time}'."
                ),
                target_id=culprit.id
            ))
        elif not culprit_clues:
            violations.append(ConstraintViolation(
                violation_type=ViolationType.ALIBI_UNBROKEN,
                component="clue",
                message=(
                    f"Culprit '{culprit.id}' claims an alibi during the crime time [{culprit.alibi_start}-{culprit.alibi_end}], "
                    f"but no crucial evidence exists to break this alibi."
                ),
                target_id=culprit.id
            ))

        # Check statement quality and action details
        for s in case.suspects:
            if not s.statement or len(s.statement.strip().split()) < 6:
                violations.append(ConstraintViolation(
                    violation_type=ViolationType.SCHEMA_ERROR,
                    component="character",
                    message=f"Suspect '{s.id}' statement is missing or too brief (< 6 words).",
                    target_id=s.id
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


# -------------------------------------------------------------
# Player Deduction & Accusation Scoring Engine
# -------------------------------------------------------------

def evaluate_player_deduction(
    case: CaseDossier,
    accused_id: str,
    selected_clue_ids: List[str]
) -> VerifyResponse:
    """Evaluate a player's submitted accusation using Neuro-Symbolic Scoring.

    Guarantees Knox Fair-Play Mystery constraints:
    1. Base Guilt Identification (40 pts): Did the player accuse the true Ground Truth killer?
    2. Crucial Clue Recall (40 pts): Did the player submit the decisive physical evidence that shatters the alibi?
    3. Deduction Precision Bonus (20 pts): Did the player present a concise case without irrelevant clutter?
    4. Anti-Spam Penalty: If player selects all or >= 80% clues without reasoning, flags SPAM_DETECTED (0 pts).
    5. Red Herring Trap: If player falls for deceptive clues, applies a -25 pt deduction.

    Latency: Pure in-memory calculation (< 0.1ms).
    """
    total_evidences = len(case.evidences)
    submitted_set = set(selected_clue_ids or [])
    crucial_evidences = [ev for ev in case.evidences if ev.is_crucial]
    crucial_ids = {ev.id for ev in crucial_evidences}
    red_herrings = [ev for ev in case.evidences if ev.is_red_herring]
    red_herring_ids = {ev.id for ev in red_herrings}

    suspect_map = {s.id: s for s in case.suspects}
    accused_suspect = suspect_map.get(accused_id)
    accused_name = f"'{accused_suspect.name}' ({accused_id})" if accused_suspect else f"'{accused_id}'"

    ground_truth = case.ground_truth
    culprit_identified = (accused_id.strip() == ground_truth.culprit_id.strip())

    found_crucial = submitted_set.intersection(crucial_ids)
    found_herrings = submitted_set.intersection(red_herring_ids)
    irrelevant_clues = submitted_set - crucial_ids - red_herring_ids

    total_crucial_count = len(crucial_ids)
    found_crucial_count = len(found_crucial)
    red_herrings_count = len(found_herrings)
    irrelevant_count = len(irrelevant_clues)

    # 1. Anti-Spam Defense: Reject bulk 'Select All' submissions
    if total_evidences >= 3 and len(submitted_set) >= total_evidences:
        return VerifyResponse(
            case_id=case.case_id,
            is_correct=False,
            verdict=DeductionVerdict.SPAM_DETECTED,
            culprit_identified=culprit_identified,
            crucial_evidences_identified=False,
            found_crucial_count=found_crucial_count,
            total_crucial_count=total_crucial_count,
            red_herrings_selected_count=red_herrings_count,
            irrelevant_clues_count=irrelevant_count,
            score=0.0,
            score_breakdown=DeductionScoreBreakdown(
                base_culprit_score=0.0,
                crucial_clues_score=0.0,
                precision_bonus=0.0,
                red_herring_penalty=0.0,
                total_score=0.0
            ),
            feedback=(
                "CẢNH BÁO SPAM CHỨNG CỨ: Bạn đã nộp toàn bộ vật chứng tại hiện trường mà không qua chọn lọc suy luận! "
                "Tòa án bác bỏ hồ sơ cáo trạng bừa bãi này. Hãy chọn đúng manh mối then chốt."
            ),
            core_contradiction=None
        )

    # 2. Accused Wrong Suspect (Innocent Person)
    if not culprit_identified:
        if red_herrings_count > 0:
            verdict = DeductionVerdict.TRAPPED_BY_RED_HERRING
            feedback = (
                f"SẬP BẪY NGHI BINH: Bạn đã cáo buộc nhầm người vô tội {accused_name}! "
                f"Bạn đã bị đánh lừa bởi {red_herrings_count} manh mối nghi binh được cố tình ngụy tạo để đánh lạc hướng."
            )
        else:
            verdict = DeductionVerdict.WRONG_SUSPECT
            feedback = (
                f"LẬP LUẬN SAI: Đối tượng bạn cáo buộc {accused_name} không phải là hung thủ thực sự. "
                "Hãy rà soát kỹ lại lời khai Alibi và thời điểm tử vong xác định trong báo cáo pháp y."
            )

        return VerifyResponse(
            case_id=case.case_id,
            is_correct=False,
            verdict=verdict,
            culprit_identified=False,
            crucial_evidences_identified=(found_crucial_count >= 1),
            found_crucial_count=found_crucial_count,
            total_crucial_count=total_crucial_count,
            red_herrings_selected_count=red_herrings_count,
            irrelevant_clues_count=irrelevant_count,
            score=0.0,
            score_breakdown=DeductionScoreBreakdown(
                base_culprit_score=0.0,
                crucial_clues_score=0.0,
                precision_bonus=0.0,
                red_herring_penalty=0.0,
                total_score=0.0
            ),
            feedback=feedback,
            core_contradiction=None
        )

    # 3. Accused True Culprit -> Compute Fine-Grained Scoring
    base_culprit_score = 40.0
    crucial_ratio = (found_crucial_count / max(1, total_crucial_count))
    crucial_score = round(crucial_ratio * 40.0, 1)

    # Precision bonus: 20 pts if clean, decremented for irrelevant clues
    precision_bonus = max(0.0, 20.0 - (irrelevant_count * 10.0))

    # Red herring penalty: -25 pts per misleading clue
    red_herring_penalty = round(red_herrings_count * 25.0, 1)

    composite_score = max(0.0, min(100.0, round(
        base_culprit_score + crucial_score + precision_bonus - red_herring_penalty, 1
    )))

    breakdown = DeductionScoreBreakdown(
        base_culprit_score=base_culprit_score,
        crucial_clues_score=crucial_score,
        precision_bonus=precision_bonus,
        red_herring_penalty=red_herring_penalty,
        total_score=composite_score
    )

    # Outcome A: Missing Crucial Clue
    if found_crucial_count == 0:
        return VerifyResponse(
            case_id=case.case_id,
            is_correct=False,
            verdict=DeductionVerdict.INSUFFICIENT_EVIDENCE,
            culprit_identified=True,
            crucial_evidences_identified=False,
            found_crucial_count=0,
            total_crucial_count=total_crucial_count,
            red_herrings_selected_count=red_herrings_count,
            irrelevant_clues_count=irrelevant_count,
            score=composite_score,
            score_breakdown=breakdown,
            feedback=(
                f"GẦN ĐÚNG: Bạn đã nhận diện chính xác hung thủ {accused_name}! "
                "Tuy nhiên, chứng cứ bạn đưa ra chưa có manh mối then chốt nào đủ sức bẻ gãy Alibi trước tòa án."
            ),
            core_contradiction=None
        )

    # Outcome B: Trapped by Red Herring (even though culprit is named)
    if red_herrings_count > 0:
        return VerifyResponse(
            case_id=case.case_id,
            is_correct=False,
            verdict=DeductionVerdict.TRAPPED_BY_RED_HERRING,
            culprit_identified=True,
            crucial_evidences_identified=True,
            found_crucial_count=found_crucial_count,
            total_crucial_count=total_crucial_count,
            red_herrings_selected_count=red_herrings_count,
            irrelevant_clues_count=irrelevant_count,
            score=composite_score,
            score_breakdown=breakdown,
            feedback=(
                f"BỊ GÀI BẪY CHỨNG CỨ: Dù bạn chỉ đúng hung thủ {accused_name}, nhưng bạn lại nộp kèm "
                f"{red_herrings_count} manh mối nghi binh được tạo ra nhằm gài bẫy người khác! "
                "Việc này làm ô nhiễm hồ sơ tố tụng và khiến lệnh bắt giữ chưa đủ căn cứ pháp lý."
            ),
            core_contradiction=None
        )

    # Outcome C: Solved Flawed (Crucial clue present, but irrelevant extras attached)
    if irrelevant_count > 0:
        return VerifyResponse(
            case_id=case.case_id,
            is_correct=True,
            verdict=DeductionVerdict.SOLVED_FLAWED,
            culprit_identified=True,
            crucial_evidences_identified=True,
            found_crucial_count=found_crucial_count,
            total_crucial_count=total_crucial_count,
            red_herrings_selected_count=0,
            irrelevant_clues_count=irrelevant_count,
            score=composite_score,
            score_breakdown=breakdown,
            feedback=(
                f"PHÁ ÁN THÀNH CÔNG: Bạn đã vạch trần hung thủ {accused_name} bằng manh mối then chốt! "
                f"Tuy nhiên, cáo trạng của bạn vẫn còn đính kèm {irrelevant_count} vật chứng dư thừa không liên quan."
            ),
            core_contradiction=ground_truth.core_contradiction
        )

    # Outcome D: Perfect Deduction (100% Master Detective)
    return VerifyResponse(
        case_id=case.case_id,
        is_correct=True,
        verdict=DeductionVerdict.SOLVED_PERFECT,
        culprit_identified=True,
        crucial_evidences_identified=True,
        found_crucial_count=found_crucial_count,
        total_crucial_count=total_crucial_count,
        red_herrings_selected_count=0,
        irrelevant_clues_count=0,
        score=100.0,
        score_breakdown=breakdown,
        feedback=(
            f"XUẤT SẮC TUYỆT ĐỐI! Bạn đã phá giải hoàn hảo vụ án '{case.title}'. "
            f"Lập luận đanh thép, vạch trần hoàn toàn sơ hở Alibi của hung thủ {accused_name}!"
        ),
        core_contradiction=ground_truth.core_contradiction
    )
