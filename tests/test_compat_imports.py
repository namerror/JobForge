import importlib


def test_legacy_skill_selection_imports_alias_canonical_modules():
    legacy_models = importlib.import_module("app.models")
    canonical_models = importlib.import_module("app.skill_selection.models")
    legacy_baseline = importlib.import_module("app.scoring.baseline")
    canonical_baseline = importlib.import_module("app.skill_selection.scoring.baseline")
    legacy_llm_client = importlib.import_module("app.services.llm_client")
    canonical_llm_client = importlib.import_module("app.skill_selection.llm_client")

    assert legacy_models is canonical_models
    assert legacy_baseline is canonical_baseline
    assert legacy_llm_client is canonical_llm_client


def test_legacy_project_llm_client_import_aliases_canonical_module():
    legacy_project_llm = importlib.import_module("app.services.project_llm_client")
    canonical_project_llm = importlib.import_module("app.project_selection.llm_client")

    assert legacy_project_llm is canonical_project_llm


def test_legacy_resume_generation_imports_alias_canonical_modules():
    legacy_selection = importlib.import_module("resume_generation.selection")
    canonical_selection = importlib.import_module("app.resume_generation.selection")
    legacy_main = importlib.import_module("resume_generation.main")
    canonical_main = importlib.import_module("app.resume_generation.main")
    legacy_pdf = importlib.import_module("resume_generation.pdf")
    canonical_pdf = importlib.import_module("app.resume_generation.pdf")

    assert legacy_selection is canonical_selection
    assert legacy_main is canonical_main
    assert legacy_pdf is canonical_pdf
