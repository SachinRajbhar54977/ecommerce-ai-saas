import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"


def get_auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }


def list_uploaded_files():
    response = requests.get(
        f"{API_URL}/upload/files",
        headers=get_auth_headers()
    )

    if response.status_code == 200:
        return response.json().get("files", [])

    return []