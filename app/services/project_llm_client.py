from __future__ import annotations

import sys

from app.project_selection import llm_client as _project_llm_client

sys.modules[__name__] = _project_llm_client
