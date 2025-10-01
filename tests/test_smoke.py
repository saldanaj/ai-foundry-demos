"""Basic smoke tests to ensure pytest discovers at least one test case.
These tests validate that core modules can be imported inside the configured
virtual environment without triggering runtime errors."""

import importlib
import sys

import pytest

MODULES_TO_IMPORT = [
    "app.config",
    "app.streamlit_app",
    "src.pii_detector",
    "src.ai_foundry_client",
]


@pytest.mark.parametrize("module_name", MODULES_TO_IMPORT)
@pytest.mark.skipif(sys.version_info < (3, 10), reason="Project requires Python 3.10+ for module imports")
def test_module_imports(module_name):
    """Ensure that important project modules import successfully."""
    module = importlib.import_module(module_name)
    assert module is not None


def test_pytest_is_configured():
    """Simple sanity check to confirm pytest runs at least one assertion."""
    assert True


@pytest.mark.xfail(sys.version_info < (3, 10), reason="Project runtime requires Python 3.10+", strict=True)
def test_python_version_requirement():
    """Highlight the minimum Python version required by the application."""
    assert sys.version_info >= (3, 10)
