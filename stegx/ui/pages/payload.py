import os
import streamlit as st
from stegx.ui.components import page_header, section_header, render_panel
from stegx.core.payload import create_payload_v2

page_header("Payload Builder", "Construct and inspect authenticated StegX V2 payloads.", "STG2", "info")

section_header("Step 1: Raw Data", "Select the file to wrap into a STG2 payload.")
payload_file = st.file_uploader("Upload File")

section_header("Step 2: Cryptography", "Configure Argon2id and ChaCha20-Poly1305.")
password = st.text_input("Master Password", type="password")

st.write("")
if payload_file and password:
    if st.button("📦 BUILD STG2 PAYLOAD", use_container_width=True):
        with st.spinner("Deriving keys and encrypting..."):
            raw_bytes = payload_file.getbuffer().tobytes()
            # create_payload_v2(data, filename, password)
            stg2_payload = create_payload_v2(raw_bytes, payload_file.name, password)
            
            st.session_state["stg2_bytes"] = stg2_payload
            st.session_state["stg2_size"] = len(stg2_payload)

if st.session_state.get("stg2_bytes"):
    st.write("")
    section_header("Payload Structure", "Binary layout analysis")
    
    # Render visual structure
    st.markdown("""
    <div style="font-family: monospace; background: var(--stegx-darker); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--stegx-border); line-height: 1.6;">
        <span style="color: var(--stegx-red);">[ 4B ] MAGIC: STG2</span><br/>
        <span style="color: #FFB86C;">[ 1B ] VERSION: 0x02</span><br/>
        <span style="color: #FFB86C;">[ 1B ] FLAGS</span><br/>
        <span style="color: #FFB86C;">[ 2B ] FILENAME_LEN</span><br/>
        <span style="color: #FFB86C;">[ 8B ] PAYLOAD_LEN</span><br/>
        <span style="color: var(--stegx-blue);">[ VAR ] FILENAME</span><br/>
        <span style="color: var(--stegx-cyan);">[ 16B ] SALT (Argon2id)</span><br/>
        <span style="color: var(--stegx-cyan);">[ 12B ] NONCE (ChaCha20)</span><br/>
        <span style="color: #ECEFF4;">[ VAR ] CIPHERTEXT</span><br/>
        <span style="color: var(--stegx-cyan);">[ 16B ] MAC TAG (Poly1305)</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    render_panel(
        "Build Successful",
        f"Total Payload Size: {st.session_state['stg2_size']} bytes<br/>AEAD: ChaCha20-Poly1305",
        "success"
    )
    
    st.download_button(
        "⬇️ DOWNLOAD .STG2 BINARY",
        data=st.session_state["stg2_bytes"],
        file_name=f"{payload_file.name}.stg2",
        use_container_width=True
    )
