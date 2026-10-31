"""Smoke tests for the project's declared runtime dependencies."""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "google_auth_httplib2",
        "google_auth_oauthlib",
        "googleapiclient",
        "pgmpy",
        "pydantic",
    ],
)
def test_runtime_dependency_is_importable(module_name: str) -> None:
    """Verify that each core runtime dependency can be imported."""
    assert import_module(module_name) is not None
