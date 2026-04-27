from __future__ import annotations

import sys

from app.skill_selection.scoring import baseline as _baseline

sys.modules[__name__] = _baseline
