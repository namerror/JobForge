from __future__ import annotations

import sys

from app.resume_generation import latex as _latex

sys.modules[__name__] = _latex
