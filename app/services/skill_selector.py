from __future__ import annotations

import sys

from app.skill_selection import selector as _selector

sys.modules[__name__] = _selector
