from __future__ import annotations

import sys

from app.resume_generation import config as _config

sys.modules[__name__] = _config
