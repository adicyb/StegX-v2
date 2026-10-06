import pytest
from stegx.core.positions import generate_positions_v2, get_payload_bit_index_v2

def test_inverse_mapping_exhaustive():
    """
    Exhaustively proves that get_payload_bit_index_v2 is the exact inverse
    of the forward cycle-walking position generator.
    """
    for N in range(1, 101):
        for R in [0, 1, N//2, N-1, N]:
            if R > N: continue

            key = f"test_key_{N}_{R}"
            forward_positions = list(generate_positions_v2(N, R, key))

            # Check length and uniqueness
            assert len(forward_positions) == R
            assert len(set(forward_positions)) == R

            # Verify mapping
            for payload_index, carrier_position in enumerate(forward_positions):
                recovered_index = get_payload_bit_index_v2(carrier_position, N, R, key)
                assert recovered_index == payload_index, f"N={N}, R={R}, C={carrier_position}, Expected Y={payload_index}, Got={recovered_index}"

            # Verify unused positions
            used_positions = set(forward_positions)
            for C in range(N):
                if C not in used_positions:
                    recovered_index = get_payload_bit_index_v2(C, N, R, key)
                    assert recovered_index == -1, f"N={N}, R={R}, C={C} should be unused, got {recovered_index}"

def test_edge_cases():
    """
    Explicit edge case test for R=0, R=1, R=N, R=N-1, N=1,2,3,4,5,7,8,9,15,16,17.
    """
    N_values = [1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17]
    for N in N_values:
        for R in [0, 1, N-1, N]:
            if R < 0 or R > N: continue
            key = f"edge_key_{N}_{R}"
            forward = list(generate_positions_v2(N, R, key))
            for payload_index, C in enumerate(forward):
                assert get_payload_bit_index_v2(C, N, R, key) == payload_index
