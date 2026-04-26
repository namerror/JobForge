from __future__ import annotations

import sys

from app.skill_selection import models as _models

sys.modules[__name__] = _models
