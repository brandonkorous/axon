"""Token encryption/decryption using Fernet (AES-128-CBC).

Generate a key once:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Store as DB_ENCRYPTION_KEY in your .env file.
"""

from __future__ import annotations

from cryptography.fernet import Fernet

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        from axon.config import settings

        key = settings.db_encryption_key
        if not key:
            raise RuntimeError(
                "DB_ENCRYPTION_KEY is required for credential storage. "
                "Generate one with: python -c "
                '"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string for database storage."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored token string."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
