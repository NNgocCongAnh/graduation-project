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

