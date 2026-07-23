from __future__ import annotations

import sys

from app.resume_generation import bullet_points as _bullet_points

sys.modules[__name__] = _bullet_points
