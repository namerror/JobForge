"""Integration smoke tests for the embedding pipeline.

These tests call the real OpenAI API and are **skipped** unless BOTH:
  1. The OPENAI_API_KEY environment variable is set.
  2. The --run-smoke flag is passed to pytest.

Run manually with:
    OPENAI_API_KEY=sk-... pytest tests/test_embedding_smoke.py -v --run-smoke
"""
import os

import pytest

pytestmark = pytest.mark.smoke


def test_embed_role_returns_valid_vector():
    from app.skill_selection.embedding_client import embed_role

    vec = embed_role("Senior Backend Engineer building Python microservices")
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert all(isinstance(v, float) for v in vec)


def test_embed_skills_returns_matching_vectors():
    from app.skill_selection.embedding_client import embed_skills

    skills = ["Python", "Docker", "Kubernetes"]
    vecs = embed_skills(skills)
    assert isinstance(vecs, list)
    assert len(vecs) == len(skills)
    # All vectors should have the same dimensionality
    dims = {len(v) for v in vecs}
    assert len(dims) == 1, f"Expected uniform dimensions, got {dims}"
    assert all(isinstance(v, float) for v in vecs[0])


def test_embed_role_and_skills_same_dimensions():
    """Role and skill embeddings must share the same vector space."""
    from app.skill_selection.embedding_client import embed_role, embed_skills

    role_vec = embed_role("Data Engineer")
    skill_vecs = embed_skills(["Spark", "SQL"])

    assert len(role_vec) == len(skill_vecs[0])
    assert len(role_vec) == len(skill_vecs[1])


def test_cosine_similarity_with_real_embeddings():
    """Sanity check: related terms should score higher than unrelated ones."""
    from app.skill_selection.embedding_client import embed_role, embed_skills
    from app.skill_selection.scoring.embeddings import cosine_similarity

    role_vec = embed_role("Machine Learning Engineer")
    vecs = embed_skills(["PyTorch", "Accounting"])

    sim_pytorch = cosine_similarity(role_vec, vecs[0])
    sim_accounting = cosine_similarity(role_vec, vecs[1])

    # PyTorch should be more relevant to ML Engineer than Accounting
    assert sim_pytorch > sim_accounting, (
        f"Expected PyTorch ({sim_pytorch:.4f}) > Accounting ({sim_accounting:.4f})"
    )
