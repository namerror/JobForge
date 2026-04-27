from __future__ import annotations

import sys

from app.skill_selection import llm_client as _llm_client

sys.modules[__name__] = _llm_client
