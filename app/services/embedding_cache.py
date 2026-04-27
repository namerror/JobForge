from __future__ import annotations

import sys

from app.skill_selection import embedding_cache as _embedding_cache

sys.modules[__name__] = _embedding_cache
