import streamlit as st
from pathlib import Path

def load_css(file_name):
    css_path = Path("styles") / file_name

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found: {css_path}")