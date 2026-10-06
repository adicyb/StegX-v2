"""
StegX Web Console Configuration and Theming.
"""
import streamlit as st

def apply_theme():
    """Apply the custom StegX V2 dark-first cybersecurity theme."""
    st.set_page_config(
        page_title="StegX V2 Console",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
            /* Base Theme - Dark First */
            .stApp {
                background-color: #0B0E14;
                color: #ECEFF4;
                font-family: 'Inter', -apple-system, sans-serif;
            }
            
            /* Sidebar Styling */
            [data-testid="stSidebar"] {
                background-color: #11151C;
                border-right: 1px solid #1E2532;
            }
            
            /* Hide Streamlit Branding */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {background-color: transparent !important;}
            
            /* Cybersecurity Accent Colors */
            :root {
                --stegx-cyan: #00E5A0;
                --stegx-blue: #4B7BFF;
                --stegx-red: #FF3B5C;
                --stegx-dark: #151A22;
                --stegx-darker: #0E1219;
                --stegx-border: #232A38;
                --stegx-text-muted: #8C9BAB;
            }
            
            /* Custom Cards and Panels */
            .stegx-card {
                background-color: var(--stegx-dark);
                border: 1px solid var(--stegx-border);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            }
            
            .stegx-panel {
                background-color: var(--stegx-darker);
                border-left: 4px solid var(--stegx-cyan);
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 0 8px 8px 0;
            }
            
            /* Status Badges */
            .badge {
                padding: 0.3rem 0.8rem;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                display: inline-block;
            }
            .badge-success { background: rgba(0, 229, 160, 0.1); color: var(--stegx-cyan); border: 1px solid rgba(0, 229, 160, 0.2); }
            .badge-warning { background: rgba(255, 184, 108, 0.1); color: #FFB86C; border: 1px solid rgba(255, 184, 108, 0.2); }
            .badge-error { background: rgba(255, 59, 92, 0.1); color: var(--stegx-red); border: 1px solid rgba(255, 59, 92, 0.2); }
            .badge-info { background: rgba(75, 123, 255, 0.1); color: var(--stegx-blue); border: 1px solid rgba(75, 123, 255, 0.2); }
            
            /* Typography */
            h1, h2, h3, h4, h5, h6 {
                color: #FFFFFF !important;
                font-weight: 600 !important;
                letter-spacing: -0.5px;
            }
            
            .text-muted {
                color: var(--stegx-text-muted);
            }
            
            hr {
                border-color: var(--stegx-border);
                margin: 2rem 0;
            }
            
            /* Streamlit overrides */
            .stButton > button {
                background-color: var(--stegx-blue);
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                padding: 0.5rem 1rem;
                transition: all 0.2s ease;
            }
            .stButton > button:hover {
                background-color: #3A63D9;
                color: white;
                transform: translateY(-1px);
            }
            
            /* Metric overrides */
            [data-testid="stMetricValue"] {
                color: var(--stegx-cyan) !important;
            }
        </style>
    """, unsafe_allow_html=True)
