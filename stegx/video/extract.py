import os
import cv2
import numpy as np

from stegx.core.crypto import decrypt_data
from stegx.core.payload import MAGIC, get_payload_info
from stegx.core.positions import generate_positions
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

def extract_bits_from_video(video_path: str, required_bits: int, positions: list[int] | None = None) -> list[int]:
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise ValueError("Could not open the video.")

    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_values = width * height * 3

    positions_by_frame = {}
    if positions is not None:
        if len(positions) != required_bits:
            video.release()
            raise ValueError("Positions array must match required_bits")
        for payload_bit_index, global_position in enumerate(positions):
            frame_index = global_position // frame_values
            local_position = global_position % frame_values
            if frame_index not in positions_by_frame:
                positions_by_frame[frame_index] = []
            positions_by_frame[frame_index].append((local_position, payload_bit_index))

    extracted_bits = [0] * required_bits
    frames_processed = 0
    bit_index = 0

    while True:
        if positions is None and bit_index >= required_bits:
            break
        
        success, frame = video.read()
        if not success:
            break

        flat_frame = frame.reshape(-1)

        if positions is None:
            remaining = required_bits - bit_index
            if remaining <= 0:
                continue
            usable = min(remaining, len(flat_frame))
            extracted_bits[bit_index:bit_index + usable] = (flat_frame[:usable] & 1).tolist()
            bit_index += usable
        else:
            if frames_processed in positions_by_frame:
                for local_pos, payload_bit_index in positions_by_frame[frames_processed]:
                    extracted_bits[payload_bit_index] = int(flat_frame[local_pos] & 1)

        frames_processed += 1

    video.release()
    return extracted_bits

def extract_video_payload(
    video_path: str,
    output_directory: str,
    password: str | None = None,
    position_key: str | None = None,
    force: bool = False,
):
    capacity_info = get_video_capacity(video_path)
    total_positions = capacity_info["available_bits"]

    initial_bits = 17 * 8
    
    if position_key:
        positions = generate_positions(total_positions, initial_bits, position_key)
        initial_bits_data = extract_bits_from_video(video_path, initial_bits, positions)
    else:
        initial_bits_data = extract_bits_from_video(video_path, initial_bits)

    initial_data = bits_to_bytes(initial_bits_data)

    if initial_data[:len(MAGIC)] != MAGIC:
        if position_key:
            raise ValueError("No valid StegX payload signature found. The position key may be incorrect.")
        raise ValueError("No valid StegX payload found in this video.")

    filename_length = int.from_bytes(initial_data[7:9], byteorder="little")
    if filename_length > 255:
        raise ValueError(f"Payload filename length ({filename_length}) exceeds security limits.")

    base_header_size = 5 + 1 + 1 + 2 + filename_length + 8
    header_bits_required = base_header_size * 8

    if position_key:
        positions = generate_positions(total_positions, header_bits_required, position_key)
        header_bits = extract_bits_from_video(video_path, header_bits_required, positions)
    else:
        header_bits = extract_bits_from_video(video_path, header_bits_required)

    base_header = bits_to_bytes(header_bits)

    flags = base_header[6]
    encrypted = bool(flags & 0x01)
    payload_size = int.from_bytes(base_header[-8:], byteorder="little")

    MAX_PAYLOAD_SIZE = 2 * 1024 * 1024 * 1024
    if payload_size > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload size ({payload_size}) exceeds absolute maximum limit ({MAX_PAYLOAD_SIZE} bytes).")

    salt_size = 16 if encrypted else 0
    total_payload_bytes = base_header_size + salt_size + payload_size
    total_payload_bits = total_payload_bytes * 8

    if total_payload_bits > total_positions:
        raise ValueError(f"Payload ({total_payload_bits} bits) exceeds video capacity ({total_positions} bits).")

    filename = base_header[9:9+filename_length].decode("utf-8")
    
    output_path = str(get_safe_output_path(output_directory, filename))
    if os.path.exists(output_path) and not force:
        raise FileExistsError(f"Output file '{output_path}' already exists. Use --force to overwrite.")

    if position_key:
        positions = generate_positions(total_positions, total_payload_bits, position_key)
        payload_bits = extract_bits_from_video(video_path, total_payload_bits, positions)
    else:
        payload_bits = extract_bits_from_video(video_path, total_payload_bits)

    payload_bytes = bits_to_bytes(payload_bits)
    payload_info = get_payload_info(payload_bytes)

    header_size = base_header_size + salt_size
    payload_data = payload_bytes[header_size:header_size + payload_size]

    if payload_info["encrypted"]:
        if not password:
            raise ValueError("This payload is encrypted. A password is required.")
        payload_data = decrypt_data(payload_data, password, payload_info["salt"])

    with open(output_path, "wb") as file:
        file.write(payload_data)

    return {
        "filename": filename,
        "payload_size": len(payload_data),
        "encrypted": encrypted,
        "randomized": bool(position_key),
        "output_path": output_path,
    }
