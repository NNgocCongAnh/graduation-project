"""Code-level randomisation of suspect and evidence identifiers before a case is published.

LLMs exhibit strong positional bias when picking identifiers (e.g. choosing SUSP-02 in
~87% of cases, and always placing the murder weapon at EV-05 / alibi-breaker at EV-04).
Instead of expecting the LLM to act as a uniform RNG, we apply a uniformly random
bijective relabelling across BOTH suspects (SUSP-01..0N) and evidences (EV-01..0M):

    original [01, 02, 03] -> shuffled e.g. [03, 01, 02]
    old SUSP-01 -> SUSP-03, old SUSP-02 (culprit) -> SUSP-01, old SUSP-03 -> SUSP-02
    and arrays are re-ordered by their new sequential ID (01, 02, 03).

All structured links (culprit_id, linked_suspect_id, clue_ids, target_suspect_id) and
every free-text mention across the dossier are updated atomically in a single regex pass
so no collision can occur and case logic remains 100% invariant.
"""

from __future__ import annotations

import random
import re
from typing import Any, Dict, Optional

from models import CaseDossier

_ID_RE = re.compile(r"SUSP-\d{2}|EV-\d{2}")
_SYSTEM_RNG = random.SystemRandom()


def _relabel(obj: Any, mapping: Dict[str, str]) -> Any:
    """Recursively replace every suspect/evidence ID token in strings, dict keys, and lists."""
    if isinstance(obj, str):
        return _ID_RE.sub(lambda m: mapping.get(m.group(0), m.group(0)), obj)
    if isinstance(obj, list):
        return [_relabel(v, mapping) for v in obj]
    if isinstance(obj, dict):
        return {_relabel(k, mapping): _relabel(v, mapping) for k, v in obj.items()}
    return obj


def shuffle_case_ids(
    case: CaseDossier,
    rng: Optional[random.Random] = None,
    shuffle_evidences: bool = True,
) -> CaseDossier:
    """Return a NEW dossier whose suspect IDs (and optionally evidence IDs) are randomly permuted.

    The input object is not modified. After applying the random ID permutation, `suspects`
    and `evidences` are sorted by their new sequential IDs so display order stays clean
    (SUSP-01..0N, EV-01..0M) while culprit and crucial/weapon slots are uniformly random.
    """
    rng = rng or _SYSTEM_RNG

    # 1. Build bijective random permutation for suspects
    susp_ids = [s.id for s in case.suspects]
    susp_shuffled = susp_ids[:]
    rng.shuffle(susp_shuffled)
    mapping: Dict[str, str] = dict(zip(susp_ids, susp_shuffled))

    # 2. Build bijective random permutation for evidences
    if shuffle_evidences and case.evidences:
        ev_ids = [e.id for e in case.evidences]
        ev_shuffled = ev_ids[:]
        rng.shuffle(ev_shuffled)
        mapping.update(zip(ev_ids, ev_shuffled))

    # 3. Single-pass atomic relabel across entire dossier
    data = _relabel(case.model_dump(mode="json"), mapping)

    # 4. Sort lists sequentially by new IDs so positions change along with IDs
    data["suspects"].sort(key=lambda s: s["id"])
    if shuffle_evidences and data.get("evidences"):
        data["evidences"].sort(key=lambda e: e["id"])

    return CaseDossier.model_validate(data)


# Backwards-compatible alias used by main.py and tests
shuffle_suspect_ids = shuffle_case_ids
