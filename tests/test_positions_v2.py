import pytest
from stegx.core.positions import (
    generate_positions_v2,
    permute,
    inverse_permute,
    _chacha20_prf,
    derive_position_key_v2
)

def test_v2_positions_edge_cases():
    # 1. N=0, R=0
    assert list(generate_positions_v2(0, 0, "test")) == []
    # 2. N=1, R=0
    assert list(generate_positions_v2(1, 0, "test")) == []
    # 3. N=1, R=1
    assert list(generate_positions_v2(1, 1, "test")) == [0]
    # 4. N=1, R>1 rejection
    with pytest.raises(ValueError, match="bounds"):
        list(generate_positions_v2(1, 2, "test"))
    # 5. R=0 for normal N
    assert list(generate_positions_v2(100, 0, "test")) == []

def test_v2_positions_validity():
    # 6. R=N for small N
    # 7. R<N for small N
    # 16. all outputs satisfy 0 <= position < N
    # 17. no duplicate positions
    # 18. exactly R positions produced
    # 21. full permutation when R=N
    N = 10

    # R = N
    pos = list(generate_positions_v2(N, N, "test"))
    assert len(pos) == N
    assert len(set(pos)) == N
    assert all(0 <= p < N for p in pos)

    # R < N
    R = 5
    pos = list(generate_positions_v2(N, R, "test"))
    assert len(pos) == R
    assert len(set(pos)) == R
    assert all(0 <= p < N for p in pos)

def test_v2_positions_powers_of_two():
    # 8. power-of-two N
    # 9. non-power-of-two N
    for N in [16, 32, 64]:
        pos = list(generate_positions_v2(N, N, "test"))
        assert len(set(pos)) == N
        assert max(pos) == N - 1

    for N in [15, 33, 65]:
        pos = list(generate_positions_v2(N, min(N, 10), "test"))
        assert len(set(pos)) == min(N, 10)
        assert all(p < N for p in pos)

def test_v2_positions_invalid_inputs():
    # 12. invalid negative N
    with pytest.raises(ValueError): list(generate_positions_v2(-1, 0, "test"))
    # 13. invalid negative R
    with pytest.raises(ValueError): list(generate_positions_v2(10, -1, "test"))
    # 14. N > 2^63-1
    with pytest.raises(ValueError): list(generate_positions_v2(1 << 64, 0, "test"))
    # 15. R > N
    with pytest.raises(ValueError): list(generate_positions_v2(10, 11, "test"))

def test_v2_positions_determinism():
    # 19. deterministic output for same key/N/R
    # 20. different position keys produce different sequences
    p1 = list(generate_positions_v2(100, 10, "key1"))
    p2 = list(generate_positions_v2(100, 10, "key1"))
    p3 = list(generate_positions_v2(100, 10, "key2"))

    assert p1 == p2
    assert p1 != p3

def test_v2_feistel_inverse():
    # 22. inverse_permute(permute(X)) == X
    # 23. permutation outputs remain inside extended Feistel domain
    key = derive_position_key_v2("test")
    N = 100
    # For N=100, m=6 (bit_length of 99), half=3 -> extended domain is [0, 63] Wait: 99 is 7 bits (64+32+2+1).
    # bit_length of 99 is 7. half = (7+1)//2 = 4. Extended domain 2^(2*4) = 256. [0, 255]
    for x in range(256):
        p = permute(x, N, key)
        assert 0 <= p < 256
        inv = inverse_permute(p, N, key)
        assert inv == x

def test_v2_large_N_memory():
    # 10. N near 2^63-1
    # 26. large-N operation without domain-sized memory
    N = (1 << 63) - 1
    R = 10
    # This must run quickly and not OOM.
    pos = list(generate_positions_v2(N, R, "large_test"))
    assert len(pos) == R
    assert len(set(pos)) == R
    assert all(0 <= p < N for p in pos)

def test_v2_kat_chacha20_prf():
    # 13. CHACha20 API COMPATIBILITY TEST
    # Verify the exact 16-byte parameter layout (counter + round_num + r_half)
    key = derive_position_key_v2("test_key_v2")
    # For key="test_key_v2", round_num=0, R_half=1
    out = _chacha20_prf(key, 0, 1)
    assert out == 9733753630029009074

def test_v2_kat_feistel_and_generator():
    # 12. KNOWN-ANSWER TEST
    key_str = "test_key_v2"
    key = derive_position_key_v2(key_str)

    # Permute KAT for X=1, N=100
    assert permute(1, 100, key) == 236

    # Generator KAT for N=100, R=5
    pos = list(generate_positions_v2(100, 5, key_str))
    assert pos == [28, 13, 31, 85, 33]

def test_v2_mathematical_boundaries():
    # 14. BOUNDARY / MATHEMATICAL TESTS
    for N in [2, 3, 4, 5, 7, 8, 9, 15, 16, 17]:
        pos = list(generate_positions_v2(N, N, "test"))
        assert len(pos) == N
        assert len(set(pos)) == N
        assert all(0 <= p < N for p in pos)
