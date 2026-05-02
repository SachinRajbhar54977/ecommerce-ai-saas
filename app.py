import streamlit as st

from utils.style_loader import load_css

import streamlit as st

import streamlit as st
from pathlib import Path

load_css("global.css")



if "token" in st.session_state:
    st.sidebar.success(f"Logged in: {st.session_state.get('user_email')}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
else:
    st.sidebar.warning("Not logged in")



user_dir = Path("backend/uploads") / st.session_state.get("user_email", "")

if user_dir.exists():
    st.sidebar.success("Using uploaded user data")
else:
    st.sidebar.info("Using demo default data")

st.set_page_config(
    page_title="E-commerce AI Platform",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 E-commerce AI & Analytics Platform")

st.markdown("""
## Welcome

This platform helps an e-commerce business understand performance, reduce churn, and make smarter decisions using analytics and AI.

### 📊 Analytical Dashboard
Use this section for:
- Executive KPIs
- Revenue analytics
- Customer analytics
- Product analytics
- Operations analytics

### 🤖 AI Powered Services
Use this section for:
- Customer churn prediction
- High-risk customer detection
- AI-driven recommendations
- Future revenue forecasting

### 🛍️ Product Intelligence
Use this section for:
- Top products
- High-return products
- Category performance
- Product quality insights

### 📈 Revenue Forecasting
Use this section for:
- Monthly revenue forecasting
- Growth planning
- Inventory and budget decisions
""")

st.info("Use the sidebar to open different service pages.")