"""Tests for code-level suspect ID relabelling (id_shuffle.py)."""

import random
from collections import Counter

from id_shuffle import shuffle_suspect_ids
from llm_service import CaseGeneratorService
from validator import validate_case_diagnostics


def _name_of(case, suspect_id):
    return next(s.name for s in case.suspects if s.id == suspect_id)


def test_relabelled_case_stays_valid_and_consistent():
    original = CaseGeneratorService.get_sample_case()
    original_culprit = _name_of(original, original.ground_truth.culprit_id)
    links_by_evidence = {
        e.id: _name_of(original, e.linked_suspect_id) for e in original.evidences if e.linked_suspect_id
    }

    for seed in range(20):
        shuffled = shuffle_suspect_ids(original, random.Random(seed))
        assert validate_case_diagnostics(shuffled).is_valid
        # the same person is still the culprit, under whatever new ID
        assert _name_of(shuffled, shuffled.ground_truth.culprit_id) == original_culprit
        assert next(s for s in shuffled.suspects if s.is_culprit).name == original_culprit
        # every evidence still points to the same person
        for e in shuffled.evidences:
            if e.linked_suspect_id:
                assert _name_of(shuffled, e.linked_suspect_id) == links_by_evidence[e.id]
        assert sorted(s.id for s in shuffled.suspects) == sorted(s.id for s in original.suspects)


def test_input_case_is_not_mutated():
    original = CaseGeneratorService.get_sample_case()
    before = original.model_dump(mode="json")
    shuffle_suspect_ids(original, random.Random(1))
    assert original.model_dump(mode="json") == before


def test_culprit_id_is_uniformly_distributed():
    original = CaseGeneratorService.get_sample_case()
    rng = random.Random(2026)
    counts = Counter(shuffle_suspect_ids(original, rng).ground_truth.culprit_id for _ in range(3000))
    n_ids = len(original.suspects)
    for sid in (s.id for s in original.suspects):
        assert abs(counts[sid] / 3000 - 1 / n_ids) < 0.04, counts


def test_free_text_mentions_are_relabelled_together():
    original = CaseGeneratorService.get_sample_case()
    rng = random.Random(7)
    shuffled = shuffle_suspect_ids(original, rng)
    mapping = {}
    for s in original.suspects:
        mapping[s.id] = next(t.id for t in shuffled.suspects if t.name == s.name)
    old_text = original.model_dump_json()
    new_text = shuffled.model_dump_json()
    for old_id, new_id in mapping.items():
        assert old_text.count(f'"{old_id}"') == new_text.count(f'"{new_id}"')
