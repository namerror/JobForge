from __future__ import annotations

import sys

from app.skill_selection import baseline_filter as _baseline_filter

sys.modules[__name__] = _baseline_filter
