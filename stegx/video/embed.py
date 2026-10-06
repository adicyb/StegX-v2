import os
import cv2
import numpy as np

from stegx.core.payload import create_payload, create_payload_v2
from stegx.core.positions import generate_positions, get_payload_bit_index_v2

def bytes_to_bits(data: bytes) -> str:
    return "".join(format(byte, "08b") for byte in data)

def embed_video_payload(
    video_path: str,
    payload_path: str,
    output_path: str,
    password: str | None = None,
    position_key: str | None = None,
    force: bool = False,
    use_v2: bool = False,
):
    if os.path.exists(output_path) and not force:
        raise FileExistsError(f"Output file '{output_path}' already exists. Use --force to overwrite.")

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError("Could not open the input video.")

    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    if use_v2:
        if password is None:
            video.release()
            raise ValueError("V2 payload requires a password.")
        filename = os.path.basename(payload_path)
        with open(payload_path, "rb") as f:
            file_data = f.read()
        payload = create_payload_v2(
            file_data=file_data,
            filename=filename,
            password=password,
            randomized=bool(position_key)
        )
    else:
        payload = create_payload(payload_path, password=password)

    payload_bits = bytes_to_bits(payload)
    required_bits = len(payload_bits)

    available_bits = width * height * 3 * frame_count

    if required_bits > available_bits:
        video.release()
        raise ValueError(f"Payload is too large for this video. Required: {required_bits:,} bits, Available: {available_bits:,} bits.")

    # Generate V1 positions if needed
    positions_v1 = None
    positions_by_frame_v1 = {}

    if position_key and not use_v2:
        positions_v1 = generate_positions(available_bits, required_bits, position_key)
        frame_values = width * height * 3
        for payload_bit_index, global_position in enumerate(positions_v1):
            frame_index = global_position // frame_values
            local_position = global_position % frame_values
            if frame_index not in positions_by_frame_v1:
                positions_by_frame_v1[frame_index] = []
            positions_by_frame_v1[frame_index].append((local_position, payload_bit_index))

    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not writer.isOpened():
        video.release()
        raise ValueError("Could not create output video using FFV1 codec.")

    bit_index = 0
    frames_processed = 0
    frame_values = width * height * 3

    # Precompute payload_bits as numpy array for fast access
    payload_bits_arr = np.array([int(b) for b in payload_bits], dtype=np.uint8)

    while True:
        success, frame = video.read()
        if not success:
            break

        flat_frame = frame.reshape(-1)

        if not position_key:
            # Sequential embedding
            if bit_index < required_bits:
                remaining_bits = required_bits - bit_index
                usable_values = min(remaining_bits, len(flat_frame))
                bits = payload_bits_arr[bit_index:bit_index + usable_values]
                flat_frame[:usable_values] &= 0b11111110
                flat_frame[:usable_values] |= bits
                bit_index += usable_values
        else:
            if not use_v2:
                # V1 Randomized
                if frames_processed in positions_by_frame_v1:
                    for local_position, payload_bit_index in positions_by_frame_v1[frames_processed]:
                        flat_frame[local_position] = (flat_frame[local_position] & 0b11111110) | payload_bits_arr[payload_bit_index]
            else:
                # V2 Randomized using Inverse Permutation (streaming mapping)
                # Instead of pre-generating all positions, we check each position in the frame.
                # However, checking every position in every frame might be slow in python!
                # Wait! frame_values is e.g. 1920*1080*3 = 6.2M.
                # Calling a Python function 6.2M times per frame is 0.5s-1s per frame. It might take minutes for a short video.
                # But it fulfills memory requirements! O(1) memory!
                # Let's optimize it slightly by checking if we have already embedded required_bits?
                # No, we can't stop early because positions are random across the entire video.
                base_C = frames_processed * frame_values
                for local_pos in range(len(flat_frame)):
                    C = base_C + local_pos
                    Y = get_payload_bit_index_v2(C, available_bits, required_bits, position_key)
                    if Y != -1:
                        flat_frame[local_pos] = (flat_frame[local_pos] & 0b11111110) | payload_bits_arr[Y]

        writer.write(frame)
        frames_processed += 1

    video.release()
    writer.release()

    if not position_key:
        if bit_index != required_bits:
            raise ValueError("Video ended before the entire payload could be embedded.")

    return {
        "payload_bits": required_bits,
        "available_bits": available_bits,
        "frames_processed": frames_processed,
        "output_path": output_path,
        "encrypted": (password is not None and password != ""),
        "randomized_positions": (position_key is not None and position_key != ""),
    }
