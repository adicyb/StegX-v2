import os
import cv2
import numpy as np
import struct

from stegx.core.crypto import decrypt_data
from stegx.core.payload import MAGIC, get_payload_info, extract_payload as extract_payload_router
from stegx.core.positions import generate_positions, get_payload_bit_index_v2
from stegx.utils.fs import get_safe_output_path
from stegx.video.capacity import get_video_capacity

def bits_to_bytes(bits: list[int]) -> bytes:
    output = bytearray()
    for index in range(0, len(bits), 8):
        byte_bits = bits[index:index + 8]
        if len(byte_bits) < 8:
            break
        value = 0
        for bit in byte_bits:
            value = (value << 1) | bit
        output.append(value)
    return bytes(output)

def extract_video_payload(
    video_path: str,
    output_directory: str,
    password: str | None = None,
    position_key: str | None = None,
    force: bool = False,
    use_v2: bool = False,
):
    capacity_info = get_video_capacity(video_path)
    total_positions = capacity_info["available_bits"]

    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError("Could not open the video.")

    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_values = width * height * 3

    # We need a 2-stage extraction because V2 metadata is at the start of the *authenticated* payload.
    # However, since the video capacity is known and the payload is small enough (1 GiB max),
    # we can extract exactly what we need.

    # Wait, for randomized, we must know required_bits before extracting.
    # So we do two full passes over the video, or we buffer extracted bits.
    # "Do not load the complete video into memory."
    # If we do 2 passes: Pass 1 extracts the header. Pass 2 extracts the whole payload.
    # This is safe and O(1) memory!

    def extract_streaming(req_bits: int) -> bytes:
        cap = cv2.VideoCapture(video_path)
        extracted = [0] * req_bits

        # Precompute V1 positions if needed
        v1_by_frame = {}
        if position_key and not use_v2:
            v1_pos = generate_positions(total_positions, req_bits, position_key)
            for pb_idx, gp in enumerate(v1_pos):
                fi = gp // frame_values
                lp = gp % frame_values
                if fi not in v1_by_frame:
                    v1_by_frame[fi] = []
                v1_by_frame[fi].append((lp, pb_idx))

        frames_processed = 0
        bit_index = 0

        while True:
            succ, frame = cap.read()
            if not succ:
                break

            flat = frame.reshape(-1)

            if not position_key:
                rem = req_bits - bit_index
                if rem <= 0:
                    break
                us = min(rem, len(flat))
                extracted[bit_index:bit_index+us] = (flat[:us] & 1).tolist()
                bit_index += us
            else:
                if not use_v2:
                    if frames_processed in v1_by_frame:
                        for lp, pb_idx in v1_by_frame[frames_processed]:
                            extracted[pb_idx] = int(flat[lp] & 1)
                else:
                    base_C = frames_processed * frame_values
                    for lp in range(len(flat)):
                        C = base_C + lp
                        Y = get_payload_bit_index_v2(C, total_positions, req_bits, position_key)
                        if Y != -1:
                            extracted[Y] = int(flat[lp] & 1)

            frames_processed += 1

        cap.release()
        return bits_to_bytes(extracted)

    if not use_v2:
        # V1
        initial_bits = 17 * 8
        initial_data = extract_streaming(initial_bits)

        if initial_data[:len(MAGIC)] != MAGIC:
            if position_key:
                raise ValueError("No valid StegX payload signature found. The position key may be incorrect.")
            raise ValueError("No valid StegX payload found in this video.")

        filename_length = int.from_bytes(initial_data[7:9], byteorder="little")
        if filename_length > 255:
            raise ValueError(f"Payload filename length ({filename_length}) exceeds security limits.")

        base_header_size = 5 + 1 + 1 + 2 + filename_length + 8
        header_data = extract_streaming(base_header_size * 8)

        flags = header_data[6]
        encrypted = bool(flags & 0x01)
        payload_size = int.from_bytes(header_data[-8:], byteorder="little")

        MAX_PAYLOAD_SIZE = 2 * 1024 * 1024 * 1024
        if payload_size > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload size ({payload_size}) exceeds absolute maximum limit ({MAX_PAYLOAD_SIZE} bytes).")

        salt_size = 16 if encrypted else 0
        total_payload_bytes = base_header_size + salt_size + payload_size
        total_payload_bits = total_payload_bytes * 8

        if total_payload_bits > total_positions:
            raise ValueError(f"Payload ({total_payload_bits} bits) exceeds video capacity ({total_positions} bits).")

        payload_bytes = extract_streaming(total_payload_bits)

        # Use V1 decrypt logic
        payload_info = get_payload_info(payload_bytes)
        header_size = base_header_size + salt_size
        payload_data = payload_bytes[header_size:header_size + payload_size]

        if payload_info["encrypted"]:
            if not password:
                raise ValueError("This payload is encrypted. A password is required.")
            payload_data = decrypt_data(payload_data, password, payload_info["salt"])

        filename = payload_info["filename"]
        encrypted = payload_info["encrypted"]

    else:
        # V2
        initial_bits = 16 * 8
        initial_data = extract_streaming(initial_bits)

        if initial_data[:4] != b"STG2":
            raise ValueError("No valid StegX V2 signature found. The position key may be incorrect.")

        fl = struct.unpack("<H", initial_data[6:8])[0]
        pl = struct.unpack("<Q", initial_data[8:16])[0]

        if fl > 255:
            raise ValueError(f"Payload filename length exceeds security limits.")
        MAX_PAYLOAD_SIZE = 2 * 1024 * 1024 * 1024
        if pl > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload size exceeds absolute maximum limit.")

        total_payload_bytes = 16 + fl + 16 + 12 + pl + 16
        if total_payload_bytes * 8 > total_positions:
            raise ValueError(f"Payload size ({total_payload_bytes * 8} bits) exceeds video capacity.")

        payload_bytes = extract_streaming(total_payload_bytes * 8)

        filename, payload_data, flags = extract_payload_router(payload_bytes, password)
        encrypted = True

    video.release()

    # OUTPUT WRITING (After Authentication)
    output_path = str(get_safe_output_path(output_directory, filename))
    if os.path.exists(output_path) and not force:
        raise FileExistsError(f"Output file '{output_path}' already exists. Use --force to overwrite.")

    with open(output_path, "wb") as file:
        file.write(payload_data)

    return {
        "filename": filename,
        "payload_size": len(payload_data),
        "encrypted": encrypted,
        "randomized": bool(position_key),
        "output_path": output_path,
    }
