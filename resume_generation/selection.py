from __future__ import annotations

import sys

from app.resume_generation import selection as _selection

sys.modules[__name__] = _selection
