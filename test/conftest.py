"""Shared pytest fixtures for the RecuseOracle test suite."""

import pytest
from gltest.gl import create_client


@pytest.fixture(scope="session")
def client():
    """A GenLayer client connected to the localnet studio."""
    return create_client(rpc_url="http://localhost:4000/api")
