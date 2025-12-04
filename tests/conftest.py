"""
Pytest configuration and fixtures for ResumeKit tests.

This module provides shared fixtures and configuration for all tests.
"""

import os

import pytest

# Disable rate limiting for tests by default
os.environ["RATE_LIMIT_ENABLED"] = "false"

# Set test auth secret key if not already set
if "AUTH_SECRET_KEY" not in os.environ:
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key-for-testing-only-not-for-production"


@pytest.fixture(autouse=True)
def _disable_rate_limiting():
    """
    Automatically disable rate limiting for all tests.

    This ensures tests can run without hitting rate limits.
    """
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    yield
    # Cleanup if needed
    os.environ.pop("RATE_LIMIT_ENABLED", None)

