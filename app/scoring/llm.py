from __future__ import annotations

import sys

from app.skill_selection.scoring import llm as _llm

sys.modules[__name__] = _llm
