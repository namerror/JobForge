from __future__ import annotations

import sys

from app.resume_generation import assembly as _assembly

sys.modules[__name__] = _assembly
