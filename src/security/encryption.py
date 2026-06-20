import os
from cryptography.fernet import Fernet

_DEFAULT_KEY_DIR = os.path.expanduser("~/.medisafe")
_KEY_PATH = os.environ.get(
    "MEDISAFE_KEY_PATH",
    os.path.join(_DEFAULT_KEY_DIR, "encryption.key"),
)


def _load_or_create_key() -> bytes:
    key_dir = os.path.dirname(_KEY_PATH)
    os.makedirs(key_dir, exist_ok=True)
    if os.path.exists(_KEY_PATH):
        with open(_KEY_PATH, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(_KEY_PATH, "wb") as f:
        f.write(key)
    # Owner read/write only — no group or world access
    os.chmod(_KEY_PATH, 0o600)
    return key


def get_fernet() -> Fernet:
    return Fernet(_load_or_create_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a string value. Returns empty string unchanged."""
    if not plaintext:
        return plaintext
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a previously encrypted string. Returns empty string unchanged."""
    if not ciphertext:
        return ciphertext
    return get_fernet().decrypt(ciphertext.encode()).decode()
