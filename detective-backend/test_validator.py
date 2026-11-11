"""Unit tests for Rule-Based Validator Engine and Game Engine Logic."""

import pytest
from models import CaseDossier, Victim, Suspect, Evidence, GroundTruth, ForensicData
from validator import validate_case_logic, is_time_in_interval, calculate_henssge_pmi_bounds
from llm_service import CaseGeneratorService


def test_sample_case_validity():
    """Verify that the baseline seed sample case passes all validation rules."""
    sample = CaseGeneratorService.get_sample_case()
    is_valid, errors = validate_case_logic(sample)
    assert is_valid is True, f"Sample case validation failed: {errors}"
    assert len(errors) == 0


def test_duplicate_suspect_id_detection():
    """Validator should reject cases with duplicated suspect IDs."""
    sample = CaseGeneratorService.get_sample_case()
    # Introduce duplicate ID
    sample.suspects[1].id = "SUSP-01"

    is_valid, errors = validate_case_logic(sample)
    assert is_valid is False
    assert any("Duplicate suspect ID" in err for err in errors)


def test_missing_crucial_evidence_detection():
    """Validator should reject cases with 0 crucial evidence."""
    sample = CaseGeneratorService.get_sample_case()
    for ev in sample.evidences:
        ev.is_crucial = False

    is_valid, errors = validate_case_logic(sample)
    assert is_valid is False
    assert any("at least 1 crucial evidence" in err for err in errors)


def test_crime_time_outside_tod_window():
    """Validator should flag when actual crime time is outside forensic TOD range."""
    sample = CaseGeneratorService.get_sample_case()
    # Move crime time to 18:00 while TOD is 21:00-22:30
    sample.ground_truth.actual_crime_time = "18:00"

    is_valid, errors = validate_case_logic(sample)
    assert is_valid is False
    assert any("outside the forensic estimated TOD window" in err for err in errors)


def test_multiple_culprits_rejection():
    """Validator should reject cases with more than 1 culprit flagged."""
    sample = CaseGeneratorService.get_sample_case()
    sample.suspects[1].is_culprit = True  # Second culprit

    is_valid, errors = validate_case_logic(sample)
    assert is_valid is False
    assert any("must have exactly 1 culprit" in err for err in errors)


def test_time_interval_helper():
    """Test time interval utility functions."""
    assert is_time_in_interval("21:40", "21:00", "22:30") is True
    assert is_time_in_interval("20:59", "21:00", "22:30") is False
    assert is_time_in_interval("22:31", "21:00", "22:30") is False


def test_neuro_symbolic_diagnostics():
    """Verify that fine-grained diagnostic violations target the correct component for localized repair."""
    from validator import validate_case_diagnostics
    from models import ViolationType

    sample = CaseGeneratorService.get_sample_case()
    # Strip crucial clues to trigger clue-level violation
    for ev in sample.evidences:
        ev.is_crucial = False

    diag = validate_case_diagnostics(sample)
    assert diag.is_valid is False
    assert len(diag.violations) >= 1
    clue_violations = [v for v in diag.violations if v.component == "clue"]
    assert len(clue_violations) >= 1
    assert any(v.violation_type == ViolationType.NO_CRUCIAL_CLUE for v in clue_violations)
    assert "CLUE:no_crucial_clue" in diag.diagnostic_feedback


def test_reasoning_chain_validation():
    """Verify that reasoning chain citing non-existent evidence is flagged."""
    from validator import validate_case_diagnostics
    from models import DeductionStep

    sample = CaseGeneratorService.get_sample_case()
    # Cite a hallucinated evidence ID
    sample.reasoning_chain.steps.append(
        DeductionStep(
            step_number=99,
            clue_ids=["EV-GHOST-999"],
            inference="Manh mối ma quái không có trong hồ sơ.",
            target_suspect_id="SUSP-01"
        )
    )

    diag = validate_case_diagnostics(sample)
    assert diag.is_valid is False
    assert any(v.component == "reasoning" and "EV-GHOST-999" in v.message for v in diag.violations)


def test_sample_case_metadata_and_reasoning_complete():
    """Verify sample seed case has valid multi-hop reasoning chain and telemetry metadata."""
    sample = CaseGeneratorService.get_sample_case()
    assert sample.reasoning_chain is not None
    assert len(sample.reasoning_chain.steps) >= 2
    assert sample.metadata is not None
    assert sample.metadata.pipeline_version == "2.0-neuro-symbolic"


# -------------------------------------------------------------
# Academic Benchmark Tests: Player Deduction Scoring & Anti-Spam
# -------------------------------------------------------------

def test_player_deduction_perfect_scenario():
    """KỊCH BẢN 1: Người chơi suy luận sắc bén (Chính xác 100%).

    - Chỉ định chính xác hung thủ (SUSP-01).
    - Cung cấp đầy đủ các manh mối then chốt (EV-01, EV-02) bẻ gãy Alibi.
    - Không nộp bất kỳ chứng cứ nghi binh (Red Herring) hay đồ vật rác nào.
    - Kỳ vọng: is_correct=True, verdict=SOLVED_PERFECT, score=100.0, core_contradiction được tiết lộ.
    """
    from validator import evaluate_player_deduction
    from models import DeductionVerdict

    sample = CaseGeneratorService.get_sample_case()
    response = evaluate_player_deduction(
        case=sample,
        accused_id="SUSP-01",
        selected_clue_ids=["EV-01", "EV-02"]
    )

    assert response.is_correct is True
    assert response.verdict == DeductionVerdict.SOLVED_PERFECT
    assert response.culprit_identified is True
    assert response.crucial_evidences_identified is True
    assert response.found_crucial_count == 2
    assert response.total_crucial_count == 2
    assert response.red_herrings_selected_count == 0
    assert response.irrelevant_clues_count == 0
    assert response.score == 100.0
    assert response.core_contradiction is not None
    assert "XUẤT SẮC TUYỆT ĐỐI" in response.feedback


def test_player_deduction_wrong_suspect_scenario():
    """KỊCH BẢN 2: Người chơi cáo buộc sai hung thủ (Bắt nhầm người vô tội).

    - Cáo buộc Bác sĩ Julian Grey (SUSP-02) - một nghi phạm hoàn toàn vô tội.
    - Dù có chọn chứng cứ then chốt EV-01 hay không, kết luận vẫn là sai lầm nghiêm trọng.
    - Kỳ vọng: is_correct=False, verdict=WRONG_SUSPECT, score=0.0, core_contradiction=None.
    """
    from validator import evaluate_player_deduction
    from models import DeductionVerdict

    sample = CaseGeneratorService.get_sample_case()
    response = evaluate_player_deduction(
        case=sample,
        accused_id="SUSP-02",
        selected_clue_ids=["EV-01"]
    )

    assert response.is_correct is False
    assert response.verdict == DeductionVerdict.WRONG_SUSPECT
    assert response.culprit_identified is False
    assert response.score == 0.0
    assert response.core_contradiction is None
    assert "LẬP LUẬN SAI" in response.feedback
    assert "Julian Grey" in response.feedback


def test_player_deduction_logic_traps_and_spam_scenario():
    """KỊCH BẢN 3: Bẫy logic (Sập bẫy Red Herring & Lừa chọn toàn bộ Select-All).

    - Phần A (Sập bẫy Nghi binh): Người chơi chọn đúng hung thủ SUSP-01 nhưng bị đánh lừa
      bởi manh mối EV-03 (Hộp thuốc an thần dở dang được ngụy tạo).
      Kỳ vọng: verdict=TRAPPED_BY_RED_HERRING, is_correct=False, bị trừ điểm nặng nề.

    - Phần B (Hành vi gian lận Spam Select-All): Người chơi tích chọn bừa bãi toàn bộ
      tất cả các manh mối hiện trường [EV-01, EV-02, EV-03].
      Kỳ vọng: Hệ thống kích hoạt phòng vệ SPAM_DETECTED, is_correct=False, score=0.0.
    """
    from validator import evaluate_player_deduction
    from models import DeductionVerdict

    sample = CaseGeneratorService.get_sample_case()

    # --- Phần A: Sập bẫy Red Herring ---
    response_trap = evaluate_player_deduction(
        case=sample,
        accused_id="SUSP-01",
        selected_clue_ids=["EV-01", "EV-03"]
    )
    assert response_trap.is_correct is False
    assert response_trap.verdict == DeductionVerdict.TRAPPED_BY_RED_HERRING
    assert response_trap.red_herrings_selected_count == 1
    assert response_trap.score <= 65.0
    assert "BỊ GÀI BẪY CHỨNG CỨ" in response_trap.feedback
    assert response_trap.core_contradiction is None

    # --- Phần B: Gian lận Select-All Spam ---
    response_spam = evaluate_player_deduction(
        case=sample,
        accused_id="SUSP-01",
        selected_clue_ids=["EV-01", "EV-02", "EV-03"]
    )
    assert response_spam.is_correct is False
    assert response_spam.verdict == DeductionVerdict.SPAM_DETECTED
    assert response_spam.score == 0.0
    assert "CẢNH BÁO SPAM CHỨNG CỨ" in response_spam.feedback


