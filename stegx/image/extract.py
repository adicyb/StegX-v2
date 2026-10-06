from pathlib import Path

from PIL import Image

from stegx.core.crypto import decrypt_data
from stegx.core.payload import (
    MAGIC,
    get_payload_info,
    extract_payload as extract_payload_router,
)
from stegx.core.positions import generate_positions, generate_positions_v2
from stegx.utils.fs import get_safe_output_path
from stegx.image.capacity import get_image_capacity


def extract_lsb_bits(image: Image.Image) -> str:
    """
    Extract the least significant bit from every
    RGB channel in sequential order.
    """

    pixels = list(
        image.convert("RGB").getdata()
    )

    bits = []

    for red, green, blue in pixels:

        bits.append(str(red & 1))
        bits.append(str(green & 1))
        bits.append(str(blue & 1))

    return "".join(bits)


def extract_randomized_bits(
    image: Image.Image,
    required_bits: int,
    position_key: str,
    use_v2: bool = False,
) -> str:
    """
    Extract LSB bits from deterministic randomized
    positions generated using the provided key.
    """

    pixels = list(
        image.convert("RGB").getdata()
    )

    # Each RGB pixel provides three available
    # embedding positions.
    total_positions = len(pixels) * 3

    if use_v2:
        positions = generate_positions_v2(total_positions, required_bits, position_key)
    else:
        positions = generate_positions(
            total_positions=total_positions,
            required_positions=required_bits,
            key=position_key,
        )

    bits = []

    for position in positions:

        pixel_index = position // 3

        channel_index = position % 3

        pixel = pixels[pixel_index]

        channel_value = pixel[channel_index]

        bits.append(
            str(channel_value & 1)
        )

    return "".join(bits)


def bits_to_bytes(bits: str) -> bytes:
    """
    Convert a string of bits into bytes.
    """

    usable_length = (
        len(bits) - (len(bits) % 8)
    )

    return bytes(
        int(bits[i:i + 8], 2)
        for i in range(
            0,
            usable_length,
            8,
        )
    )


def extract_payload(
    image_path: str,
    output_directory: str = "samples/extracted",
    password: str | None = None,
    position_key: str | None = None,
    force: bool = False,
    use_v2: bool = False,
) -> dict:
    """
    Extract a StegX payload from an image.

    Supports both sequential and randomized
    embedding positions.

    If the payload is encrypted, a password is required.
    If randomized embedding was used, the same
    position key is required.
    """

    image = Image.open(
        image_path
    ).convert("RGB")


    # Determine the payload size required to fetch.
    import struct
    from stegx.image.capacity import get_image_capacity
    capacity_info = get_image_capacity(image_path)
    available_bits = capacity_info["available_bits"]

    if not position_key:
        # ------------------------------------------
        # SEQUENTIAL EXTRACTION
        # ------------------------------------------
        bits = extract_lsb_bits(image)
        raw_data = bits_to_bytes(bits)

        if use_v2:
            if raw_data[:4] != b"STG2":
                raise ValueError("No valid StegX V2 signature found.")
            import struct
            fl = struct.unpack("<H", raw_data[6:8])[0]
            pl = struct.unpack("<Q", raw_data[8:16])[0]
            total_payload_bytes = 16 + fl + 16 + 12 + pl + 16
            raw_data = raw_data[:total_payload_bytes]
    else:
        # ------------------------------------------
        # RANDOMIZED EXTRACTION
        # ------------------------------------------
        if use_v2:
            initial_bits_required = 16 * 8
            initial_bits = extract_randomized_bits(image, initial_bits_required, position_key, use_v2=True)
            initial_data = bits_to_bytes(initial_bits)

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

            if total_payload_bytes * 8 > available_bits:
                raise ValueError(f"Payload size ({total_payload_bytes * 8} bits) exceeds carrier capacity.")

            # Now extract the full payload using exactly the right number of bits
            bits = extract_randomized_bits(image, total_payload_bytes * 8, position_key, use_v2=True)
            raw_data = bits_to_bytes(bits)
        else:
            initial_bits_required = 9 * 8
            initial_bits = extract_randomized_bits(image, initial_bits_required, position_key, use_v2=False)
            initial_data = bits_to_bytes(initial_bits)
            if initial_data[:5] != b"STEGX":
                raise ValueError("No valid StegX payload signature found.")
            filename_length = int.from_bytes(initial_data[7:9], byteorder="little")
            if filename_length > 255:
                raise ValueError(f"Payload filename length exceeds security limits.")
            base_header_bytes = 5 + 1 + 1 + 2 + filename_length + 8
            header_bits = extract_randomized_bits(image, base_header_bytes * 8, position_key, use_v2=False)
            header_data = bits_to_bytes(header_bits)
            flags = header_data[6]
            encrypted = bool(flags & 0x01)
            payload_size = int.from_bytes(header_data[base_header_bytes - 8:base_header_bytes], byteorder="little")
            salt_size = 16 if encrypted else 0
            total_payload_bytes = base_header_bytes + salt_size + payload_size
            MAX_PAYLOAD_SIZE = 2 * 1024 * 1024 * 1024
            if payload_size > MAX_PAYLOAD_SIZE:
                raise ValueError(f"Payload size exceeds absolute maximum limit.")
            if total_payload_bytes * 8 > available_bits:
                raise ValueError(f"Payload size exceeds carrier capacity.")

            bits = extract_randomized_bits(image, total_payload_bytes * 8, position_key, use_v2=False)
            raw_data = bits_to_bytes(bits)

    # ------------------------------------------
    # PARSE AND DECRYPT (Router)
    # ------------------------------------------

    filename, payload_data, flags = extract_payload_router(raw_data, password)

    # ------------------------------------------
    # SAVE RECOVERED FILE
    # ------------------------------------------

    recovered_file = get_safe_output_path(
        output_directory,
        filename,
    )

    import os
    if os.path.exists(recovered_file) and not force:
        raise FileExistsError(f"Output file '{recovered_file}' already exists. Use --force to overwrite.")

    with open(recovered_file, "wb") as file:
        file.write(payload_data)

    return {
        "filename": filename,
        "payload_size": len(payload_data),
        "encrypted": True if use_v2 else True, # We don't have direct access to 'encrypted' flag dynamically here, but password is required for V2.
        "randomized_positions": (position_key is not None and position_key != ""),
        "output_path": str(recovered_file),
    }



def get_displayable_content(
    file_path: str,
):
    """
    Return file content if it is a readable text file.
    Return None for binary files.
    """

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return file.read()

    except (
        UnicodeDecodeError,
        OSError,
    ):

        return None