"""Code-level randomisation of suspect identifiers before a case is published.

LLMs are poor random number generators: asked to "pick one of SUSP-01..03 in a balanced
way", gpt-4o-mini picked SUSP-02 in 28/30 runs. Instead of asking the model to be
random, the published case gets a uniformly random *relabelling* of its suspect IDs:

    original SUSP-02 (culprit) -> e.g. SUSP-03, SUSP-01 -> SUSP-02, ...

The relabelling is applied consistently to every field and every free-text string
that mentions a suspect ID, and the order of the suspect list is shuffled too, so the
case logic is unchanged (a pure renaming) while the culprit's ID and list position are
uniformly distributed from the player's point of view.
"""

from __future__ import annotations

import random
import re
from typing import Any, Dict, Optional

from models import CaseDossier

_ID_RE = re.compile(r"SUSP-\d{2}")
_SYSTEM_RNG = random.SystemRandom()


def _relabel(obj: Any, mapping: Dict[str, str]) -> Any:
    """Recursively replace every suspect ID token in strings, dict keys and lists."""
    if isinstance(obj, str):
        return _ID_RE.sub(lambda m: mapping.get(m.group(0), m.group(0)), obj)
    if isinstance(obj, list):
        return [_relabel(v, mapping) for v in obj]
    if isinstance(obj, dict):
        return {_relabel(k, mapping): _relabel(v, mapping) for k, v in obj.items()}
    return obj


def shuffle_suspect_ids(case: CaseDossier, rng: Optional[random.Random] = None) -> CaseDossier:
    """Return a NEW dossier whose suspect IDs (and list order) are randomly permuted.

    The input object is not modified. Pass a seeded ``random.Random`` for reproducible tests;
    production uses the operating-system RNG.
    """
    rng = rng or _SYSTEM_RNG
    ids = [s.id for s in case.suspects]
    shuffled = ids[:]
    rng.shuffle(shuffled)
    mapping = dict(zip(ids, shuffled))

    data = _relabel(case.model_dump(mode="json"), mapping)
    rng.shuffle(data["suspects"])
    return CaseDossier.model_validate(data)
