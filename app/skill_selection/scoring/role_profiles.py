import yaml
from pathlib import Path

_PROFILES_DIR = Path(__file__).parent.parent / "data" / "role_profiles"

# Filenames that don't map directly to their role key (stem -> key)
_FILENAME_TO_KEY = {
    "ml_ai": "ml/ai",
}


def _load_role_profiles() -> dict:
    profiles = {}
    for yaml_file in sorted(_PROFILES_DIR.glob("*.yaml")):
        stem = yaml_file.stem
        key = _FILENAME_TO_KEY.get(stem, stem)
        with open(yaml_file) as f:
            profiles[key] = yaml.safe_load(f)
    return profiles


# Mapping of role profiles to their associated keywords and boost terms.
ROLE_PROFILES = _load_role_profiles()

def detect_role_family(job_role: str) -> str:
    job_role_clean = job_role.lower().strip()
    tokens = job_role_clean.replace("-", " ").split()

    # Most specific first
    if "mobile" in tokens:
        return "mobile"
    if "fullstack" in tokens or ("full" in tokens and "stack" in tokens):
        return "fullstack"
    if "backend" in tokens:
        return "backend"
    if "frontend" in tokens:
        return "frontend"
    if "devops" in tokens:
        return "devops"
    if "ml" in tokens or "machine" in tokens and "learning" in tokens or "ai" in tokens:
        return "ml"
    if "data" in tokens:
        return "data"
    if "security" in tokens or "cybersecurity" in tokens:
        return "security"

    return "general"