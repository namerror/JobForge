from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# === Health endpoint tests ===

def test_health():
    """Test health endpoint returns OK."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_method_not_allowed():
    """Test health endpoint only accepts GET."""
    res = client.post("/health")
    assert res.status_code == 405


# === Select skills endpoint tests ===

def test_select_skills_basic():
    """Test basic select-skills endpoint functionality."""
    payload = {
        "job_role": "backend",
        "technology": ["Python", "Django", "PostgreSQL"],
        "programming": ["Python", "Java"],
        "concepts": ["API", "Microservices"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert "technology" in data
    assert "programming" in data
    assert "concepts" in data
    assert isinstance(data["technology"], list)
    assert isinstance(data["programming"], list)
    assert isinstance(data["concepts"], list)


def test_select_skills_empty_lists():
    """Test select-skills with empty skill lists."""
    payload = {
        "job_role": "backend",
        "technology": [],
        "programming": [],
        "concepts": [],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["technology"] == []
    assert data["programming"] == []
    assert data["concepts"] == []


def test_select_skills_missing_field():
    """Test select-skills with missing required fields."""
    payload = {
        "job_role": "backend",
        "technology": ["Python"],
        # Missing programming and concepts
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 422  # Unprocessable Entity


def test_select_skills_invalid_types():
    """Test select-skills with invalid data types."""
    payload = {
        "job_role": "backend",
        "technology": "not a list",  # Should be a list
        "programming": ["Python"],
        "concepts": ["API"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 422


def test_select_skills_method_not_allowed():
    """Test select-skills endpoint only accepts POST."""
    res = client.get("/select-skills")
    assert res.status_code == 405


# === Response validation tests ===

def test_select_skills_response_structure():
    """Test that response matches expected structure."""
    payload = {
        "job_role": "frontend",
        "technology": ["React", "Vue", "Angular"],
        "programming": ["JavaScript", "TypeScript"],
        "concepts": ["UI", "UX"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200

    data = res.json()
    # Check all required fields are present
    required_fields = {"technology", "programming", "concepts"}
    assert set(data.keys()) == required_fields


def test_select_skills_maintains_subset():
    """Test that output is a subset of input (no invented skills)."""
    payload = {
        "job_role": "backend",
        "technology": ["Python", "Django", "FastAPI"],
        "programming": ["Python", "Java", "C#"],
        "concepts": ["API", "Database", "Cloud"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200

    data = res.json()
    # Currently the placeholder just returns all input, but future scorer
    # should only return subsets
    assert set(data["technology"]).issubset(set(payload["technology"]))
    assert set(data["programming"]).issubset(set(payload["programming"]))
    assert set(data["concepts"]).issubset(set(payload["concepts"]))


# === Different role tests ===


    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200


def test_select_skills_fullstack_role():
    """Test select-skills for fullstack role."""
    payload = {
        "job_role": "fullstack",
        "technology": ["React", "Django", "Docker"],
        "programming": ["Python", "JavaScript"],
        "concepts": ["API", "UI"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200


def test_select_skills_devops_role():
    """Test select-skills for devops role."""
    payload = {
        "job_role": "devops",
        "technology": ["Docker", "Kubernetes", "AWS", "Terraform"],
        "programming": ["Python", "Bash"],
        "concepts": ["CI/CD", "Infrastructure", "Automation"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200


def test_select_skills_mlai_role():
    """Test select-skills for ML/AI role."""
    payload = {
        "job_role": "ml/ai",
        "technology": ["TensorFlow", "PyTorch", "Scikit-learn"],
        "programming": ["Python", "C++"],
        "concepts": ["Machine Learning", "Deep Learning", "NLP"],
    }

    res = client.post("/select-skills", json=payload)
    assert res.status_code == 200
