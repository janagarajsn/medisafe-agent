"""Shared pytest fixtures — patch file paths so tests never touch ~/.medisafe."""

import os

import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Redirect DB and encryption key to a temporary directory for every test."""
    key_path = str(tmp_path / "test.key")
    db_path = str(tmp_path / "test.db")

    # Pre-create a known key so encryption is consistent within the test
    key = Fernet.generate_key()
    with open(key_path, "wb") as fh:
        fh.write(key)

    monkeypatch.setattr("src.security.encryption._KEY_PATH", key_path)
    monkeypatch.setattr("src.database.manager._DB_PATH", db_path)

    # Fresh schema for every test
    from src.database.manager import init_db
    init_db()

    yield
