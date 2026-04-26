from __future__ import annotations

import sys

from app.skill_selection import embedding_client as _embedding_client

sys.modules[__name__] = _embedding_client
