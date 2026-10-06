import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

# --- V1 Constants ---
SALT_SIZE = 16
ITERATIONS = 600_000

# --- V2 Constants ---
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 65536  # KiB
ARGON2_PARALLELISM = 4
ARGON2_KEY_LEN = 32

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a Fernet-compatible encryption key from
    a user password and salt. (V1)
    """

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )

    key = base64.urlsafe_b64encode(
        kdf.derive(password.encode("utf-8"))
    )

    return key


def encrypt_data(
    data: bytes,
    password: str,
) -> tuple[bytes, bytes]:
    """
    Encrypt raw data using a password. (V1)

    Returns:
        salt, encrypted_data
    """

    salt = os.urandom(SALT_SIZE)

    key = derive_key(
        password,
        salt,
    )

    cipher = Fernet(key)

    encrypted_data = cipher.encrypt(data)

    return salt, encrypted_data


def decrypt_data(
    encrypted_data: bytes,
    password: str,
    salt: bytes,
) -> bytes:
    """
    Decrypt encrypted data using the password and salt. (V1)
    """

    key = derive_key(
        password,
        salt,
    )

    cipher = Fernet(key)

    try:
        return cipher.decrypt(encrypted_data)

    except InvalidToken:
        raise ValueError(
            "Incorrect password or corrupted encrypted data."
        )


def derive_key_v2(password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte key using Argon2id for V2.
    """
    kdf = Argon2id(
        salt=salt,
        length=ARGON2_KEY_LEN,
        iterations=ARGON2_TIME_COST,
        lanes=ARGON2_PARALLELISM,
        memory_cost=ARGON2_MEMORY_COST,
        ad=None,
        secret=None
    )
    return kdf.derive(password.encode("utf-8"))


def _encrypt_data_v2(
    data: bytes,
    password: str,
    salt: bytes,
    nonce: bytes,
    aad: bytes,
) -> bytes:
    """
    Encrypt data using ChaCha20-Poly1305 (V2).

    Returns:
        salt, nonce, ciphertext_with_tag
    """
    key = derive_key_v2(password, salt)
    cipher = ChaCha20Poly1305(key)
    ciphertext_with_tag = cipher.encrypt(nonce, data, aad)
    return ciphertext_with_tag


def _decrypt_data_v2(
    ciphertext_with_tag: bytes,
    password: str,
    salt: bytes,
    nonce: bytes,
    aad: bytes,
) -> bytes:
    """
    Decrypt V2 data using ChaCha20-Poly1305.
    """
    key = derive_key_v2(password, salt)
    cipher = ChaCha20Poly1305(key)

    try:
        return cipher.decrypt(nonce, ciphertext_with_tag, aad)
    except InvalidTag:
        raise ValueError("Authentication failed: Incorrect password or corrupted payload.")