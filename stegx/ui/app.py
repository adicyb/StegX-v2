"""
StegX Web Console Entry Point.
"""
import streamlit as st
import importlib.metadata
from stegx.ui.theme import apply_theme

# Apply theme globally before any other rendering
apply_theme()

try:
    __version__ = importlib.metadata.version("stegx")
except importlib.metadata.PackageNotFoundError:
    __version__ = "2.1.0-dev"

# Sidebar Branding
st.sidebar.markdown(f"""
    <div style='text-align: center; padding-bottom: 20px;'>
        <h1 style='margin-bottom: 0;'>STEGX</h1>
        <p style='color: #00E5A0; font-family: monospace; letter-spacing: 1px; margin-top: -5px;'>V2 SECURE PROTOCOL</p>
        <p style='color: #8C9BAB; font-size: 0.8rem;'>v{__version__}</p>
    </div>
""", unsafe_allow_html=True)

# Define multipage navigation using standard st.navigation (Streamlit 1.36+)
pages = {
    "Overview": [
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
        st.Page("pages/settings.py", title="Settings", icon="⚙️")
    ],
    "Operations": [
        st.Page("pages/embed.py", title="Embed", icon="🔒"),
        st.Page("pages/extract.py", title="Extract", icon="🔓"),
        st.Page("pages/analyze.py", title="Analyze", icon="🔬")
    ],
    "Advanced": [
        st.Page("pages/payload.py", title="Payload Builder", icon="📦"),
        st.Page("pages/video.py", title="Video Streaming", icon="🎞️")
    ]
}

pg = st.navigation(pages)
pg.run()
