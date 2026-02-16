"""Pytest configuration for test suite."""
import os
import sys
import pytest


# Set environment variables BEFORE any app imports
os.environ["DEV_MODE"] = "true"
os.environ.setdefault("TOP_N", "10")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment and reload modules with correct env vars."""
    # Reload the baseline module to pick up the new DEV_MODE value
    if "app.scoring.baseline" in sys.modules:
        import importlib
        import app.scoring.baseline
        importlib.reload(app.scoring.baseline)

    yield
