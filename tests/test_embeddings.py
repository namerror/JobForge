"""Unit tests for app/scoring/embeddings.py"""
import json
import math
import pytest
from unittest.mock import patch

from app.scoring import embeddings
from app.scoring.embeddings import (
    normalize_skill,
    construct_role_text,
    cosine_similarity,
    embedding_rank_skills,
    embedding_select_skills,
)
from app.services.embedding_cache import EmbeddingCache


# ---------------------------------------------------------------------------
# normalize_skill
# ---------------------------------------------------------------------------

def test_normalize_skill_strips_and_lowercases():
    assert normalize_skill("  Python  ") == "python"


def test_normalize_skill_applies_synonym(monkeypatch):
    monkeypatch.setattr(embeddings, "SYNONYM_TO_NORMALIZED", {"js": "javascript"})
    assert normalize_skill("JS") == "javascript"


def test_normalize_skill_unknown_passthrough():
    assert normalize_skill("someunknowntool") == "someunknowntool"


# ---------------------------------------------------------------------------
# construct_role_text
# ---------------------------------------------------------------------------

def test_construct_role_text_with_job_text():
    result = construct_role_text("Backend Engineer", "We use Python and Kafka.")
    assert result == "backend engineer\nWe use Python and Kafka."


def test_construct_role_text_without_job_text():
    result = construct_role_text("  Data Scientist  ", None)
    assert result == "data scientist"


def test_construct_role_text_empty_job_text_falsy():
    result = construct_role_text("SRE", "")
    assert result == "sre"


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

def test_cosine_similarity_identical_vectors():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_opposite_vectors():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_zero_vector_returns_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


# ---------------------------------------------------------------------------
# EmbeddingCache.cache_lookup
# ---------------------------------------------------------------------------

def _make_cache(role_data: dict | None = None, skill_data: dict | None = None) -> EmbeddingCache:
    """Build an EmbeddingCache with pre-populated in-memory dicts, bypassing disk I/O."""
    cache = EmbeddingCache.__new__(EmbeddingCache)
    cache.role_cache = role_data if role_data is not None else {}
    cache.skill_cache = skill_data if skill_data is not None else {}
    cache.model = "test-model"
    cache.dimensions = None
    return cache


def _disable_cache_writes(monkeypatch):
    monkeypatch.setattr(embeddings.cache, "cache_store", lambda *args, **kwargs: None)


def test_cache_lookup_role_hit():
    cache = _make_cache(role_data={"backend engineer": [0.1, 0.2]})
    assert cache.cache_lookup("backend engineer", type="role") == [0.1, 0.2]


def test_cache_lookup_role_miss():
    cache = _make_cache(role_data={})
    assert cache.cache_lookup("unknown role", type="role") is None


def test_cache_lookup_skill_hit():
    cache = _make_cache(skill_data={"python": [0.5, 0.6]})
    assert cache.cache_lookup("python", type="skill") == [0.5, 0.6]


def test_cache_lookup_skill_miss():
    cache = _make_cache(skill_data={})
    assert cache.cache_lookup("rust", type="skill") is None


def test_cache_lookup_invalid_type_raises():
    cache = _make_cache()
    with pytest.raises(ValueError, match="Invalid cache type"):
        cache.cache_lookup("anything", type="invalid")


def test_load_embeddings_cache_loads_json(tmp_path):
    role_data = {"backend engineer": [0.1, 0.2]}
    skill_data = {"python": [0.5, 0.6]}

    role_file = tmp_path / "role_cache.json"
    skill_file = tmp_path / "skill_cache.json"
    role_file.write_text(json.dumps(role_data))
    skill_file.write_text(json.dumps(skill_data))

    cache = EmbeddingCache.__new__(EmbeddingCache)
    cache._ROLE_EMB_CACHE_DIR = role_file
    cache._SKILL_EMB_CACHE_DIR = skill_file
    cache.role_cache, cache.skill_cache = cache._load_embeddings_cache()

    assert cache.role_cache == role_data
    assert cache.skill_cache == skill_data


def test_load_embeddings_cache_missing_files_defaults_to_empty(tmp_path):
    cache = EmbeddingCache.__new__(EmbeddingCache)
    cache._ROLE_EMB_CACHE_DIR = tmp_path / "nonexistent_role.json"
    cache._SKILL_EMB_CACHE_DIR = tmp_path / "nonexistent_skill.json"
    cache.role_cache, cache.skill_cache = cache._load_embeddings_cache()

    assert cache.role_cache == {}
    assert cache.skill_cache == {}


def test_cache_store_persists_role_write_through(tmp_path):
    cache = EmbeddingCache.__new__(EmbeddingCache)
    cache._ROLE_EMB_CACHE_DIR = tmp_path / "role_cache.json"
    cache._SKILL_EMB_CACHE_DIR = tmp_path / "skill_cache.json"
    cache.model = "test-model"
    cache.dimensions = 3
    cache.role_cache = {}
    cache.skill_cache = {}

    cache.cache_store("backend engineer", [0.1, 0.2, 0.3], type="role")

    payload = json.loads(cache._ROLE_EMB_CACHE_DIR.read_text())
    assert payload["model"] == "test-model"
    assert payload["dimensions"] == 3
    assert payload["data"]["backend engineer"] == [0.1, 0.2, 0.3]


def test_cache_store_persists_skill_write_through(tmp_path):
    cache = EmbeddingCache.__new__(EmbeddingCache)
    cache._ROLE_EMB_CACHE_DIR = tmp_path / "role_cache.json"
    cache._SKILL_EMB_CACHE_DIR = tmp_path / "skill_cache.json"
    cache.model = "test-model"
    cache.dimensions = None
    cache.role_cache = {}
    cache.skill_cache = {}

    cache.cache_store("python", [0.5, 0.6], type="skill")

    payload = json.loads(cache._SKILL_EMB_CACHE_DIR.read_text())
    assert payload["model"] == "test-model"
    assert payload["dimensions"] is None
    assert payload["data"]["python"] == [0.5, 0.6]


def test_load_embeddings_cache_rejects_model_mismatch(tmp_path, caplog):
    payload = {"version": 1, "model": "other-model", "dimensions": 3, "data": {"x": [0.1]}}
    role_file = tmp_path / "role_cache.json"
    role_file.write_text(json.dumps(payload))

    cache = EmbeddingCache.__new__(EmbeddingCache)
    cache._ROLE_EMB_CACHE_DIR = role_file
    cache._SKILL_EMB_CACHE_DIR = tmp_path / "skill_cache.json"
    cache.model = "test-model"
    cache.dimensions = 3

    cache.role_cache, cache.skill_cache = cache._load_embeddings_cache()

    assert cache.role_cache == {}


# ---------------------------------------------------------------------------
# embedding_rank_skills
# ---------------------------------------------------------------------------

ROLE_VEC = [1.0, 0.0]
FAKE_SKILL_VECS = [[1.0, 0.0], [0.0, 1.0], [0.7071, 0.7071]]


def test_embedding_rank_skills_empty_returns_empty(monkeypatch):
    _disable_cache_writes(monkeypatch)
    ranked, details = embedding_rank_skills(skills=[], role_vec=ROLE_VEC)
    assert ranked == []
    assert details is None


def test_embedding_rank_skills_empty_dev_mode_returns_empty_dict(monkeypatch):
    _disable_cache_writes(monkeypatch)
    ranked, details = embedding_rank_skills(skills=[], role_vec=ROLE_VEC, dev_mode=True)
    assert ranked == []
    assert details == {}


def test_embedding_rank_skills_orders_by_similarity(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    skills = ["low", "high", "mid"]
    # high → [1,0] sim=1.0, mid → [0.7,0.7] sim≈0.707, low → [0,1] sim=0.0
    monkeypatch.setattr(embeddings, "embed_skills", lambda _: [[0.0, 1.0], [1.0, 0.0], [0.7071, 0.7071]])
    ranked, _ = embedding_rank_skills(skills=skills, role_vec=ROLE_VEC)
    assert ranked == ["high", "mid", "low"]


def test_embedding_rank_skills_top_n(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    skills = ["a", "b", "c"]
    monkeypatch.setattr(embeddings, "embed_skills", lambda _: [[1.0, 0.0], [0.5, 0.5], [0.0, 1.0]])
    ranked, _ = embedding_rank_skills(skills=skills, role_vec=ROLE_VEC, top_n=2)
    assert len(ranked) == 2
    assert ranked[0] == "a"


def test_embedding_rank_skills_dev_mode_includes_details(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    skills = ["python", "rust"]
    monkeypatch.setattr(embeddings, "embed_skills", lambda _: [[1.0, 0.0], [0.0, 1.0]])
    _, details = embedding_rank_skills(skills=skills, role_vec=ROLE_VEC, dev_mode=True)
    assert details is not None
    assert "python" in details
    assert "similarity" in details["python"]


def test_embedding_rank_skills_length_mismatch_raises(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings, "embed_skills", lambda _: [[1.0, 0.0]])  # only 1 vec for 2 skills
    with pytest.raises(ValueError, match="does not match"):
        embedding_rank_skills(skills=["a", "b"], role_vec=ROLE_VEC)


def test_embedding_rank_skills_stable_tiebreak(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    # Two skills with identical similarity — should tie-break by normalized name asc
    skills = ["Zebra", "Alpha"]
    monkeypatch.setattr(embeddings, "embed_skills", lambda _: [[1.0, 0.0], [1.0, 0.0]])
    ranked, _ = embedding_rank_skills(skills=skills, role_vec=ROLE_VEC)
    assert ranked == ["Alpha", "Zebra"]


# ---------------------------------------------------------------------------
# embedding_select_skills
# ---------------------------------------------------------------------------

def _make_embed_role(vec):
    return lambda text: vec


def _make_embed_skills(vecs):
    """Return embed_skills mock that returns `vecs` for any call."""
    def _embed(skills):
        # return as many vecs as there are skills
        return vecs[: len(skills)]
    return _embed


ROLE_VEC_2D = [1.0, 0.0]
ONE_VEC = [1.0, 0.0]


def test_embedding_select_skills_uses_role_cache(monkeypatch):
    """When role text is in cache, embed_role should NOT be called."""
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    role_text = "backend engineer"
    monkeypatch.setattr(embeddings.cache, "role_cache", {role_text: ROLE_VEC_2D})
    called = []
    monkeypatch.setattr(embeddings, "embed_role", lambda t: called.append(t) or ROLE_VEC_2D)
    monkeypatch.setattr(embeddings, "embed_skills", lambda skills: [[1.0, 0.0]] * len(skills))

    embedding_select_skills(
        job_role="Backend Engineer",
        technology=["docker"],
        programming=["python"],
        concepts=["ci/cd"],
    )
    assert called == [], "embed_role should not be called on cache hit"


def test_embedding_select_skills_calls_embed_role_on_cache_miss(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "role_cache", {})
    called = []

    def fake_embed_role(text):
        called.append(text)
        return ROLE_VEC_2D

    monkeypatch.setattr(embeddings, "embed_role", fake_embed_role)
    monkeypatch.setattr(embeddings, "embed_skills", lambda skills: [[1.0, 0.0]] * len(skills))

    embedding_select_skills(
        job_role="Data Engineer",
        technology=["spark"],
        programming=["scala"],
        concepts=["etl"],
    )
    assert len(called) == 1


def test_embedding_select_skills_returns_subset_of_input(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "role_cache", {})
    monkeypatch.setattr(embeddings, "embed_role", lambda _: ROLE_VEC_2D)
    monkeypatch.setattr(embeddings, "embed_skills", lambda skills: [[1.0, 0.0]] * len(skills))

    technology = ["docker", "kubernetes"]
    programming = ["python", "go"]
    concepts = ["microservices"]

    result, _ = embedding_select_skills(
        job_role="Backend Engineer",
        technology=technology,
        programming=programming,
        concepts=concepts,
    )
    assert set(result["technology"]).issubset(set(technology))
    assert set(result["programming"]).issubset(set(programming))
    assert set(result["concepts"]).issubset(set(concepts))


def test_embedding_select_skills_short_role_warns(monkeypatch, caplog):
    import logging
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "role_cache", {})
    monkeypatch.setattr(embeddings, "embed_role", lambda _: ROLE_VEC_2D)
    monkeypatch.setattr(embeddings, "embed_skills", lambda skills: [[1.0, 0.0]] * len(skills))

    with caplog.at_level(logging.WARNING, logger="embeddings_scorer"):
        embedding_select_skills(
            job_role="x",  # very short — below MIN_ROLE_TEXT_CHARS
            technology=["docker"],
            programming=[],
            concepts=[],
        )
    assert any("role_text_too_short" in r.msg or "role_text_too_short" == getattr(r, "event", None)
               for r in caplog.records)


def test_embedding_select_skills_dev_mode_warnings_in_details(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "role_cache", {})
    monkeypatch.setattr(embeddings, "embed_role", lambda _: ROLE_VEC_2D)
    monkeypatch.setattr(embeddings, "embed_skills", lambda skills: [[1.0, 0.0]] * len(skills))

    _, details = embedding_select_skills(
        job_role="x",
        technology=["docker"],
        programming=[],
        concepts=[],
        dev_mode=True,
    )
    assert details is not None
    assert "_warnings" in details
    assert len(details["_warnings"]) > 0


def test_embedding_select_skills_rate_limit_raises(monkeypatch):
    import openai
    from unittest.mock import MagicMock
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "role_cache", {})

    fake_response = MagicMock()
    fake_response.request = MagicMock()

    def raise_rate_limit(_):
        raise openai.RateLimitError("rate limit", response=fake_response, body=None)

    monkeypatch.setattr(embeddings, "embed_role", raise_rate_limit)

    with pytest.raises(RuntimeError, match="rate limit"):
        embedding_select_skills(
            job_role="Backend Engineer",
            technology=["docker"],
            programming=["python"],
            concepts=[],
        )


def test_embedding_select_skills_empty_categories(monkeypatch):
    _disable_cache_writes(monkeypatch)
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "role_cache", {})
    monkeypatch.setattr(embeddings, "embed_role", lambda _: ROLE_VEC_2D)
    monkeypatch.setattr(embeddings, "embed_skills", lambda skills: [])

    result, _ = embedding_select_skills(
        job_role="Backend Engineer",
        technology=[],
        programming=[],
        concepts=[],
    )
    assert result == {"technology": [], "programming": [], "concepts": []}


def test_embedding_select_skills_stores_role_on_cache_miss(monkeypatch):
    calls = []
    monkeypatch.setattr(embeddings.cache, "role_cache", {})
    monkeypatch.setattr(embeddings.cache, "skill_cache", {})
    monkeypatch.setattr(embeddings.cache, "cache_store", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(embeddings, "embed_role", lambda _: ROLE_VEC_2D)

    embedding_select_skills(
        job_role="Backend Engineer",
        technology=[],
        programming=[],
        concepts=[],
    )

    assert any(args[0] == "backend engineer" and kwargs.get("type") == "role" for args, kwargs in calls)


def test_embedding_rank_skills_uses_cache_and_stores_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(embeddings.cache, "skill_cache", {"python": [1.0, 0.0]})
    monkeypatch.setattr(embeddings.cache, "cache_store", lambda *args, **kwargs: calls.append((args, kwargs)))

    requested = []
    def fake_embed_skills(texts):
        requested.append(list(texts))
        return [[0.0, 1.0] for _ in texts]

    monkeypatch.setattr(embeddings, "embed_skills", fake_embed_skills)

    ranked, _ = embedding_rank_skills(skills=["Python", "Rust"], role_vec=ROLE_VEC)
    assert ranked
    assert requested == [["rust"]]
    assert any(args[0] == "rust" and kwargs.get("type") == "skill" for args, kwargs in calls)
