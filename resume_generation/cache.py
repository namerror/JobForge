from __future__ import annotations

import sys

from app.resume_generation import cache as _cache

sys.modules[__name__] = _cache
