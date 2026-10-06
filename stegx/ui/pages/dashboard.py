import streamlit as st
import importlib.metadata
from stegx.ui.components import render_card, render_status_badge, section_header, page_header, render_panel
from stegx.core.format_handler import SAFE_IMAGE_FORMATS, CONDITIONAL_IMAGE_FORMATS, VIDEO_FORMATS

try:
    __version__ = importlib.metadata.version("stegx")
except importlib.metadata.PackageNotFoundError:
    __version__ = "2.1.0-dev"

page_header(
    "STEGX",
    "Secure Media Steganography Console. Embed authenticated encrypted payloads into images and streaming videos.",
    "STG2 READY",
    "success"
)

col_qa1, col_qa2, col_qa3 = st.columns(3)
with col_qa1:
    if st.button("🔒 Embed Payload", use_container_width=True):
        st.switch_page("pages/embed.py")
with col_qa2:
    if st.button("🔓 Extract Payload", use_container_width=True):
        st.switch_page("pages/extract.py")
with col_qa3:
    if st.button("🔬 Analyze Media", use_container_width=True):
        st.switch_page("pages/analyze.py")

st.write("")
section_header("Security Architecture", "V2 Protocol cryptographic stack")

col1, col2, col3 = st.columns(3)
with col1:
    render_card("Encryption", "ChaCha20-Poly1305", "🔒")
    render_card("Key Derivation", "Argon2id (t=2, m=65MB)", "🔑")
with col2:
    render_card("Positioning", "Keyed Feistel Cycle Walking", "🎲")
    render_card("Metadata", "Authenticated AAD", "🏷️")
with col3:
    render_card("Image Pipeline", "LSB Embedding", "🖼️")
    render_card("Video Pipeline", "O(1) Streaming LSB", "🎞️")

st.markdown("""
<div style="padding: 1.5rem; background: var(--stegx-darker); border: 1px solid var(--stegx-border); border-radius: 8px; margin-bottom: 2rem;">
    <h4 style="margin-top: 0; color: #8C9BAB;">V2 Cryptographic Pipeline</h4>
    <div style="font-family: monospace; color: #ECEFF4; line-height: 1.8;">
        &nbsp;&nbsp;[ Raw Payload File ]<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br/>
        &nbsp;&nbsp;[ Argon2id KDF ] → Derives Master Key<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br/>
        &nbsp;&nbsp;[ ChaCha20-Poly1305 ] → Encrypts & Authenticates<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br/>
        &nbsp;&nbsp;[ Authenticated STG2 Payload ]<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br/>
        &nbsp;&nbsp;[ Keyed Position Permutation ] → Scatters Bits<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br/>
        &nbsp;&nbsp;[ Carrier Media LSB ] → Image / O(1) Video Stream
    </div>
</div>
""", unsafe_allow_html=True)

section_header("Compatibility & Formats", "Supported media and protocol handling")

c_col1, c_col2 = st.columns(2)
with c_col1:
    render_panel("V2 / STG2 Primary", "The default protocol for all new operations. Provides AEAD and deterministic randomization.", "success")
    image_fmts = list(SAFE_IMAGE_FORMATS.keys()) + list(CONDITIONAL_IMAGE_FORMATS.keys())
    st.write(f"**Image Formats:** {', '.join(image_fmts)}")
with c_col2:
    render_panel("V1 Legacy", "Explicitly supported for extraction of old payloads. No automatic upgrade.", "warning")
    video_fmts = list(VIDEO_FORMATS.keys())
    st.write(f"**Video Formats:** {', '.join(video_fmts)}")

st.write("")
st.info("StegX provides authenticated encryption and integrity protection. Steganographic undetectability is not claimed.")
