import os
import tempfile
import streamlit as st
from stegx.ui.components import page_header, section_header, render_panel
from stegx.core.format_handler import get_file_extension, VIDEO_FORMATS
from stegx.image.extract import extract_payload
from stegx.video.extract import extract_video_payload

page_header("Extract Payload", "Authenticate and extract a payload from a StegX carrier.", "STG2", "success")

section_header("Step 1: Stego Carrier", "Upload the suspect media.")
carrier_file = st.file_uploader("Upload Carrier Media", type=["png", "bmp", "tiff", "tif", "avi", "mkv", "mp4", "mov"])

if carrier_file:
    ext = get_file_extension(carrier_file.name)
    is_video = ext in VIDEO_FORMATS
    st.write(f"**Filename:** {carrier_file.name}")
    
    with tempfile.TemporaryDirectory() as td:
        carrier_path = os.path.join(td, carrier_file.name)
        with open(carrier_path, "wb") as f:
            f.write(carrier_file.getbuffer())
        
        # We can't perfectly run detection without the position key if it was randomized,
        # but the API allows checking sequential. To be safe, we rely on the user providing keys below.
        
        section_header("Step 2: Authentication", "Provide cryptographic parameters.")
        col1, col2, col3 = st.columns(3)
        with col1:
            password = st.text_input("Master Password", type="password")
        with col2:
            pos_key = st.text_input("Position Key (Optional)", type="password", help="Leave blank if sequential.")
        with col3:
            v1_compat = st.checkbox("V1 Legacy Mode", help="Extract using the old unauthenticated protocol.")

        st.write("")
        if st.button("🔓 EXTRACT PAYLOAD", use_container_width=True):
            if not password and not v1_compat:
                render_panel("Authentication Required", "A password is required for V2 extraction.", "warning")
            else:
                out_dir = os.path.join(td, "extracted")
                os.makedirs(out_dir, exist_ok=True)
                
                try:
                    with st.spinner("Authenticating and extracting..."):
                        if is_video:
                            res = extract_video_payload(carrier_path, out_dir, password=password, position_key=pos_key if pos_key else None, force=True, use_v2=not v1_compat)
                        else:
                            res = extract_payload(carrier_path, out_dir, password=password, position_key=pos_key if pos_key else None, force=True, use_v2=not v1_compat)
                        
                        extracted_file = os.path.join(out_dir, res["filename"])
                        if os.path.exists(extracted_file):
                            with open(extracted_file, "rb") as ef:
                                e_bytes = ef.read()
                            
                            st.session_state["ext_success"] = True
                            st.session_state["ext_bytes"] = e_bytes
                            st.session_state["ext_name"] = res["filename"]
                            st.session_state["ext_proto"] = "V1" if v1_compat else "V2 (STG2)"
                            
                except Exception as e:
                    render_panel("Extraction Failed", str(e), "error")
                    st.session_state["ext_success"] = False

if st.session_state.get("ext_success"):
    render_panel(
        "✓ Payload authenticated and extracted", 
        f"Filename: {st.session_state['ext_name']}<br/>Size: {len(st.session_state['ext_bytes'])} bytes<br/>Protocol: {st.session_state['ext_proto']}", 
        "success"
    )
    st.download_button(
        "⬇️ DOWNLOAD PAYLOAD",
        data=st.session_state["ext_bytes"],
        file_name=st.session_state["ext_name"],
        use_container_width=True
    )
