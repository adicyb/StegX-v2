import pytest
from typer.testing import CliRunner
import os
from PIL import Image

from stegx.cli import app

runner = CliRunner()

def create_test_image(path: str):
    img = Image.new("RGB", (100, 100), color="red")
    img.save(path)

def create_test_video(path: str):
    import cv2
    import numpy as np
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"FFV1"), 30, (32, 32))
    for _ in range(5):
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        frame[:] = 128
        writer.write(frame)
    writer.release()

@pytest.fixture
def test_files(tmp_path):
    img_path = str(tmp_path / "carrier.png")
    vid_path = str(tmp_path / "carrier.avi")
    sec_path = str(tmp_path / "secret.txt")
    out_img = str(tmp_path / "stego.png")
    out_vid = str(tmp_path / "stego.avi")
    out_dir = str(tmp_path / "extracted")

    create_test_image(img_path)
    create_test_video(vid_path)
    with open(sec_path, "wb") as f:
        f.write(b"Hello V2 CLI")

    return {
        "img": img_path,
        "vid": vid_path,
        "sec": sec_path,
        "out_img": out_img,
        "out_vid": out_vid,
        "out_dir": out_dir,
    }

def test_v2_image_embedding_and_extraction_sequential(test_files):
    # Sequential mode (no position key required)
    result = runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--sequential"
    ], input="mypassword\n")
    assert result.exit_code == 0
    assert "Payload embedded successfully" in result.stdout
    assert "mypassword" not in result.stdout
    assert "mypassword" not in result.stderr if result.stderr else True

    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"]
    ], input="mypassword\n")
    assert result.exit_code == 0
    assert "Payload extracted successfully" in result.stdout
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "rb") as f:
        assert f.read() == b"Hello V2 CLI"

def test_v2_image_randomized(test_files):
    # Randomized is default, requires position key
    result = runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--position-key", "myposkey"
    ], input="mypassword\n")
    assert result.exit_code == 0

    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"],
        "--position-key", "myposkey"
    ], input="mypassword\n")
    assert result.exit_code == 0
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "rb") as f:
        assert f.read() == b"Hello V2 CLI"

def test_position_key_required_for_randomized(test_files):
    # Defaults to randomized, but no position key provided -> should fail
    result = runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"]
    ], input="mypassword\n")
    assert result.exit_code != 0
    assert "requires an independent --position-key" in result.stderr

def test_password_is_never_printed(test_files):
    result = runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--sequential"
    ], input="secret_pass_123\n")
    assert "secret_pass_123" not in result.stdout
    assert "secret_pass_123" not in result.stderr if result.stderr else True

def test_wrong_password(test_files):
    runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--sequential"
    ], input="correct_pass\n")

    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"]
    ], input="wrong_pass\n")
    assert result.exit_code != 0
    assert "Authentication failed" in result.stdout

def test_tampered_carrier(test_files):
    runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--sequential"
    ], input="correct_pass\n")

    # Tamper with image
    img = Image.open(test_files["out_img"])
    pixels = list(img.getdata())
    pixels[0] = (pixels[0][0] ^ 1, pixels[0][1], pixels[0][2])
    img.putdata(pixels)
    img.save(test_files["out_img"])

    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"]
    ], input="correct_pass\n")
    assert result.exit_code != 0
    # Could be No valid StegX V2 signature found, or Authentication failed. Both are fine.
    assert "Extraction failed" in result.stdout or "No valid" in result.stdout or "Authentication" in result.stdout

def test_v2_video_embedding_extraction(test_files):
    result = runner.invoke(app, [
        "hide-video", test_files["vid"], test_files["sec"], "-p",
        "--output-path", test_files["out_vid"],
        "--sequential"
    ], input="mypassword\n")
    assert result.exit_code == 0

    result = runner.invoke(app, [
        "extract-video", test_files["out_vid"], "-p",
        "--output-directory", test_files["out_dir"]
    ], input="mypassword\n")
    assert result.exit_code == 0
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "rb") as f:
        assert f.read() == b"Hello V2 CLI"

def test_v2_video_randomized(test_files):
    result = runner.invoke(app, [
        "hide-video", test_files["vid"], test_files["sec"], "-p",
        "--output-path", test_files["out_vid"],
        "--position-key", "vidkey"
    ], input="mypassword\n")
    assert result.exit_code == 0

    result = runner.invoke(app, [
        "extract-video", test_files["out_vid"], "-p",
        "--output-directory", test_files["out_dir"],
        "--position-key", "vidkey"
    ], input="mypassword\n")
    assert result.exit_code == 0
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "rb") as f:
        assert f.read() == b"Hello V2 CLI"

def test_stegx_password_env_var(test_files):
    os.environ["STEGX_PASSWORD"] = "env_password"
    result = runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"],
        "--output-path", test_files["out_img"],
        "--sequential"
    ])
    assert result.exit_code == 0
    assert "env_password" not in result.stdout
    assert "Warning: STEGX_PASSWORD environment variable is used" in result.stdout

    result = runner.invoke(app, [
        "extract-image", test_files["out_img"],
        "--output-directory", test_files["out_dir"]
    ])
    assert result.exit_code == 0
    del os.environ["STEGX_PASSWORD"]

def test_existing_output_rejected_without_force(test_files):
    os.makedirs(test_files["out_dir"], exist_ok=True)
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "wb") as f:
        f.write(b"existing")

    runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--sequential"
    ], input="pass\n")

    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"]
    ], input="pass\n")
    assert result.exit_code != 0
    assert "Use --force to overwrite" in result.stdout

    # With --force
    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"],
        "--force"
    ], input="pass\n")
    assert result.exit_code == 0
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "rb") as f:
        assert f.read() == b"Hello V2 CLI"

def test_invalid_arguments_return_nonzero(test_files):
    result = runner.invoke(app, ["hide-image", "nonexistent.png", "secret.txt"])
    assert result.exit_code != 0

def test_v1_compatibility_workflow(test_files):
    # Hide with --v1
    result = runner.invoke(app, [
        "hide-image", test_files["img"], test_files["sec"], "-p",
        "--output-path", test_files["out_img"],
        "--v1"
    ], input="mypassword\n")
    assert result.exit_code == 0

    # Extract with V2 default -> Should fail, does not fallback
    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"]
    ], input="mypassword\n")
    assert result.exit_code != 0

    # Extract with --v1 -> Should succeed
    result = runner.invoke(app, [
        "extract-image", test_files["out_img"], "-p",
        "--output-directory", test_files["out_dir"],
        "--v1"
    ], input="mypassword\n")
    assert result.exit_code == 0
    with open(os.path.join(test_files["out_dir"], "secret.txt"), "rb") as f:
        assert f.read() == b"Hello V2 CLI"
