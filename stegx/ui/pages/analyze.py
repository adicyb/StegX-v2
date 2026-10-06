import os
import tempfile
import streamlit as st
from stegx.ui.components import page_header, section_header, render_panel
from stegx.core.format_handler import get_file_extension, VIDEO_FORMATS
from stegx.analysis.signature import analyze_signature
from stegx.analysis.heuristic import analyze_heuristics
from stegx.video.detection import analyze_video_signature
from stegx.video.heuristic import analyze_video_heuristics

page_header("Media Analysis", "Perform signature and heuristic forensics on suspect media.", "ANALYSIS", "info")

carrier_file = st.file_uploader("Upload Suspect Media", type=["png", "bmp", "tiff", "tif", "avi", "mkv", "mp4", "mov"])

if carrier_file:
    ext = get_file_extension(carrier_file.name)
    is_video = ext in VIDEO_FORMATS
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Target:** {carrier_file.name}")
    with col2:
        pos_key = st.text_input("Position Key (Optional)", type="password", help="Required to detect randomized V2 signatures.")
    
    st.write("")
    if st.button("🔬 RUN ANALYSIS", use_container_width=True):
        with tempfile.TemporaryDirectory() as td:
            carrier_path = os.path.join(td, carrier_file.name)
            with open(carrier_path, "wb") as f:
                f.write(carrier_file.getbuffer())
            
            with st.spinner("Analyzing media..."):
                # Run Signature
                if is_video:
                    sig_res = analyze_video_signature(carrier_path, position_key=pos_key if pos_key else None)
                    heur_res = analyze_video_heuristics(carrier_path)
                else:
                    sig_res = analyze_signature(carrier_path, position_key=pos_key if pos_key else None)
                    heur_res = analyze_heuristics(carrier_path)
            
            section_header("Analysis Results", "Forensic findings")
            
            # Signature Results
            if sig_res.get("detected"):
                render_panel(
                    f"Signature: DETECTED (StegX V{sig_res.get('version', 'Unknown')})",
                    f"Payload size: {sig_res.get('payload_size', 'Unknown')} bytes<br/>"
                    f"Encrypted: {sig_res.get('encrypted', True)}<br/>"
                    f"Original file: {sig_res.get('original_filename', 'Unknown')}",
                    "success"
                )
                st.warning("Cryptographic Authentication Status: UNVERIFIED. Detection does not imply the payload is intact or extractable without the correct password.")
            else:
                render_panel("Signature: NOT DETECTED", "No StegX header was found. If the payload was embedded with a position key, ensure you provided it.", "warning")
            
            # Heuristic Results
            st.write("")
            st.markdown("#### Heuristic Metrics")
            if is_video:
                st.write(f"- Frames analyzed: {heur_res.get('frames_analyzed', 0)}")
                st.write(f"- Suspicion Score: {heur_res.get('suspicion_score', 0)} / 100")
                st.write(f"- Verdict: {heur_res.get('verdict', 'Unknown')}")
            else:
                st.write(f"- Entropy: {heur_res.get('entropy', 0):.4f}")
                st.write(f"- Chi-Square P-Value: {heur_res.get('chi_square_p', 0):.4f}")
                st.write(f"- Suspicion Score: {heur_res.get('suspicion_score', 0)} / 100")
                st.write(f"- Verdict: {heur_res.get('verdict', 'Unknown')}")
                
            st.info("Heuristic analysis measures statistical anomalies in the LSB plane. It cannot definitively prove the presence of hidden data.")
