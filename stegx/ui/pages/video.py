import os
import tempfile
import streamlit as st
from stegx.ui.components import page_header, section_header, render_panel
from stegx.video.analyze import get_video_info
from stegx.video.capacity import get_video_capacity
from stegx.video.codec_test import check_video_codec
from stegx.core.format_handler import get_file_extension, VIDEO_FORMATS

page_header("Video Streaming Engine", "O(1) memory video processing, capability checks, and metadata inspection.", "FFV1", "info")

section_header("Video Inspector", "Upload a video to analyze its capacity and codec properties.")
video_file = st.file_uploader("Upload Video", type=["avi", "mkv", "mp4", "mov"])

if video_file:
    ext = get_file_extension(video_file.name)
    if ext not in VIDEO_FORMATS:
        render_panel("Unsupported Format", "Only AVI, MKV, MP4, and MOV containers are supported for inspection.", "error")
    else:
        with tempfile.TemporaryDirectory() as td:
            video_path = os.path.join(td, video_file.name)
            with open(video_path, "wb") as f:
                f.write(video_file.getbuffer())
                
            st.write("")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Metadata")
                info = get_video_info(video_path)
                st.write(f"- Resolution: {info.get('width')}x{info.get('height')}")
                st.write(f"- FPS: {info.get('fps')}")
                st.write(f"- Frame Count: {info.get('frame_count')}")
            
            with col2:
                st.markdown("#### Steganographic Capacity")
                cap_bits = get_video_capacity(video_path)["available_bits"]
                cap_bytes = cap_bits // 8
                st.write(f"- Theoretical bits: {cap_bits:,}")
                st.write(f"- Theoretical bytes: {cap_bytes:,}")
                st.write(f"- Safe payload size: ~{max(0, cap_bytes - 1024):,} bytes")
            
            st.write("")
            section_header("Codec Diagnostics", "Verify lossless pipeline support.")
            st.info("Video embedding requires the FFV1 lossless codec to prevent compression from destroying the LSB payload.")
            
            if st.button("🔧 TEST FFV1 CODEC", use_container_width=True):
                with st.spinner("Testing codec..."):
                    out_test = os.path.join(td, "test.avi")
                    res = check_video_codec(video_path, out_test, "FFV1")
                    success = res.get("file_exists") and res.get("file_size", 0) > 0
                    if success:
                        render_panel("Codec Test Passed", "FFV1 lossless encoding is supported by the system's OpenCV backend.", "success")
                    else:
                        render_panel("Codec Test Failed", "The system's OpenCV backend failed to write FFV1 frames. Video embedding will not work correctly.", "error")
