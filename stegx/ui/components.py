"""
Reusable UI components for StegX Streamlit Web Console.
"""
import streamlit as st

def render_card(title: str, content: str, icon: str = ""):
    """Renders a styled card with title and content."""
    html = f"""
    <div class="stegx-card">
        <h4 style="margin-top:0; margin-bottom: 0.5rem; color: #8C9BAB !important;">{icon} {title}</h4>
        <div style="font-size: 1.1rem; font-weight: 500; color: #ECEFF4;">{content}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_status_badge(text: str, status: str = "info"):
    """Renders a status badge."""
    valid_statuses = ["success", "warning", "error", "info"]
    safe_status = status if status in valid_statuses else "info"
    
    html = f'<span class="badge badge-{safe_status}">{text}</span>'
    st.markdown(html, unsafe_allow_html=True)

def section_header(title: str, subtitle: str = ""):
    """Renders a section header."""
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"<p class='text-muted' style='margin-top: -10px;'>{subtitle}</p>", unsafe_allow_html=True)
    st.divider()

def page_header(title: str, description: str, badge_text: str = "STG2 READY", badge_type: str = "success"):
    """Renders the top hero section of a page."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(title)
        st.markdown(f"<p style='font-size: 1.1rem; color: #8C9BAB;'>{description}</p>", unsafe_allow_html=True)
    with col2:
        st.write("")
        st.write("")
        render_status_badge(badge_text, badge_type)
    st.markdown("<hr style='margin-top: 1rem; margin-bottom: 2rem;'/>", unsafe_allow_html=True)

def render_panel(title: str, message: str, type: str = "info"):
    """Renders an elevated side panel."""
    color_map = {
        "info": "var(--stegx-blue)",
        "success": "var(--stegx-cyan)",
        "warning": "#FFB86C",
        "error": "var(--stegx-red)"
    }
    color = color_map.get(type, color_map["info"])
    html = f"""
    <div class="stegx-panel" style="border-left-color: {color};">
        <strong style="color: {color};">{title}</strong><br/>
        <span style="color: #ECEFF4;">{message}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def capacity_meter(available: int, required: int):
    """Renders a capacity utilization meter."""
    if available <= 0:
        pct = 100
        color = "var(--stegx-red)"
    else:
        pct = min(100, (required / available) * 100)
        color = "var(--stegx-cyan)" if pct <= 80 else ("#FFB86C" if pct <= 95 else "var(--stegx-red)")
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span class="text-muted">Capacity Utilization</span>
            <span style="color: {color}; font-weight: 600;">{pct:.1f}%</span>
        </div>
        <div style="width: 100%; background-color: var(--stegx-dark); border-radius: 4px; height: 8px; overflow: hidden;">
            <div style="width: {pct}%; background-color: {color}; height: 100%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 0.8rem;" class="text-muted">
            <span>{required:,} bytes required</span>
            <span>{available:,} bytes available</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
