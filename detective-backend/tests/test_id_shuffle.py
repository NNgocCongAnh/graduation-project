"""Tests for code-level suspect and evidence ID relabelling (id_shuffle.py)."""

import random
from collections import Counter

from id_shuffle import shuffle_case_ids, shuffle_suspect_ids
from llm_service import CaseGeneratorService
from validator import validate_case_diagnostics


def _name_of(case, suspect_id):
    return next(s.name for s in case.suspects if s.id == suspect_id)


def test_relabelled_case_stays_valid_and_consistent():
    original = CaseGeneratorService.get_sample_case()
    original_culprit = _name_of(original, original.ground_truth.culprit_id)
    links_by_title = {
        e.title: _name_of(original, e.linked_suspect_id)
        for e in original.evidences
        if e.linked_suspect_id
    }
    weapon_titles = {e.title for e in original.evidences if e.is_weapon}

    for seed in range(20):
        shuffled = shuffle_case_ids(original, random.Random(seed))
        assert validate_case_diagnostics(shuffled).is_valid
        # the same person is still the culprit, under whatever new ID
        assert _name_of(shuffled, shuffled.ground_truth.culprit_id) == original_culprit
        assert next(s for s in shuffled.suspects if s.is_culprit).name == original_culprit
        # every evidence still points to the same person and preserves is_weapon
        for e in shuffled.evidences:
            if e.linked_suspect_id:
                assert _name_of(shuffled, e.linked_suspect_id) == links_by_title[e.title]
            assert e.is_weapon == (e.title in weapon_titles)
        assert [s.id for s in shuffled.suspects] == sorted(s.id for s in original.suspects)
        assert [e.id for e in shuffled.evidences] == sorted(e.id for e in original.evidences)


def test_input_case_is_not_mutated():
    original = CaseGeneratorService.get_sample_case()
    before = original.model_dump(mode="json")
    shuffle_suspect_ids(original, random.Random(1))
    assert original.model_dump(mode="json") == before


def test_culprit_and_weapon_ids_are_uniformly_distributed():
    original = CaseGeneratorService.get_sample_case()
    rng = random.Random(2026)
    culprit_counts = Counter()
    weapon_counts = Counter()
    trials = 3000
    for _ in range(trials):
        s_case = shuffle_case_ids(original, rng)
        culprit_counts[s_case.ground_truth.culprit_id] += 1
        w = next((e.id for e in s_case.evidences if e.is_weapon), None)
        if w:
            weapon_counts[w] += 1

    n_susp = len(original.suspects)
    for sid in (s.id for s in original.suspects):
        assert abs(culprit_counts[sid] / trials - 1 / n_susp) < 0.04, culprit_counts

    n_ev = len(original.evidences)
    if weapon_counts:
        for eid in (e.id for e in original.evidences):
            assert abs(weapon_counts[eid] / trials - 1 / n_ev) < 0.04, weapon_counts


def test_free_text_mentions_are_relabelled_together():
    original = CaseGeneratorService.get_sample_case()
    rng = random.Random(7)
    shuffled = shuffle_case_ids(original, rng)

    susp_map = {
        s.id: next(t.id for t in shuffled.suspects if t.name == s.name)
        for s in original.suspects
    }
    ev_map = {
        e.id: next(t.id for t in shuffled.evidences if t.title == e.title)
        for e in original.evidences
    }
    old_text = original.model_dump_json()
    new_text = shuffled.model_dump_json()
    for old_id, new_id in {**susp_map, **ev_map}.items():
        assert old_text.count(f'"{old_id}"') == new_text.count(f'"{new_id}"')
