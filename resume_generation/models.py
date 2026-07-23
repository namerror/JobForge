from __future__ import annotations

import sys

from app.resume_generation import models as _models

sys.modules[__name__] = _models
