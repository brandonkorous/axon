"""Tests for axon.db.encryption — Fernet encrypt/decrypt round-trip."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet, InvalidToken

from axon.db.encryption import _get_fernet, decrypt_token, encrypt_token
import axon.db.encryption as enc_module


@pytest.fixture(autouse=True)
def reset_fernet():
    """Reset module-level fernet singleton between tests."""
    enc_module._fernet = None
    yield
    enc_module._fernet = None


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def setup_fernet(fernet_key):
    """Set up a valid Fernet instance on the module."""
    enc_module._fernet = Fernet(fernet_key.encode())


class TestEncryptDecrypt:
    def test_round_trip_simple(self, setup_fernet):
        plaintext = "sk-abc123"
        cipher = encrypt_token(plaintext)
        assert cipher != plaintext
        assert decrypt_token(cipher) == plaintext

    def test_round_trip_unicode(self, setup_fernet):
        plaintext = "token-with-unicode-\u00e9\u00e0\u00fc"
        assert decrypt_token(encrypt_token(plaintext)) == plaintext

    def test_round_trip_empty_string(self, setup_fernet):
        assert decrypt_token(encrypt_token("")) == ""

    def test_different_ciphertexts_each_call(self, setup_fernet):
        """Fernet includes a timestamp + random IV, so encrypting the same
        plaintext twice must produce different ciphertexts."""
        a = encrypt_token("same")
        b = encrypt_token("same")
        assert a != b


class TestErrorHandling:
    def test_decrypt_garbage_raises(self, setup_fernet):
        with pytest.raises(Exception):
            decrypt_token("not-valid-base64-ciphertext!!!")

    def test_decrypt_wrong_key(self, setup_fernet):
        """Decrypting with a different key should fail."""
        cipher = encrypt_token("secret")
        other_key = Fernet.generate_key()
        enc_module._fernet = Fernet(other_key)
        with pytest.raises(InvalidToken):
            decrypt_token(cipher)


class TestMissingKey:
    def test_no_key_raises_runtime_error(self, monkeypatch: pytest.MonkeyPatch):
        """When DB_ENCRYPTION_KEY is empty, _get_fernet should raise."""
        monkeypatch.setattr("axon.config.settings.db_encryption_key", "")
        with pytest.raises(RuntimeError, match="DB_ENCRYPTION_KEY"):
            _get_fernet()
