import hashlib
import random


def generate_positions(
    total_positions: int,
    required_positions: int,
    key: str,
) -> list[int]:
    """
    Generate deterministic randomized positions.

    The same key and total number of positions will
    always generate the same sequence of positions.
    """

    if required_positions > total_positions:

        raise ValueError(
            "Required positions cannot exceed "
            "total available positions."
        )

    if not key:

        raise ValueError(
            "A position key is required."
        )

    # Convert the user-provided key into a stable
    # integer seed using SHA-256.
    key_hash = hashlib.sha256(
        key.encode("utf-8")
    ).digest()

    seed = int.from_bytes(
        key_hash,
        byteorder="big",
    )

    # Create an isolated random generator so we do
    # not affect Python's global random state.
    generator = random.Random(seed)

    # Generate unique randomized positions.
    positions = generator.sample(
        range(total_positions),
        required_positions,
    )

    return positions
import struct
from typing import Generator
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend

def derive_position_key_v2(position_key_str: str) -> bytes:
    """
    Derives exactly a 32-byte key exclusively for the position permutation PRF.
    """
    prefix = b"StegX-V2-Position-Feistel-PRF-v1"
    return hashlib.sha256(prefix + position_key_str.encode("utf-8")).digest()

def _chacha20_prf(key: bytes, round_num: int, r_half: int) -> int:
    """
    Evaluates the low-level ChaCha20 PRF for the Feistel network.

    16-byte API Nonce Construction:
      bytes 0-3: 0x00000000 (4-byte little-endian uint32 block counter)
      bytes 4-7: round_num (4-byte little-endian uint32)
      bytes 8-15: r_half (8-byte little-endian uint64)

    Returns the first 8 bytes of ciphertext as a little-endian uint64.
    """
    nonce = struct.pack("<IIQ", 0, round_num, r_half)

    algorithm = algorithms.ChaCha20(key, nonce)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    encryptor = cipher.encryptor()

    out = encryptor.update(b"\x00" * 8)

    return struct.unpack("<Q", out)[0]

def permute(X: int, N: int, key: bytes) -> int:
    """
    Computes the forward keyed Feistel permutation P(X) over the extended domain.
    """
    if N <= 1:
        return 0

    m = (N - 1).bit_length()
    half = (m + 1) // 2
    mask = (1 << half) - 1

    L = X >> half
    R = X & mask

    for round_num in range(8):
        K = _chacha20_prf(key, round_num, R)
        new_R = L ^ (K & mask)
        L = R
        R = new_R

    return (L << half) | R

def inverse_permute(X: int, N: int, key: bytes) -> int:
    """
    Computes the inverse keyed Feistel permutation P^{-1}(X) over the extended domain.
    """
    if N <= 1:
        return 0

    m = (N - 1).bit_length()
    half = (m + 1) // 2
    mask = (1 << half) - 1

    L = X >> half
    R = X & mask

    # Apply rounds in reverse
    for round_num in range(7, -1, -1):
        R_prev = L
        K = _chacha20_prf(key, round_num, R_prev)
        L_prev = R ^ (K & mask)
        L = L_prev
        R = R_prev

    return (L << half) | R

def generate_positions_v2(N: int, R: int, position_key: str) -> Generator[int, None, None]:
    """
    Generates exactly R distinct positions in [0, N-1] using a deterministic
    keyed Feistel permutation and cycle walking.

    Runs in strictly O(1) auxiliary memory.
    """
    if N < 0 or N > (1 << 63) - 1:
        raise ValueError("N is out of bounds.")
    if R < 0 or R > N:
        raise ValueError("R is out of bounds.")

    if N == 0 or R == 0:
        return

    key = derive_position_key_v2(position_key)

    for i in range(R):
        X = i
        while True:
            X = permute(X, N, key)
            if X < N:
                yield X
                break


def get_payload_bit_index_v2(C: int, N: int, R: int, position_key: str) -> int:
    """
    Computes the payload bit index Y for a given carrier position C.
    Returns Y if C is used to store a payload bit (Y < R), else -1.
    """
    key = derive_position_key_v2(position_key)
    Y = C
    while True:
        Y = inverse_permute(Y, N, key)
        if Y < N:
            break
    if Y < R:
        return Y
    return -1
