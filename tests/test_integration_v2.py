import pytest
from pathlib import Path
from PIL import Image

from stegx.image.embed import embed_payload as image_embed
from stegx.image.extract import extract_payload as image_extract
from stegx.video.embed import embed_video_payload as video_embed
from stegx.video.extract import extract_video_payload as video_extract

def create_test_image(path: Path):
    img = Image.new("RGB", (100, 100), color="red")
    img.save(path)

def create_test_video(path: Path):
    import cv2
    import numpy as np
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"FFV1"), 30, (32, 32))
    for _ in range(5):
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        frame[:] = 128
        writer.write(frame)
    writer.release()

def test_v2_image_round_trip(tmp_path):
    # 1. V2 image round trip.
    # 3. V2 sequential image round trip.
    img_path = tmp_path / "carrier.png"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.png"
    out_dir = tmp_path / "extracted"

    create_test_image(img_path)
    sec_path.write_text("Hello V2 Sequential Image")

    image_embed(str(img_path), str(sec_path), str(out_path), password="pass", use_v2=True)
    res = image_extract(str(out_path), str(out_dir), password="pass", use_v2=True)

    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_text() == "Hello V2 Sequential Image"

def test_v2_randomized_image_round_trip(tmp_path):
    # 2. V2 randomized image round trip.
    img_path = tmp_path / "carrier.png"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.png"
    out_dir = tmp_path / "extracted"

    create_test_image(img_path)
    sec_path.write_text("Hello V2 Randomized Image")

    image_embed(str(img_path), str(sec_path), str(out_path), password="pass", position_key="pos_key", use_v2=True)
    res = image_extract(str(out_path), str(out_dir), password="pass", position_key="pos_key", use_v2=True)

    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_text() == "Hello V2 Randomized Image"

def test_v2_image_wrong_password_or_tampered(tmp_path):
    # 4. Wrong password.
    # 5. Tampered image/carrier.
    img_path = tmp_path / "carrier.png"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.png"
    out_dir = tmp_path / "extracted"

    create_test_image(img_path)
    sec_path.write_text("Secret")
    image_embed(str(img_path), str(sec_path), str(out_path), password="pass", use_v2=True)

    # Wrong password
    with pytest.raises(ValueError, match="Authentication failed"):
        image_extract(str(out_path), str(out_dir), password="wrong", use_v2=True)

    # Tampered image
    img = Image.open(out_path)
    pixels = list(img.getdata())
    # Modify the first pixel significantly to ruin the payload
    pixels[0] = (pixels[0][0] ^ 1, pixels[0][1], pixels[0][2])
    img.putdata(pixels)
    img.save(out_path)

    with pytest.raises(ValueError, match="(Authentication failed|No valid StegX V2 signature found)"):
        image_extract(str(out_path), str(out_dir), password="pass", use_v2=True)

def test_v2_video_round_trip(tmp_path):
    # 1. V2 video round trip.
    # 3. Sequential V2 video.
    vid_path = tmp_path / "carrier.avi"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.avi"
    out_dir = tmp_path / "extracted"

    create_test_video(vid_path)
    sec_path.write_text("Hello V2 Sequential Video")

    video_embed(str(vid_path), str(sec_path), str(out_path), password="pass", use_v2=True)
    res = video_extract(str(out_path), str(out_dir), password="pass", use_v2=True)

    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_text() == "Hello V2 Sequential Video"

def test_v2_randomized_video_round_trip(tmp_path):
    # 2. Randomized V2 video.
    vid_path = tmp_path / "carrier.avi"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.avi"
    out_dir = tmp_path / "extracted"

    create_test_video(vid_path)
    sec_path.write_text("Hello V2 Randomized Video")

    video_embed(str(vid_path), str(sec_path), str(out_path), password="pass", position_key="poskey", use_v2=True)
    res = video_extract(str(out_path), str(out_dir), password="pass", position_key="poskey", use_v2=True)

    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_text() == "Hello V2 Randomized Video"

def test_v2_video_wrong_password_or_tampered(tmp_path):
    # 4. Wrong password.
    # 5. Tampered video.
    vid_path = tmp_path / "carrier.avi"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.avi"
    out_dir = tmp_path / "extracted"

    create_test_video(vid_path)
    sec_path.write_text("Secret")
    video_embed(str(vid_path), str(sec_path), str(out_path), password="pass", use_v2=True)

    with pytest.raises(ValueError, match="Authentication failed"):
        video_extract(str(out_path), str(out_dir), password="wrong", use_v2=True)

    # Tampered video
    import cv2
    cap = cv2.VideoCapture(str(out_path))
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        frames.append(frame)
    cap.release()

    if frames:
        frames[0][0, 0, 0] ^= 1
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"FFV1"), 30, (32, 32))
        for frame in frames:
            writer.write(frame)
        writer.release()

    with pytest.raises(ValueError, match="(Authentication failed|No valid StegX V2 signature found)"):
        video_extract(str(out_path), str(out_dir), password="pass", use_v2=True)

def test_v2_insufficient_capacity(tmp_path):
    # Insufficient carrier capacity.
    vid_path = tmp_path / "carrier.avi"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.avi"

    create_test_video(vid_path) # 32x32x5 frames = small
    # Large payload
    sec_path.write_text("A" * 100000)
    with pytest.raises(ValueError, match="too large"):
        video_embed(str(vid_path), str(sec_path), str(out_path), password="pass", use_v2=True)

def test_v2_image_embed_uses_basename(tmp_path):
    """
    Verify that embedding a payload correctly extracts only the basename
    from the provided payload path, thereby preventing accidental or
    intentional path traversal payloads from being generated at the source.
    (Dedicated extraction-side path traversal is tested in test_security.py).
    """
    img_path = tmp_path / "carrier.png"
    out_path = tmp_path / "stego.png"
    out_dir = tmp_path / "extracted"

    create_test_image(img_path)

    # Create a payload file in a nested directory structure
    nested_dir = tmp_path / "nested" / "deep"
    nested_dir.mkdir(parents=True, exist_ok=True)
    sec_path = nested_dir / "secret.txt"
    sec_path.write_text("deeply nested data")

    # Embed using the deep path
    image_embed(str(img_path), str(sec_path), str(out_path), password="pass", use_v2=True)

    # The embedded filename should just be "secret.txt", not "nested/deep/secret.txt"
    res = image_extract(str(out_path), str(out_dir), password="pass", use_v2=True)
    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_text() == "deeply nested data"

def test_v2_unicode_and_empty(tmp_path):
    img_path = tmp_path / "carrier.png"
    sec_path = tmp_path / "测试.txt"
    out_path = tmp_path / "stego.png"
    out_dir = tmp_path / "extracted"

    create_test_image(img_path)
    sec_path.write_text("")
    image_embed(str(img_path), str(sec_path), str(out_path), password="pass", use_v2=True)

    res = image_extract(str(out_path), str(out_dir), password="pass", use_v2=True)
    assert res["filename"] == "测试.txt"
    assert (out_dir / "测试.txt").read_text() == ""

def test_v2_actual_mapping_image(tmp_path):
    img_path = tmp_path / "carrier.png"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.png"
    out_dir = tmp_path / "extracted"

    create_test_image(img_path)

    # We embed exactly 256 bytes (2048 bits)
    data = bytes(range(256))
    sec_path.write_bytes(data)

    image_embed(str(img_path), str(sec_path), str(out_path), password="pass", position_key="map_test", use_v2=True)
    res = image_extract(str(out_path), str(out_dir), password="pass", position_key="map_test", use_v2=True)

    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_bytes() == data

def test_v2_actual_mapping_video(tmp_path):
    vid_path = tmp_path / "carrier.avi"
    sec_path = tmp_path / "secret.txt"
    out_path = tmp_path / "stego.avi"
    out_dir = tmp_path / "extracted"

    create_test_video(vid_path)

    data = bytes([(x * 3) % 256 for x in range(120)])
    sec_path.write_bytes(data)

    video_embed(str(vid_path), str(sec_path), str(out_path), password="pass", position_key="map_test", use_v2=True)
    res = video_extract(str(out_path), str(out_dir), password="pass", position_key="map_test", use_v2=True)

    assert res["filename"] == "secret.txt"
    assert (out_dir / "secret.txt").read_bytes() == data
