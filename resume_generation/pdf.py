from __future__ import annotations

import sys

if __name__ == "__main__":
    from app.resume_generation.pdf import main

    main()
else:
    from app.resume_generation import pdf as _pdf

    sys.modules[__name__] = _pdf
