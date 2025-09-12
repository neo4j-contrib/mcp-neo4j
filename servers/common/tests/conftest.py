"""
Shared test fixtures for common package tests.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_environment():
    """Auto-used fixture to ensure clean test environment."""
    # This fixture can be used for any global test setup/teardown
    yield
