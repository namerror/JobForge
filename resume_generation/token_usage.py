from __future__ import annotations

import sys

from app.resume_generation import token_usage as _token_usage

sys.modules[__name__] = _token_usage
