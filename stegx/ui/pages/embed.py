import os
import tempfile
import streamlit as st
from stegx.ui.components import page_header, section_header, render_panel, capacity_meter
from stegx.core.format_handler import get_file_extension, SAFE_IMAGE_FORMATS, CONDITIONAL_IMAGE_FORMATS, VIDEO_FORMATS
from stegx.image.capacity import get_image_capacity
from stegx.video.capacity import get_video_capacity
from stegx.image.embed import embed_payload
from stegx.video.embed import embed_video_payload

page_header("Embed Payload", "Securely embed an authenticated payload into an image or video.", "STG2", "success")

# Step 1: Carrier
section_header("Step 1: Carrier", "Select the image or video to hide data within.")
carrier_file = st.file_uploader("Upload Carrier Media", type=["png", "bmp", "tiff", "tif", "jpg", "jpeg", "webp", "mp4", "mkv", "avi", "mov"])

if carrier_file:
    ext = get_file_extension(carrier_file.name)
    is_video = ext in VIDEO_FORMATS
    st.write(f"**Filename:** {carrier_file.name}")
    st.write(f"**Size:** {carrier_file.size / 1024 / 1024:.2f} MB")
    st.write(f"**Type:** {'Video' if is_video else 'Image'}")

# Step 2: Payload
section_header("Step 2: Payload", "Select the secret file to hide.")
payload_file = st.file_uploader("Upload Secret Payload")
if payload_file:
    st.write(f"**Filename:** {payload_file.name}")
    st.write(f"**Size:** {payload_file.size} bytes")

# Step 3: Security
section_header("Step 3: Security & Positioning", "Configure cryptographic bounds.")
password = st.text_input("V2 Master Password", type="password", help="Required for AEAD ChaCha20-Poly1305 encryption.")

col1, col2 = st.columns(2)
with col1:
    pos_mode = st.radio("Positioning Mode", ["Randomized", "Sequential"], index=0, help="Randomized distributes bits via keyed permutation.")
with col2:
    if pos_mode == "Randomized":
        pos_key = st.text_input("Position Key", type="password", help="PRNG seed for cycle-walking permutation.")
    else:
        pos_key = None
        st.info("Sequential mode: bits are written linearly.")

# Step 4: Action & Capacity
section_header("Step 4: Execute", "Check capacity and process.")
if carrier_file and payload_file:
    # Need to save carrier temporarily to measure capacity safely
    with tempfile.TemporaryDirectory() as td:
        carrier_path = os.path.join(td, carrier_file.name)
        payload_path = os.path.join(td, payload_file.name)
        out_name = f"stego_{carrier_file.name}"
        if not is_video and ext in CONDITIONAL_IMAGE_FORMATS:
            out_name = f"stego_{os.path.splitext(carrier_file.name)[0]}.png"
        if is_video:
            out_name = f"stego_{os.path.splitext(carrier_file.name)[0]}.avi" # FFV1 container
        output_path = os.path.join(td, out_name)
        
        with open(carrier_path, "wb") as f:
            f.write(carrier_file.getbuffer())
        with open(payload_path, "wb") as f:
            f.write(payload_file.getbuffer())
        
        try:
            if is_video:
                cap_bits = get_video_capacity(carrier_path)["available_bits"]
            else:
                cap_bits = get_image_capacity(carrier_path)["available_bits"]
            cap_bytes = cap_bits // 8
            
            # V2 overhead roughly: 16 (magic+ver+flags+pl) + fn_len + 16 (salt) + 12 (nonce) + 16 (tag)
            # Roughly payload_size + fn_len + 60
            req_bytes = payload_file.size + len(payload_file.name.encode('utf-8')) + 60
            
            capacity_meter(cap_bytes, req_bytes)
            
            if req_bytes > cap_bytes:
                render_panel("Insufficient Capacity", "The carrier is too small to hold this payload + metadata overhead.", "error")
            elif not password:
                render_panel("Authentication Required", "A password is required for V2.", "warning")
            elif pos_mode == "Randomized" and not pos_key:
                render_panel("Position Key Required", "A position key is required for Randomized mode.", "warning")
            else:
                if st.button("🔒 EMBED PAYLOAD", use_container_width=True):
                    with st.spinner("Embedding payload..."):
                        if is_video:
                            embed_video_payload(carrier_path, payload_path, output_path, password=password, position_key=pos_key, force=True, use_v2=True)
                        else:
                            embed_payload(carrier_path, payload_path, output_path, password=password, position_key=pos_key, force=True, use_v2=True)
                        
                        if os.path.exists(output_path):
                            with open(output_path, "rb") as out_f:
                                out_bytes = out_f.read()
                            st.session_state["embed_success"] = True
                            st.session_state["embed_bytes"] = out_bytes
                            st.session_state["embed_name"] = out_name
                            st.session_state["embed_size"] = len(out_bytes)
        except Exception as e:
            render_panel("Processing Error", str(e), "error")

if st.session_state.get("embed_success"):
    render_panel("✓ Payload embedded successfully", f"Output: {st.session_state['embed_name']} ({st.session_state['embed_size']} bytes) | Protocol: STG2", "success")
    st.download_button(
        "⬇️ DOWNLOAD OUTPUT",
        data=st.session_state["embed_bytes"],
        file_name=st.session_state["embed_name"],
        use_container_width=True
    )
