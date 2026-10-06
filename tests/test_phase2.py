import os
import pytest
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import patch

from stegx.image.embed import embed_payload
from stegx.image.extract import extract_payload
from stegx.video.embed import embed_video_payload
from stegx.video.extract import extract_video_payload
from stegx.cli import app
from typer.testing import CliRunner

runner = CliRunner()

def create_dummy_image(path):
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(path)

def create_dummy_video(path):
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (100, 100))
    for _ in range(10):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        out.write(frame)
    out.release()

def test_overwrite_rejection(tmp_path):
    img_path = str(tmp_path / "carrier.png")
    payload_path = str(tmp_path / "payload.txt")
    out_dir = str(tmp_path / "out")

    create_dummy_image(img_path)
    with open(payload_path, "w") as f:
        f.write("Secret!")

    os.makedirs(out_dir, exist_ok=True)
    # create the file that would be overwritten
    with open(os.path.join(out_dir, "payload.txt"), "w") as f:
        f.write("Old data")

    embed_payload(img_path, payload_path, str(tmp_path / "stego.png"))

    with pytest.raises(FileExistsError, match="already exists"):
        extract_payload(str(tmp_path / "stego.png"), out_dir, force=False)

def test_force_overwrite(tmp_path):
    img_path = str(tmp_path / "carrier.png")
    payload_path = str(tmp_path / "payload.txt")
    out_dir = str(tmp_path / "out")

    create_dummy_image(img_path)
    with open(payload_path, "w") as f:
        f.write("Secret!")

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "payload.txt"), "w") as f:
        f.write("Old data")

    embed_payload(img_path, payload_path, str(tmp_path / "stego.png"))

    # Should not raise
    extract_payload(str(tmp_path / "stego.png"), out_dir, force=True)

    with open(os.path.join(out_dir, "payload.txt"), "r") as f:
        assert f.read() == "Secret!"

def test_insufficient_video_capacity(tmp_path):
    vid_path = str(tmp_path / "carrier.mp4")
    payload_path = str(tmp_path / "huge_payload.txt")

    create_dummy_video(vid_path)

    # Generate a huge file (e.g. 10MB) which exceeds 100x100x3x10 bits capacity (~300k bits)
    with open(payload_path, "wb") as f:
        f.write(b"0" * 10_000_000)

    with pytest.raises(ValueError, match="Payload is too large|exceeds video capacity"):
        embed_video_payload(vid_path, payload_path, str(tmp_path / "stego.mp4"))

def test_password_handling_cli(tmp_path):
    img_path = str(tmp_path / "carrier.png")
    payload_path = str(tmp_path / "payload.txt")
    stego_path = str(tmp_path / "stego.png")
    out_dir = str(tmp_path / "out")

    create_dummy_image(img_path)
    with open(payload_path, "w") as f:
        f.write("Secret!")

    # Provide password via interactive prompt (simulated)
    result = runner.invoke(app, ["hide-image", img_path, payload_path, "--output-path", stego_path, "--sequential", "-p"], input="mysecretpass\n")
    assert result.exit_code == 0
    assert "Payload embedded successfully" in result.stdout

    # Extract using ENV var
    os.environ["STEGX_PASSWORD"] = "mysecretpass"
    result = runner.invoke(app, ["extract-image", stego_path, "--output-directory", out_dir])
    if result.exit_code != 0:
        print("STDOUT:", result.stdout)
    assert result.exit_code == 0

    with open(os.path.join(out_dir, "payload.txt"), "r") as f:
        assert f.read() == "Secret!"

def test_malformed_video(tmp_path):
    vid_path = str(tmp_path / "broken.mp4")
    with open(vid_path, "wb") as f:
        f.write(b"not a video file")

    with pytest.raises(ValueError, match="Could not open|unsupported"):
        from stegx.video.extract import extract_video_payload
        extract_video_payload(vid_path, str(tmp_path))
