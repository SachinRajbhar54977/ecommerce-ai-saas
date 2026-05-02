import streamlit as st
import requests

from utils.style_loader import load_css

from utils.config import get_api_url

load_css("global.css")
load_css("ai_services.css")



API_URL = get_api_url()

st.markdown("""
<div class="ai-card">
    <h1>🔐 Login</h1>
    <p>Login to access the E-commerce AI Analytics SaaS platform.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Login", "Signup"])

with tab1:
    st.subheader("Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        response = requests.post(
            f"{API_URL}/login",
            data={
                "username": email,
                "password": password
            }
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state["token"] = token
            st.session_state["user_email"] = email
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password")

with tab2:
    st.subheader("Create Account")

    signup_email = st.text_input("Email", key="signup_email")
    signup_password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Create Account"):
        response = requests.post(
            f"{API_URL}/signup",
            params={
                "email": signup_email,
                "password": signup_password
            }
        )

        if response.status_code == 200:
            st.success("Account created successfully. Now login.")
        else:
            st.error(response.json().get("detail", "Signup failed"))

if "token" in st.session_state:
    st.success(f"Logged in as {st.session_state.get('user_email')}")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()