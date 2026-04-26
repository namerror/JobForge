from __future__ import annotations

import sys

from app.skill_selection.scoring import synonyms as _synonyms

sys.modules[__name__] = _synonyms
