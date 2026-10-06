import os
import struct

from stegx.core.crypto import encrypt_data, decrypt_data, _encrypt_data_v2, _decrypt_data_v2

# --- V1 Constants ---
MAGIC = b"STEGX"
VERSION = 1
FLAG_ENCRYPTED = 0x01
SALT_SIZE = 16

# --- V2 Constants ---
MAGIC_V2 = b"STG2"
VERSION_V2 = 0x02
SALT_SIZE_V2 = 16
NONCE_SIZE_V2 = 12
TAG_SIZE_V2 = 16
MAX_FILENAME_LEN = 255
MAX_PAYLOAD_SIZE = 1073741824  # 1 GiB

# Flag bits V2
FLAG_V2_RANDOMIZED = 0x01
FLAG_V2_SEQUENTIAL = 0x00

def create_payload(
    file_path: str,
    password: str | None = None,
) -> bytes:
    """
    Read a file and package it into the StegX payload format (V1).
    """
    with open(file_path, "rb") as file:
        file_data = file.read()

    filename = os.path.basename(file_path)
    filename_bytes = filename.encode("utf-8")

    flags = 0
    salt = b""

    # Encrypt the file data if a password was provided.
    if password:
        salt, file_data = encrypt_data(
            file_data,
            password,
        )

        flags |= FLAG_ENCRYPTED

    header = b""
    header += MAGIC
    header += struct.pack("B", VERSION)
    header += struct.pack("B", flags)
    header += struct.pack("H", len(filename_bytes))
    header += filename_bytes
    header += struct.pack("Q", len(file_data))

    if flags & FLAG_ENCRYPTED:
        header += salt

    return header + file_data


def get_payload_info(payload: bytes) -> dict:
    """
    Read and validate a StegX payload header (V1).
    """
    minimum_header_size = 5 + 1 + 1 + 2 + 8

    if len(payload) < minimum_header_size:
        raise ValueError("Payload is too small to be a valid StegX payload.")

    offset = 0

    magic = payload[offset:offset + 5]
    offset += 5

    if magic != MAGIC:
        raise ValueError("StegX signature not found.")

    version = struct.unpack("B", payload[offset:offset + 1])[0]
    offset += 1

    flags = struct.unpack("B", payload[offset:offset + 1])[0]
    offset += 1

    filename_length = struct.unpack("H", payload[offset:offset + 2])[0]
    if filename_length > 255:
        raise ValueError(f"Payload filename length ({filename_length}) exceeds security limits.")
    offset += 2

    if offset + filename_length > len(payload):
        raise ValueError("Payload ends prematurely before filename.")

    filename = payload[offset:offset + filename_length].decode("utf-8")
    offset += filename_length

    if offset + 8 > len(payload):
        raise ValueError("Payload ends prematurely before payload size.")

    payload_size = struct.unpack("Q", payload[offset:offset + 8])[0]
    if payload_size > 2 * 1024 * 1024 * 1024:
        raise ValueError(f"Payload size ({payload_size}) exceeds absolute maximum limit.")
    offset += 8

    encrypted = bool(flags & FLAG_ENCRYPTED)
    salt = None

    if encrypted:
        if len(payload) < offset + SALT_SIZE:
            raise ValueError("Encrypted payload is missing salt.")
        salt = payload[offset:offset + SALT_SIZE]
        offset += SALT_SIZE

    return {
        "magic": magic.decode(),
        "version": version,
        "encrypted": encrypted,
        "filename": filename,
        "payload_size": payload_size,
        "salt": salt,
        "header_size": offset,
    }

# --- V2 Functions ---

def create_payload_v2(
    file_data: bytes,
    filename: str,
    password: str,
    randomized: bool = True,
) -> bytes:
    """
    Package data into the StegX V2 payload format.
    """
    filename_bytes = filename.encode("utf-8")
    fl = len(filename_bytes)
    if fl > MAX_FILENAME_LEN:
        raise ValueError(f"Filename exceeds {MAX_FILENAME_LEN} UTF-8 bytes.")

    pl = len(file_data)
    if pl > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload exceeds absolute maximum limit of 1 GiB.")

    flags = FLAG_V2_RANDOMIZED if randomized else FLAG_V2_SEQUENTIAL

    salt = os.urandom(SALT_SIZE_V2)
    nonce = os.urandom(NONCE_SIZE_V2)

    fixed_header = struct.pack("<4sBBHQ", MAGIC_V2, VERSION_V2, flags, fl, pl)
    aad = fixed_header + filename_bytes + salt + nonce

    ciphertext_with_tag = _encrypt_data_v2(file_data, password, salt, nonce, aad)

    if len(ciphertext_with_tag) != pl + TAG_SIZE_V2:
        raise ValueError("Unexpected ciphertext length from AEAD.")

    ciphertext = ciphertext_with_tag[:pl]
    tag = ciphertext_with_tag[pl:]

    return aad + ciphertext + tag


def parse_payload_v2(payload: bytes, password: str) -> tuple[str, bytes, int]:
    """
    Parses, authenticates, and decrypts a V2 payload.
    """
    if len(payload) < 16:
        raise ValueError("Payload header is truncated or malformed.")

    magic, version, flags, fl, pl = struct.unpack("<4sBBHQ", payload[:16])

    if magic != MAGIC_V2:
        raise ValueError("Invalid magic for V2 parser.")

    if version != VERSION_V2:
        raise ValueError("Unsupported V2 version.")

    if flags & 0b11111110 != 0:
        raise ValueError("Reserved flag bits must be 0.")

    if fl > MAX_FILENAME_LEN:
        raise ValueError(f"Filename length ({fl}) exceeds security limits.")

    if pl > MAX_PAYLOAD_SIZE:
        raise ValueError("Payload size exceeds absolute maximum limit.")

    expected_length = 16 + fl + SALT_SIZE_V2 + NONCE_SIZE_V2 + pl + TAG_SIZE_V2
    if len(payload) < expected_length:
        raise ValueError("Payload header is truncated or malformed.")

    if len(payload) != expected_length:
        raise ValueError("Payload length mismatch.")

    offset = 16
    filename_bytes = payload[offset : offset + fl]
    offset += fl

    salt = payload[offset : offset + SALT_SIZE_V2]
    offset += SALT_SIZE_V2

    nonce = payload[offset : offset + NONCE_SIZE_V2]
    offset += NONCE_SIZE_V2

    ciphertext = payload[offset : offset + pl]
    offset += pl

    tag = payload[offset : offset + TAG_SIZE_V2]
    offset += TAG_SIZE_V2

    aad_len = 16 + fl + SALT_SIZE_V2 + NONCE_SIZE_V2
    aad = payload[:aad_len]

    ciphertext_with_tag = ciphertext + tag
    plaintext = _decrypt_data_v2(ciphertext_with_tag, password, salt, nonce, aad)

    try:
        filename = filename_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Filename is not valid UTF-8.")

    return filename, plaintext, flags


def extract_payload(payload: bytes, password: str | None = None) -> tuple[str, bytes, int]:
    """
    Universal strict router for StegX payloads.
    """
    if len(payload) < 4:
        raise ValueError("Payload header is truncated or malformed.")

    magic4 = payload[:4]

    if magic4 == MAGIC_V2:
        if password is None:
            raise ValueError("Password required.")
        return parse_payload_v2(payload, password)

    elif magic4 == b"STEG":
        if len(payload) < 5 or payload[4:5] != b"X":
            raise ValueError("Unknown or unsupported StegX format.")

        info = get_payload_info(payload)
        header_size = info["header_size"]
        payload_size = info["payload_size"]
        file_data = payload[header_size:header_size + payload_size]

        if info["encrypted"]:
            if password is None:
                raise ValueError("Password required.")
            file_data = decrypt_data(file_data, password, info["salt"])

        return info["filename"], file_data, 0

    else:
        raise ValueError("Unknown or unsupported StegX format.")
