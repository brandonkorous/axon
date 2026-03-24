"""Tests for axon.db.encryption — Fernet encrypt/decrypt round-trip.

NOTE: We import the encryption module directly to avoid pulling in
sqlalchemy via axon.db.__init__.  If sqlalchemy is installed, the
normal import path works fine too.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken


@pytest.fixture
def enc():
    """Import encryption module, stubbing out the db package __init__ if needed."""
    # If axon.db is already imported and has sqlalchemy, just use it
    # Otherwise, temporarily stub axon.db so we can import encryption alone
    needs_stub = "axon.db" not in sys.modules
    if needs_stub:
        stub = ModuleType("axon.db")
        sys.modules["axon.db"] = stub

    import axon.db.encryption as _enc
    importlib.reload(_enc)  # ensure fresh state
    _enc._fernet = None
    yield _enc
    _enc._fernet = None

    if needs_stub and "axon.db" in sys.modules and isinstance(sys.modules["axon.db"], ModuleType):
        # Only remove our stub, not a real module
        if not hasattr(sys.modules["axon.db"], "Base"):
            del sys.modules["axon.db"]


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestEncryptDecrypt:
    def test_round_trip_simple(self, enc, fernet_key):
        enc._fernet = Fernet(fernet_key.encode())
        plaintext = "sk-abc123"
        cipher = enc.encrypt_token(plaintext)
        assert cipher != plaintext
        assert enc.decrypt_token(cipher) == plaintext

    def test_round_trip_unicode(self, enc, fernet_key):
        enc._fernet = Fernet(fernet_key.encode())
        plaintext = "token-with-unicode-\u00e9\u00e0\u00fc"
        assert enc.decrypt_token(enc.encrypt_token(plaintext)) == plaintext

    def test_round_trip_empty_string(self, enc, fernet_key):
        enc._fernet = Fernet(fernet_key.encode())
        assert enc.decrypt_token(enc.encrypt_token("")) == ""

    def test_different_ciphertexts_each_call(self, enc, fernet_key):
        """Fernet includes a timestamp + random IV, so encrypting the same
        plaintext twice must produce different ciphertexts."""
        enc._fernet = Fernet(fernet_key.encode())
        a = enc.encrypt_token("same")
        b = enc.encrypt_token("same")
        assert a != b


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_decrypt_garbage_raises(self, enc, fernet_key):
        enc._fernet = Fernet(fernet_key.encode())
        with pytest.raises(Exception):
            enc.decrypt_token("not-valid-base64-ciphertext!!!")

    def test_decrypt_wrong_key(self, enc, fernet_key):
        """Decrypting with a different key should fail."""
        enc._fernet = Fernet(fernet_key.encode())
        cipher = enc.encrypt_token("secret")
        # Swap in a different key
        other_key = Fernet.generate_key()
        enc._fernet = Fernet(other_key)
        with pytest.raises(InvalidToken):
            enc.decrypt_token(cipher)


# ---------------------------------------------------------------------------
# Missing key
# ---------------------------------------------------------------------------


class TestMissingKey:
    def test_no_key_raises_runtime_error(self, enc, monkeypatch: pytest.MonkeyPatch):
        """When DB_ENCRYPTION_KEY is empty, _get_fernet should raise."""
        enc._fernet = None
        monkeypatch.setattr("axon.config.settings.db_encryption_key", "")
        with pytest.raises(RuntimeError, match="DB_ENCRYPTION_KEY"):
            enc._get_fernet()
