from __future__ import annotations

import sys

from app.skill_selection.scoring import role_profiles as _role_profiles

sys.modules[__name__] = _role_profiles
