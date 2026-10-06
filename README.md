<div align="center">

```
 ██████╗▄▄▄█████▓▓█████  ▄████    ▐██▌ 
██╔════╝▓  ██▒ ▓▒▓█   ▀ ██▒ ▀█▒ ▓▓▓▓██▓
╚█████╗ ▒ ▓██░ ▒░▒███  ▒██░▄▄▄░   ▐██▌ 
 ╚═══██╗░ ▓██▓ ░ ▒▓█  ▄ ░▓█  ██▓ ▓▓▓▓██▓
██████╔╝  ▒██▒ ░ ░▒████▒░▒▓███▀▒ ▐██▌ 
╚═════╝   ▒ ░░   ░░ ▒░ ░ ░▒   ▒   ▀▀   
```

**Secure Media Steganography Toolkit for Images and Videos**

<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-4B7BFF?style=flat-square&labelColor=0B0E14" /></a>
<a href="#-license"><img src="https://img.shields.io/badge/License-Educational-00E5A0?style=flat-square&labelColor=0B0E14" /></a>
<a href="#-limitations"><img src="https://img.shields.io/badge/Status-Prototype-FF3B5C?style=flat-square&labelColor=0B0E14" /></a>
<a href="#-usage"><img src="https://img.shields.io/badge/Interface-CLI-ECEFF4?style=flat-square&labelColor=0B0E14" /></a>

**[Features](#-features) · [Install](#-install) · [Quick Start](#-quick-start) · [Commands](#-commands) · [Usage](#-usage) · [Detection](#-detection) · [Testing](#-testing) · [Architecture](#-architecture) · [Roadmap](#-roadmap)**

</div>

<br/>

Every pixel has a channel it doesn't need. StegX writes payloads into that spare bit — across images and video frames — then gives you the tools to encrypt what you hid, measure how much room you have, and prove (or disprove) that something's there at all.

<br/>

## `$ about StegX V2`

StegX defaults to the **StegX V2 protocol**, which provides:
- **Authenticated Encryption**: ChaCha20-Poly1305 + Argon2id ensures confidentiality and tamper-evidence.
- **Randomized Position Generator**: Keyed Feistel cycle-walking permutation scatters payload bits deterministically across the media carrier without ever hitting the same pixel twice.
- **Independent Position Key**: Isolates cryptographic payload security from steganographic carrier placement.
- **Streaming Media Integration**: Zero-memory `O(1)` dynamic position inversion enables mathematically perfect video stream decoding without holding frame pixels in RAM.

⚠️ **Important Security Distinction**:
**Encryption security** provides cryptographic confidentiality and prevents tampering (provided the password is secure).
**Steganographic detectability** is entirely separate. Randomized placement scatters data but does *not* eliminate statistical artifacts. Adversaries using advanced steganalysis or machine learning can still detect the presence of hidden data, even when randomized and encrypted.

<br/>

## `$ features`

<table>
<tr>
<th width="33%">Image</th>
<th width="33%">Video</th>
<th width="34%">Encryption</th>
</tr>
<tr valign="top">
<td>

LSB embedding into PNG, BMP, TIFF/TIF carriers. JPEG/WebP inputs are detected and redirected to a safe lossless output. Capacity calculation, extraction, and automatic preview of recovered text files. Optional key-based randomized pixel selection in place of sequential embedding.

</td>
<td>

Frame-by-frame LSB embedding with FFV1 lossless codec support, pixel-level integrity verification, and video info / capacity analysis.

</td>
<td>

Optional password-based encryption, applied **before** embedding — PBKDF2-HMAC-SHA256, a random 16-byte salt, 600,000 iterations, and Fernet authenticated encryption.

</td>
</tr>
</table>

<br/>

## `$ detect`

Two engines, one command. `detect` figures out whether your file is an image or video, then runs both.

<table>
<tr>
<th width="20%"></th>
<th width="40%">signature</th>
<th width="40%">heuristic</th>
</tr>
<tr valign="top">
<td><b>method</b></td>
<td>Scans for StegX's structured <code>STEGX</code> magic header</td>
<td>Measures statistical properties of the LSB plane</td>
</tr>
<tr valign="top">
<td><b>recovers</b></td>
<td>Version · encryption status · filename · payload size</td>
<td>Entropy · chi-square · bit balance · suspicion score</td>
</tr>
<tr valign="top">
<td><b>certainty</b></td>
<td>Definitive — confirms a known StegX payload</td>
<td>Probabilistic — flags anomalies, proves nothing</td>
</tr>
</table>

> Heuristic analysis never proves hidden data exists. It only surfaces statistics that *may* indicate it.

```bash
python3 -m stegx.cli detect samples/test_stego.png
```

If the payload was embedded with `--position-key`, pass the same key to `detect` so the signature scan can locate the header at its randomized offsets:

```bash
python3 -m stegx.cli detect samples/random_stego.png --position-key mysecretkey
```

<details>
<summary><b>sample report</b></summary>

```text
--- StegX Detection Report ---

File: samples/stego_video.avi
Media Type: Video
Format: AVI

--- Signature Analysis ---
[+] STEGX signature: DETECTED
[+] Version: 1
[+] Encrypted: False
[+] Original filename: secret.txt
[+] Payload size: 17 B

--- Heuristic Analysis ---
Frames analyzed: 20
Suspicion Score: 0/100
Verdict: Low suspicion

--- Overall Result ---
[+] KNOWN STEGX PAYLOAD DETECTED
[+] Hidden data is confirmed by the STEGX signature.
```

</details>

<br/>

## `$ architecture`

```
StegX
│
├── stegx/
│   ├── core/              shared primitives
│   │   ├── crypto.py          encryption · key derivation
│   │   ├── format_handler.py  media format validation
│   │   └── payload.py         payload packing · parsing
│   │
│   ├── image/              image pipeline
│   │   ├── capacity.py
│   │   ├── embed.py
│   │   └── extract.py
│   │
│   ├── video/               video pipeline
│   │   ├── analyze.py
│   │   ├── capacity.py
│   │   ├── codec_test.py
│   │   ├── detection.py
│   │   ├── embed.py
│   │   ├── extract.py
│   │   ├── heuristic.py
│   │   └── integrity.py
│   │
│   ├── analysis/            detection engines
│   │   ├── heuristic.py
│   │   └── signature.py
│   │
│   ├── utils/
│   │   └── banner.py
│   │
│   └── cli.py                entry point
│
├── samples/
├── requirements.txt
├── pyproject.toml
└── README.md
```

<br/>

## `$ requirements`

- Python 3.10+
- pip
- OpenCV-compatible video backend
- FFV1 codec support for lossless video embedding

<br/>

## `$ install`

Clone the repository:

```bash
git clone https://github.com/adicyb/StegX.git
cd StegX
```

Create and activate a virtual environment:

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

Then install StegX itself (this uses `pyproject.toml` and registers the `stegx` command on your `PATH`):

```bash
pip install -e .
```

> Installing only `requirements.txt` sets up the dependencies but does **not** install the `stegx` command. Use `pip install -e .` to get the CLI entry point.

Once installed, verify it worked:

```bash
stegx
```

<br/>

## `$ quick start`

After installation, launch StegX by running:

```bash
stegx
```

This displays the StegX banner and the available commands, grouped into Image, Video, and Detection categories.

For help with a specific command:

```bash
stegx COMMAND --help
```

For example:

```bash
stegx hide-image --help
stegx extract-image --help
stegx hide-video --help
stegx extract-video --help
```

<br/>

## `$ commands`

Running `stegx` with no arguments displays the available commands grouped by category.

### Image Commands

| Command | Description |
|---|---|
| `info` | Display information about StegX |
| `formats` | Display supported media formats |
| `check FILE` | Check whether a media file is supported |
| `capacity IMAGE` | Calculate image payload capacity |
| `payload-info FILE` | Inspect a StegX payload |
| `hide-image` | Hide a file inside an image |
| `extract-image` | Extract hidden data from an image |
| `analyze-signature` | Analyze an image for a StegX signature |
| `analyze-heuristic` | Analyze an image for possible LSB steganography |

### Video Commands

| Command | Description |
|---|---|
| `video-info VIDEO` | Display video information |
| `video-capacity VIDEO` | Calculate video payload capacity |
| `codec-test VIDEO` | Test video codec compatibility |
| `video-integrity ORIGINAL MODIFIED` | Compare original and modified video frames |
| `hide-video` | Hide a file inside a video |
| `extract-video` | Extract hidden data from a video |
| `analyze-video-signature` | Analyze a video for a StegX signature |
| `analyze-video-heuristic` | Analyze a video for possible steganographic artifacts |

### Detection

| Command | Description |
|---|---|
| `detect FILE` | Detect possible StegX payloads using signature and heuristic analysis |

<br/>

## `$ usage`

### StegX V2

StegX defaults to the modern V2 format, which requires a password and an independent position key (for default randomized mode).

#### Password Handling
Passwords are never accepted as plaintext command-line arguments to prevent leakage in shell history or process monitors.
Use `-p` or `--password` to trigger a secure interactive prompt. For automation, the `STEGX_PASSWORD` environment variable is supported (with a security warning).

#### Overwrite Protection
Extraction uses safe path resolution. Existing files will not be overwritten unless `--force` (`-f`) is explicitly provided.

<details open>
<summary><b>image</b></summary>

```bash
# V2 embedding (randomized by default)
python3 -m stegx.cli hide-image \
  samples/carrier.png \
  samples/secret.txt \
  --output-path samples/stego.png \
  --position-key my_random_seed \
  -p

# Extraction
python3 -m stegx.cli extract-image \
  samples/stego.png \
  --output-directory samples/extracted \
  --position-key my_random_seed \
  -p
```

> The `--position-key` controls *where* bits are hidden. The `-p` password controls *what* the bits decrypt to.

If low latency is required, you can use sequential mode:
```bash
python3 -m stegx.cli hide-image samples/carrier.png samples/secret.txt -p --sequential
```
</details>

<details open>
<summary><b>video (streaming support)</b></summary>

Video embedding utilizes an $\mathcal{O}(1)$ algorithmic position inverse, guaranteeing that neither the embedding nor the extraction routines store arrays of video pixels in memory.

```bash
python3 -m stegx.cli hide-video \
  samples/video.mp4 \
  samples/secret.txt \
  --output-path samples/stego.avi \
  --position-key video_seed \
  -p

python3 -m stegx.cli extract-video \
  samples/stego.avi \
  --position-key video_seed \
  -p
```

> ⚠️ **Important:** LSB-based video embedding requires pixel values to survive encoding. StegX currently uses the **FFV1 lossless codec** for stego video output. Transcoding it to MP4/H.264 or uploading it to web platforms will destroy the payload.

</details>

<details open>
<summary><b>V1 legacy format</b></summary>

To use or extract legacy unauthenticated StegX V1 payloads, pass the `--v1` flag.
```bash
python3 -m stegx.cli hide-image samples/carrier.png samples/secret.txt --v1
python3 -m stegx.cli extract-image samples/stego.png --v1
```

</details>

<br/>

## `$ payload format`

### V2 Format (Authenticated)

```text
┌───────────────┐
│ MAGIC: STG2   │  4 bytes
├───────────────┤
│ VERSION       │  1 byte (0x02)
├───────────────┤
│ FLAGS         │  1 byte
├───────────────┤
│ SALT          │  16 bytes (Argon2id)
├───────────────┤
│ NONCE         │  12 bytes (ChaCha20)
├───────────────┤
│ CIPHERTEXT    │  variable
├───────────────┤
│ MAC TAG       │  16 bytes (Poly1305)
└───────────────┘
```

The ciphertext encapsulates the filename length, filename, and plaintext data. Validating the Poly1305 MAC tag guarantees cryptographic integrity of the payload, rejecting incorrect passwords and tampering identically to prevent oracle attacks.

### Protocol Details
- **Key Derivation:** Argon2id (t=2, m=65536 KiB, p=4) derives 32 bytes from the interactive password.
- **AEAD:** ChaCha20-Poly1305 (RFC 7539).
- **Position Generation:** Keyed Feistel cycle-walking permutation using ChaCha20 as the PRF, domain separated strictly for position layout.

<br/>

## `$ testing`

Run the complete test suite using:

```bash
pytest -v
```

The project currently includes tests for:

- Payload creation and validation
- Encryption and decryption
- Incorrect password handling
- Randomized embedding positions
- Image embedding and extraction
- Video embedding and extraction
- Encrypted and randomized workflows

Current test suite: **95 tests passing**.

<br/>

## `$ limitations`

- **Steganalysis:** Randomized pixel selection mathematically disperses bits but does **not** make the steganography undetectable. Advanced heuristic or machine-learning steganalysis can still detect carrier alteration. Do not confuse encryption security with steganographic invisibility.
- **Video Compression:** Video embedding requires a lossless codec (FFV1). Any lossy recompression (e.g. to MP4/H.264) will destroy the payload.
- **Legacy Fallback:** The CLI does not silently fallback between V1 and V2. Legacy payload extraction requires the explicit `--v1` flag.

<br/>

## `$ roadmap`

- [x] Key-based randomized pixel selection *(images)*
- [ ] Key-based randomized pixel selection *(video)*
- [ ] Multi-bit embedding options
- [ ] Additional image formats
- [ ] Audio steganography
- [ ] Advanced steganalysis techniques
- [ ] ML-based steganography detection
- [ ] GUI / web interface
- [ ] Batch media analysis
- [ ] Automated report generation

<br/>

---

<div align="center">

<sub>Built for cybersecurity education, digital forensics research, and steganography experimentation.</sub>
<br/>
<sub><strong>Not to be used for concealing malicious content or evading legitimate security controls.</strong></sub>

<br/><br/>

<sub><strong>Aditya Khandelwal</strong> — Cybersecurity · Digital Forensics · Security Research</sub>
<br/>
<sub>Educational / research use · ⭐ star the repo if StegX was useful to you</sub>

</div>