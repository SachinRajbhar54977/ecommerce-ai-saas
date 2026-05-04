# import os
# import streamlit as st

# def get_api_url():
#     return st.secrets.get("API_URL", os.getenv("API_URL", "http://127.0.0.1:8000"))

import os
import streamlit as st

def get_api_url():
    try:
        return st.secrets["API_URL"]
    except Exception:
        return os.getenv("API_URL", "http://127.0.0.1:8000")