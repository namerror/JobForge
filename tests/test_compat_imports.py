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
