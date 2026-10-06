import sys
import platform
import importlib.metadata
import streamlit as st
from stegx.ui.components import page_header, section_header, render_card

try:
    __version__ = importlib.metadata.version("stegx")
except importlib.metadata.PackageNotFoundError:
    __version__ = "2.1.0-dev"

page_header("Console Settings", "System information and security configurations.", "SYSTEM", "info")

section_header("Environment", "Host and runtime telemetry")

col1, col2 = st.columns(2)
with col1:
    render_card("Python Version", sys.version.split(" ")[0], "🐍")
    render_card("Platform", platform.system() + " " + platform.release(), "🖥️")
with col2:
    render_card("StegX Version", f"v{__version__}", "🛡️")
    
    try:
        crypto_ver = importlib.metadata.version("cryptography")
    except:
        crypto_ver = "Unknown"
    render_card("Cryptography", f"v{crypto_ver}", "🔒")

st.write("")
section_header("Security Disclaimer", "Operational limitations")
st.warning("""
**StegX provides authenticated encryption and integrity protection.**

The V2 protocol (STG2) uses robust cryptography (ChaCha20-Poly1305 and Argon2id) to ensure that embedded payloads remain confidential and tamper-evident. The V2 position generator (Keyed Feistel with Cycle Walking) randomizes the distribution of payload bits across the carrier medium.

**However, steganographic undetectability is NOT guaranteed.**
Randomized bit distribution mitigates visual artifacts but introduces statistical noise in the LSB plane. Advanced steganalysis tools (such as structural analysis or ML-based detectors) can still identify carrier alteration. StegX should not be relied upon to perfectly evade state-level heuristic steganalysis.
""")
