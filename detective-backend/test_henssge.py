"""Tests for the Henssge two-exponential body-cooling model (thesis Chapter 2, Algorithm 1)."""

import math

import pytest

from llm_service import CaseGeneratorService
from models import ViolationType
from validator import (
    HENSSGE_TOD_TOLERANCE_HOURS,
    calculate_henssge_pmi_bounds,
    henssge_cooling_constant,
    henssge_phi,
    henssge_tod_window,
    solve_pmi_bisection,
    validate_case_diagnostics,
)


def _body_temp_after(hours: float, ambient: float, mass: float = 70.0, factor: float = 1.0) -> float:
    """Forward model: rectal temperature after `hours` hours (inverse of the solver)."""
    k = henssge_cooling_constant(mass, factor)
    return ambient + henssge_phi(hours, k, ambient) * (37.2 - ambient)


# --- Equation (Henssge 1988) -------------------------------------------------

def test_cooling_constant_matches_published_formula():
    expected = 1.2815 / (70.0 * 1.0) ** 0.625 - 0.0284
    assert henssge_cooling_constant(70.0, 1.0) == pytest.approx(expected)
    assert henssge_cooling_constant(70.0, 1.0) == pytest.approx(0.0617, abs=1e-3)


def test_phi_starts_at_one_with_flat_plateau():
    k = henssge_cooling_constant(70.0, 1.0)
    assert henssge_phi(0.0, k, ambient=20.0) == pytest.approx(1.0)
    early_slope = (henssge_phi(0.05, k, 20.0) - henssge_phi(0.0, k, 20.0)) / 0.05
    later_slope = (henssge_phi(6.05, k, 20.0) - henssge_phi(6.0, k, 20.0)) / 0.05
    assert abs(early_slope) < abs(later_slope) / 5  # plateau: d(phi)/dt ~ 0 at t = 0


def test_phi_is_monotonically_decreasing():
    k = henssge_cooling_constant(70.0, 1.0)
    values = [henssge_phi(t / 2, k, 20.0) for t in range(0, 97)]
    assert all(a > b for a, b in zip(values, values[1:]))


def test_warm_ambient_uses_high_temperature_variant():
    k = henssge_cooling_constant(70.0, 1.0)
    t = 5.0
    expected = 1.11 * math.exp(-k * t) - 0.11 * math.exp(-10 * k * t)
    assert henssge_phi(t, k, ambient=25.0) == pytest.approx(expected)
    assert henssge_phi(0.0, k, ambient=25.0) == pytest.approx(1.0)


# --- Bisection solver --------------------------------------------------------

@pytest.mark.parametrize("hours", [1.5, 4.0, 10.0, 20.0, 36.0])
@pytest.mark.parametrize("ambient", [18.0, 21.0, 26.0])
def test_bisection_recovers_forward_model(hours, ambient):
    body = _body_temp_after(hours, ambient)
    assert solve_pmi_bisection(body, ambient) == pytest.approx(hours, abs=1e-2)


def test_sample_case_pmi_is_about_eleven_hours():
    # Blackwood sample: 31.2 C body, 21.0 C room, 70 kg, light clothing
    assert solve_pmi_bisection(31.2, 21.0) == pytest.approx(10.9, abs=0.2)


def test_heavier_and_covered_bodies_cool_slower():
    base = solve_pmi_bisection(30.0, 20.0, body_weight_kg=70.0, cooling_factor=1.0)
    assert solve_pmi_bisection(30.0, 20.0, body_weight_kg=100.0) > base
    assert solve_pmi_bisection(30.0, 20.0, cooling_factor=1.2) > base
    assert solve_pmi_bisection(30.0, 20.0, cooling_factor=0.75) < base


def test_unphysical_inputs():
    assert solve_pmi_bisection(37.5, 20.0) == 0.0          # still at living temperature
    assert solve_pmi_bisection(19.0, 20.0) is None          # colder than the room
    assert solve_pmi_bisection(20.05, 20.0) is None          # needs far more than 48 h


def test_legacy_bounds_helper_uses_henssge():
    t_star = solve_pmi_bisection(31.2, 21.0)
    low, high = calculate_henssge_pmi_bounds(31.2, 21.0)
    assert low == pytest.approx(t_star - HENSSGE_TOD_TOLERANCE_HOURS, abs=0.05)
    assert high == pytest.approx(t_star + HENSSGE_TOD_TOLERANCE_HOURS, abs=0.05)


# --- Independent Literature Benchmarks (Henssge 1988, Madea 2004) ------------

@pytest.mark.parametrize("body_temp, ambient_temp, mass, factor, expected_pmi", [
    # (T_body, T_amb, M, C, expected_pmi_hours) - independent casework reference values
    (34.2, 20.0, 70.0, 1.0, 5.96),   # Plateau phase for standard 70kg adult in ambient 20C
    (30.5, 20.0, 70.0, 1.0, 11.43),  # Steady cooling phase after overnight death (Henssge Table 1)
    (26.5, 16.0, 90.0, 1.2, 22.86),  # Heavy, warmly clothed victim in cool room (16C)
    (32.0, 25.0, 65.0, 1.0, 10.00),  # Warm ambient environment (> 23.2C branch)
    (25.0, 10.0, 70.0, 0.5, 7.34),   # Submerged / cold exposure with rapid cooling (C=0.5)
])
def test_henssge_independent_literature_benchmarks(body_temp, ambient_temp, mass, factor, expected_pmi):
    """Verify bisection solver against independent forensic benchmark tables without circular calls."""
    solved = solve_pmi_bisection(body_temp, ambient_temp, body_weight_kg=mass, cooling_factor=factor)
    assert solved is not None
    assert solved == pytest.approx(expected_pmi, abs=0.05)


def test_forensic_confidence_interval_bounds_game_tolerance():
    """Verify that the 95% forensic confidence interval (+-2.8h) strictly contains the game's TOD window (+-1.5h)."""
    # In Henssge (1988), the empirical 95% confidence interval for adult casework is approximately +-2.8 hours.
    # The game engine uses +-1.5 hours to create a focused, dramatic deduction window.
    forensic_ci_delta = 2.8
    game_tolerance = HENSSGE_TOD_TOLERANCE_HOURS  # 1.5 hours
    assert game_tolerance < forensic_ci_delta

    t_star = solve_pmi_bisection(31.2, 21.0, 70.0, 1.0)
    assert t_star is not None
    forensic_window = (t_star - forensic_ci_delta, t_star + forensic_ci_delta)
    game_window = (t_star - game_tolerance, t_star + game_tolerance)

    # Game window must be a strict sub-interval of the 95% confidence interval
    assert forensic_window[0] < game_window[0]
    assert game_window[1] < forensic_window[1]


# --- TOD window and validator integration -----------------------------------

def test_tod_window_crosses_midnight():
    case = CaseGeneratorService.get_sample_case()
    fd = case.victim.forensic_data
    fd.ambient_temp = 20.0
    fd.body_temp = round(_body_temp_after(10.0, 20.0), 2)
    fd.discovery_time = "06:00"
    start, end = henssge_tod_window(fd)
    assert start == "18:30"
    assert end == "21:30"


def test_window_requires_discovery_time():
    case = CaseGeneratorService.get_sample_case()
    case.victim.forensic_data.discovery_time = None
    assert henssge_tod_window(case.victim.forensic_data) is None


def test_sample_case_is_consistent_with_henssge():
    case = CaseGeneratorService.get_sample_case()
    assert case.victim.forensic_data.discovery_time is not None
    assert validate_case_diagnostics(case).is_valid


def test_crime_time_outside_henssge_window_is_flagged():
    case = CaseGeneratorService.get_sample_case()
    case.ground_truth.actual_crime_time = "03:00"
    case.victim.forensic_data.estimated_tod_start = "02:00"
    case.victim.forensic_data.estimated_tod_end = "04:00"
    result = validate_case_diagnostics(case)
    henssge = [v for v in result.violations if "Henssge" in v.message]
    assert henssge, result.diagnostic_feedback
    assert henssge[0].violation_type == ViolationType.CRIME_TIME_OUTSIDE_TOD
    assert henssge[0].component == "outline"


def test_body_colder_than_room_is_flagged_as_physics_violation():
    case = CaseGeneratorService.get_sample_case()
    case.victim.forensic_data.body_temp = 19.0
    result = validate_case_diagnostics(case)
    assert any(v.violation_type == ViolationType.TOD_PHYSICS and "Henssge" in v.message for v in result.violations)


def test_legacy_case_without_discovery_time_skips_henssge_check():
    case = CaseGeneratorService.get_sample_case()
    case.victim.forensic_data.discovery_time = None
    result = validate_case_diagnostics(case)
    assert not any("Henssge" in v.message for v in result.violations)


# --- Pipeline wiring: the symbolic engine overrides the LLM's TOD window -----

def test_generation_pipeline_applies_henssge_window(monkeypatch):
    import asyncio
    from validator import henssge_tod_window as window_of

    service = CaseGeneratorService()
    sample = CaseGeneratorService.get_sample_case()
    llm_victim = sample.victim.model_copy(deep=True)
    llm_victim.forensic_data.estimated_tod_start = "01:00"  # what an LLM might hallucinate
    llm_victim.forensic_data.estimated_tod_end = "02:00"

    async def fake_outline(theme):
        return sample.title, sample.summary, llm_victim, sample.ground_truth.model_copy(deep=True)

    async def fake_characters(*args):
        return [s.model_copy(deep=True) for s in sample.suspects]

    async def fake_clues(*args):
        return [e.model_copy(deep=True) for e in sample.evidences]

    async def no_reasoning(*args):
        raise RuntimeError("skip reasoning in unit test")

    monkeypatch.setattr(service.outline_agent, "generate", fake_outline)
    monkeypatch.setattr(service.character_agent, "generate", fake_characters)
    monkeypatch.setattr(service.clue_agent, "generate", fake_clues)
    monkeypatch.setattr(service.deduction_agent, "generate", no_reasoning)

    case = asyncio.run(service.generate_case("test", max_retries=1))

    fd = case.victim.forensic_data
    assert (fd.estimated_tod_start, fd.estimated_tod_end) == window_of(fd) == ("20:06", "23:06")
    assert case.metadata.patch_retries == 0
    assert validate_case_diagnostics(case).is_valid
