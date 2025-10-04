"""Pytest configuration and fixtures for BactScout tests."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_data_dir(project_root):
    """Return the sample_data directory path."""
    return project_root / "sample_data"


@pytest.fixture
def config_file(project_root):
    """Return the default config file path."""
    return project_root / "bactscout_config.yml"
