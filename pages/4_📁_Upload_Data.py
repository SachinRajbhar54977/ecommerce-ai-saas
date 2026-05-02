import streamlit as st
import requests

from utils.auth_guard import require_login
from utils.style_loader import load_css

from utils.config import get_api_url

# -----------------------------
# AUTH + STYLES
# -----------------------------

require_login()

load_css("global.css")
load_css("ai_services.css")


API_URL = get_api_url()


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }


def get_upload_status():
    response = requests.get(
        f"{API_URL}/upload/status",
        headers=get_auth_headers()
    )

    if response.status_code == 200:
        return response.json()

    return None


def upload_csv_file(uploaded_file):
    files = {
        "file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")
    }

    response = requests.post(
        f"{API_URL}/upload/csv",
        files=files,
        headers=get_auth_headers()
    )

    return response


def show_data_status(status):
    st.markdown("### 📦 Data Readiness Status")

    files = status.get("files", {})

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Required Datasets")

        for file, exists in files.items():
            if exists:
                st.success(f"✔ {file}")
            else:
                st.warning(f"✖ {file} missing")

    with c2:
        st.markdown("#### System Readiness")

        if status.get("forecasting_ready"):
            st.success("📈 Forecasting is ready")
        else:
            st.info("Upload orders data to enable forecasting")

        if status.get("dashboard_ready"):
            st.success("🚀 Full dashboard is ready")
        else:
            st.info("Upload all required datasets for complete analytics")

    if status.get("forecasting_ready"):
        st.page_link(
            "pages/3_📈_Revenue_Forecasting.py",
            label="Go to Revenue Forecasting",
            icon="📈"
        )


# -----------------------------
# PAGE HEADER
# -----------------------------

st.markdown("""
<div class="ai-card">
    <h1>📁 Upload Data</h1>
    <p>Upload your business datasets to power analytics, forecasting, and AI services.</p>
</div>
""", unsafe_allow_html=True)


# -----------------------------
# CURRENT DATA STATUS
# -----------------------------

current_status = get_upload_status()

if current_status:
    show_data_status(current_status)

st.divider()


# -----------------------------
# FILE UPLOAD
# -----------------------------

st.markdown("### ⬆️ Upload New CSV")

st.info("""
Supported dataset types:
- customers data
- orders data
- monthly revenue data
- product summary data

The system will auto-detect the dataset type and save it correctly.
""")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)

if uploaded_file:
    st.write(f"Selected file: **{uploaded_file.name}**")

    if st.button("Upload File"):
        response = upload_csv_file(uploaded_file)

        if response.status_code == 200:
            upload_result = response.json()

            st.success("✅ File uploaded successfully")

            st.markdown(f"""
### Uploaded File Processed

- Dataset detected as: **{upload_result.get("dataset_type")}**
- Original filename: **{upload_result.get("original_filename")}**
- Saved as: **{upload_result.get("saved_as")}**
""")

            updated_status = get_upload_status()

            if updated_status:
                show_data_status(updated_status)

        else:
            try:
                error_message = response.json().get("detail", "Upload failed")
            except Exception:
                error_message = "Upload failed"

            st.error(f"❌ {error_message}")