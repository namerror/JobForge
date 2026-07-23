from __future__ import annotations

import sys

if __name__ == "__main__":
    from app.resume_generation.enrich import main

    raise SystemExit(main())

from app.resume_generation import enrich as _enrich

sys.modules[__name__] = _enrich
