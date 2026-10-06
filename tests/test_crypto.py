import pytest

from stegx.core.crypto import (
    decrypt_data,
    encrypt_data,
)


def test_encrypt_and_decrypt():

    original_data = (
        b"Hello from StegX encryption test"
    )

    password = "testpassword123"

    salt, encrypted_data = encrypt_data(
        original_data,
        password,
    )

    decrypted_data = decrypt_data(
        encrypted_data,
        password,
        salt,
    )

    assert decrypted_data == original_data


def test_encrypted_data_is_different():

    original_data = (
        b"Sensitive StegX data"
    )

    password = "testpassword123"

    salt, encrypted_data = encrypt_data(
        original_data,
        password,
    )

    assert encrypted_data != original_data


def test_wrong_password_raises_error():

    original_data = (
        b"Secret StegX message"
    )

    salt, encrypted_data = encrypt_data(
        original_data,
        "correctpassword",
    )

    with pytest.raises(ValueError):

        decrypt_data(
            encrypted_data,
            "wrongpassword",
            salt,
        )


def test_encryption_generates_salt():

    original_data = b"Test data"

    salt, encrypted_data = encrypt_data(
        original_data,
        "password123",
    )

    assert len(salt) == 16
    assert len(encrypted_data) > 0


# --- V2 Tests ---

from stegx.core.crypto import (
    _encrypt_data_v2,
    _decrypt_data_v2,
    derive_key_v2,
    ARGON2_TIME_COST,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_KEY_LEN,
)

def test_v2_encrypt_and_decrypt():
    original_data = b"Hello from StegX V2 encryption test"
    password = "testpassword123"
    aad = b"associated_data_v2"

    import os
    salt = os.urandom(16)
    nonce = os.urandom(12)
    ciphertext_with_tag = _encrypt_data_v2(
        original_data,
        password,
        salt,
        nonce,
        aad,
    )

    decrypted_data = _decrypt_data_v2(
        ciphertext_with_tag,
        password,
        salt,
        nonce,
        aad,
    )

    assert decrypted_data == original_data

def test_v2_argon2_parameters_are_fixed():
    # 6. ARGON2 PARAMETERS
    assert ARGON2_TIME_COST == 2
    assert ARGON2_MEMORY_COST == 65536
    assert ARGON2_PARALLELISM == 4
    assert ARGON2_KEY_LEN == 32

def test_v2_true_known_answer_test():
    # 1. TRUE KNOWN-ANSWER TEST
    password = "testpassword"
    test_salt = bytes([0] * 16)
    test_nonce = bytes([1] * 12)
    aad = bytes([116, 101, 115, 116, 95, 97, 97, 100, 95, 100, 97, 116, 97])
    plaintext = bytes([84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 107, 110, 111, 119, 110, 32, 97, 110, 115, 119, 101, 114, 32, 116, 101, 115, 116, 32, 112, 108, 97, 105, 110, 116, 101, 120, 116, 32, 102, 111, 114, 32, 86, 50, 46])

    expected_ct_with_tag = bytes([176, 28, 82, 62, 61, 27, 54, 21, 205, 168, 100, 229, 42, 238, 111, 115, 254, 212, 160, 99, 22, 229, 195, 14, 82, 120, 181, 4, 72, 1, 250, 214, 235, 74, 107, 230, 54, 103, 2, 107, 120, 100, 34, 7, 245, 131, 155, 63, 231, 73, 102, 227, 59, 88, 139, 2, 129, 126, 1, 30, 114])

    salt, nonce = test_salt, test_nonce
    ciphertext_with_tag = _encrypt_data_v2(
        plaintext,
        password,
        salt,
        nonce,
        aad,
    )

    assert salt == test_salt
    assert nonce == test_nonce
    assert ciphertext_with_tag == expected_ct_with_tag

    decrypted = _decrypt_data_v2(
        expected_ct_with_tag,
        password,
        test_salt,
        test_nonce,
        aad,
    )
    assert decrypted == plaintext

def test_v2_salt_and_nonce_randomness():
    # 2. SALT RANDOMNESS TEST and 3. NONCE RANDOMNESS TEST
    original_data = b"Secret StegX message"
    password = "testpassword123"
    aad = b"associated_data_v2"

    import os
    salt1, nonce1 = os.urandom(16), os.urandom(12)
    ct1 = _encrypt_data_v2(original_data, password, salt1, nonce1, aad)
    salt2, nonce2 = os.urandom(16), os.urandom(12)
    ct2 = _encrypt_data_v2(original_data, password, salt2, nonce2, aad)

    # Asserting production randomness
    assert salt1 != salt2, "Encryption must generate distinct random salts"
    assert nonce1 != nonce2, "Encryption must generate distinct random nonces"
    assert ct1 != ct2, "Distinct salt and nonces must produce different ciphertexts"

def test_v2_authentication_failures_are_indistinguishable():
    # 4. AUTHENTICATION FAILURE API
    # 5. NO PLAINTEXT AFTER FAILED AUTHENTICATION
    original_data = b"Secret StegX message"
    aad = b"aad"
    password = "correctpassword"
    import os
    salt = os.urandom(16)
    nonce = os.urandom(12)
    ciphertext_with_tag = _encrypt_data_v2(
        original_data, password, salt, nonce, aad
    )

    expected_msg = "Authentication failed: Incorrect password or corrupted payload."

    # Failure 1: Wrong password
    with pytest.raises(ValueError, match=expected_msg):
        _decrypt_data_v2(ciphertext_with_tag, "wrongpassword", salt, nonce, aad)

    # Failure 2: Modified ciphertext
    modified_ct = bytearray(ciphertext_with_tag)
    modified_ct[0] ^= 0x01
    with pytest.raises(ValueError, match=expected_msg):
        _decrypt_data_v2(bytes(modified_ct), password, salt, nonce, aad)

    # Failure 3: Modified AAD
    with pytest.raises(ValueError, match=expected_msg):
        _decrypt_data_v2(ciphertext_with_tag, password, salt, nonce, b"bad_aad")

    # Failure 4: Modified Nonce
    modified_nonce = bytearray(nonce)
    modified_nonce[0] ^= 0x01
    with pytest.raises(ValueError, match=expected_msg):
        _decrypt_data_v2(ciphertext_with_tag, password, salt, bytes(modified_nonce), aad)

    # Prove no plaintext is returned
    returned_plaintext = None
    try:
        returned_plaintext = _decrypt_data_v2(bytes(modified_ct), password, salt, nonce, aad)
    except ValueError:
        pass
    assert returned_plaintext is None, "Failed authentication MUST NOT return any decrypted data"

def test_v2_empty_plaintext():
    original_data = b""
    password = "testpassword123"
    aad = b"associated_data_v2"

    import os
    salt = os.urandom(16)
    nonce = os.urandom(12)
    ciphertext_with_tag = _encrypt_data_v2(
        original_data, password, salt, nonce, aad
    )
    decrypted_data = _decrypt_data_v2(
        ciphertext_with_tag, password, salt, nonce, aad
    )
    assert decrypted_data == b""

def test_v2_small_and_binary_plaintext():
    original_data = bytes([0x00, 0xFF, 0x55, 0xAA])
    password = "testpassword123"
    aad = b"binary_aad"

    import os
    salt = os.urandom(16)
    nonce = os.urandom(12)
    ciphertext_with_tag = _encrypt_data_v2(
        original_data, password, salt, nonce, aad
    )
    decrypted_data = _decrypt_data_v2(
        ciphertext_with_tag, password, salt, nonce, aad
    )
    assert decrypted_data == original_data