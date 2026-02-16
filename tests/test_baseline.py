from app.scoring.baseline import score_skill, normalize_skill


# === Normalization tests ===

def test_normalize_skill_lowercases():
    """Test that skills are normalized to lowercase."""
    assert normalize_skill("Python") == "python"
    assert normalize_skill("PYTHON") == "python"
    assert normalize_skill("PyThOn") == "python"


def test_normalize_skill_strips_whitespace():
    """Test that whitespace is stripped."""
    assert normalize_skill("  python  ") == "python"
    assert normalize_skill("\tpython\n") == "python"


def test_normalize_skill_applies_synonyms():
    """Test that synonyms are normalized to canonical form."""
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("react.js") == "react"
    assert normalize_skill("Node.js") == "nodejs"
    assert normalize_skill("postgres") == "postgresql"
    assert normalize_skill("JS") == "javascript"


def test_normalize_skill_preserves_unknown():
    """Test that unknown skills are lowercased but otherwise preserved."""
    assert normalize_skill("CustomSkill") == "customskill"
    assert normalize_skill("some-framework") == "some-framework"


# === Scoring tests - exact matches ===

def test_score_skill_exact_match_with_normalization():
    """Test exact match with synonym normalization."""
    score, details = score_skill(
        skill="ReactJS",
        role_family="frontend",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "react"
    assert "react" in details["matched_keywords"]


def test_score_skill_exact_match_backend():
    """Test exact match for backend role."""
    score, details = score_skill(
        skill="FastAPI",
        role_family="backend",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "fastapi"
    assert "fastapi" in details["matched_keywords"]


def test_score_skill_exact_match_programming():
    """Test exact match for programming category."""
    score, details = score_skill(
        skill="Python",
        role_family="backend",
        category="programming",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "python"
    assert "python" in details["matched_keywords"]


def test_score_skill_exact_match_concepts():
    """Test exact match for concepts category."""
    score, details = score_skill(
        skill="Microservices",
        role_family="backend",
        category="concepts",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "microservices"
    assert "microservices" in details["matched_keywords"]


# === Scoring tests - partial matches ===

def test_score_skill_partial_match():
    """Test partial match scoring."""
    score, details = score_skill(
        skill="dock",
        role_family="devops",
        category="technology",
        job_text=None,
    )

    assert score == 1.0
    assert details["normalized_skill"] == "dock"
    assert "docker" in details["matched_keywords"]


def test_score_skill_partial_match_ci():
    """Test partial match for CI/CD."""
    score, details = score_skill(
        skill="ci",
        role_family="devops",
        category="concepts",
        job_text=None,
    )

    # "ci" should normalize to "ci/cd" and match exactly
    assert score == 3.0
    assert details["normalized_skill"] == "ci/cd"


# === Inheritance tests ===

def test_score_skill_inherits_parent_keywords():
    """Test that fullstack inherits keywords from parent roles."""
    score, details = score_skill(
        skill="FastAPI",
        role_family="fullstack",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "fastapi"
    assert "fastapi" in details["matched_keywords"]


def test_score_skill_inherits_from_multiple_parents():
    """Test that fullstack inherits from backend, frontend, and devops."""
    # Test backend skill
    score_backend, _ = score_skill(
        skill="Django",
        role_family="fullstack",
        category="technology",
        job_text=None,
    )
    assert score_backend == 3.0

    # Test frontend skill
    score_frontend, _ = score_skill(
        skill="React",
        role_family="fullstack",
        category="technology",
        job_text=None,
    )
    assert score_frontend == 3.0

    # Test devops skill
    score_devops, _ = score_skill(
        skill="Docker",
        role_family="fullstack",
        category="technology",
        job_text=None,
    )
    assert score_devops == 3.0


# === Fallback to general profile ===

def test_score_skill_unknown_role_falls_back_to_general():
    """Test that unknown role families fall back to general profile."""
    score, details = score_skill(
        skill="Python",
        role_family="unknown_role",
        category="programming",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "python"
    assert "python" in details["matched_keywords"]


def test_score_skill_general_role():
    """Test scoring with general role profile."""
    score, details = score_skill(
        skill="Git",
        role_family="general",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "git"
    assert "git" in details["matched_keywords"]


# === No match cases ===

def test_score_skill_no_match():
    """Test that unrelated skills score 0."""
    score, details = score_skill(
        skill="Photoshop",
        role_family="backend",
        category="technology",
        job_text=None,
    )

    assert score == 0.0
    assert details["normalized_skill"] == "photoshop"


def test_score_skill_wrong_category():
    """Test that skills in wrong category score 0."""
    score, details = score_skill(
        skill="React",
        role_family="frontend",
        category="programming",  # React is in technology, not programming
        job_text=None,
    )

    assert score == 0.0
    assert details["normalized_skill"] == "react"


# === Edge cases ===

def test_score_skill_empty_string():
    """Test handling of empty skill string."""
    score, details = score_skill(
        skill="",
        role_family="backend",
        category="technology",
        job_text=None,
    )

    assert score == 0.0
    assert details["normalized_skill"] == ""


def test_score_skill_whitespace_only():
    """Test handling of whitespace-only skill."""
    score, details = score_skill(
        skill="   ",
        role_family="backend",
        category="technology",
        job_text=None,
    )

    assert score == 0.0
    assert details["normalized_skill"] == ""


# === Determinism tests ===

def test_score_skill_deterministic():
    """Test that scoring is deterministic across multiple runs."""
    skill = "React"
    role_family = "frontend"
    category = "technology"

    results = [
        score_skill(skill, role_family, category, None)
        for _ in range(5)
    ]

    # All results should be identical
    scores = [r[0] for r in results]
    assert len(set(scores)) == 1, "Scores should be deterministic"

    normalized_skills = [r[1]["normalized_skill"] for r in results]
    assert len(set(normalized_skills)) == 1, "Normalization should be deterministic"


# === Category-specific tests ===

def test_score_skill_ml_ai_role():
    """Test ML/AI role specific keywords."""
    score, details = score_skill(
        skill="TensorFlow",
        role_family="ml/ai",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "tensorflow"


def test_score_skill_security_role():
    """Test security role specific keywords."""
    score, details = score_skill(
        skill="Metasploit",
        role_family="security",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "metasploit"


def test_score_skill_mobile_role():
    """Test mobile role specific keywords."""
    score, details = score_skill(
        skill="React Native",
        role_family="mobile",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "react native"


def test_score_skill_data_role():
    """Test data role specific keywords."""
    score, details = score_skill(
        skill="Spark",
        role_family="data",
        category="technology",
        job_text=None,
    )

    assert score == 3.0
    assert details["normalized_skill"] == "spark"


