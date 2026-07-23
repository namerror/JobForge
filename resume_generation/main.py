from __future__ import annotations

import sys

if __name__ == "__main__":
    from app.resume_generation.main import (
        run_resume_generation_pipeline,
        write_resume_latex_from_config,
        write_resume_pdf_from_config,
    )

    resume_result = run_resume_generation_pipeline()
    latex_path = write_resume_latex_from_config(resume_result)
    write_resume_pdf_from_config(latex_path)
else:
    from app.resume_generation import main as _main

    sys.modules[__name__] = _main
