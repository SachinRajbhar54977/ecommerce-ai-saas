import streamlit as st

def require_login():
    if "token" not in st.session_state:
        st.warning("Please login first from the Login page.")
        st.stop()