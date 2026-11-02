"""Shared pytest configuration."""

import pytest
from jitxlib.parts.resolver import reset


@pytest.fixture(autouse=True)
def reset_parts_resolver():
    """Give every test an independent Parts 2 resolver run."""
    reset()
    yield
    reset()
