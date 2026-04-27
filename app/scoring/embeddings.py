from __future__ import annotations

import sys

from app.skill_selection.scoring import embeddings as _embeddings

sys.modules[__name__] = _embeddings
