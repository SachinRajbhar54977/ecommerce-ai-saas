import streamlit as st
import pandas as pd
import joblib
from utils.data_loader import load_data

from utils.style_loader import load_css

from utils.auth_guard import require_login

load_css("global.css")
load_css("ai_services.css")


require_login()

st.markdown("""
<div class="ai-card">
    <h1>🤖 AI Powered Services</h1>
    <p>
        Predict churn risk, identify high-risk customers, and generate action recommendations using machine learning.
    </p>
</div>
""", unsafe_allow_html=True)

customers, orders, revenue, products = load_data()

st.title("🤖 AI Powered Services")
st.markdown("Customer churn prediction and high-risk customer intelligence.")

model = joblib.load("churn_model.pkl")
label_encoders = joblib.load("label_encoders.pkl")
feature_names = joblib.load("feature_names.pkl")

# -----------------------------
# SINGLE CUSTOMER CHURN
# -----------------------------

st.subheader("🔮 Single Customer Churn Prediction")

selected_customer = st.selectbox(
    "Select Customer ID",
    customers["customer_id"].unique()
)

customer_data = customers[customers["customer_id"] == selected_customer].copy()

st.write("### Customer Snapshot")
st.dataframe(customer_data, use_container_width=True)

input_df = customer_data.copy()

drop_cols = ["customer_id", "registration_date"]
input_df = input_df.drop(columns=[col for col in drop_cols if col in input_df.columns])

for col in label_encoders:
    if col in input_df.columns:
        input_df[col] = label_encoders[col].transform(input_df[col])

input_df = input_df[feature_names]

if st.button("Analyze Churn Risk"):
    proba = model.predict_proba(input_df)[0][1]

    if proba < 0.3:
        risk = "LOW 🟢"
        recommendation = "No immediate action required."
    elif proba < 0.7:
        risk = "MEDIUM 🟡"
        recommendation = "Send engagement email or personalized offer."
    else:
        risk = "HIGH 🔴"
        recommendation = "Offer discount or retention campaign immediately."

    c1, c2 = st.columns(2)
    c1.metric("Churn Probability", f"{proba*100:.2f}%")
    c2.metric("Risk Level", risk)

    st.success(f"Recommended Action: {recommendation}")

st.divider()

# -----------------------------
# HIGH RISK CUSTOMER LIST
# -----------------------------

st.subheader("🚨 High Risk Customer List")

all_customers_input = customers.copy()

drop_cols = ["customer_id", "registration_date"]
all_customers_model_input = all_customers_input.drop(
    columns=[col for col in drop_cols if col in all_customers_input.columns]
)

for col in label_encoders:
    if col in all_customers_model_input.columns:
        all_customers_model_input[col] = label_encoders[col].transform(all_customers_model_input[col])

all_customers_model_input = all_customers_model_input[feature_names]

churn_probs = model.predict_proba(all_customers_model_input)[:, 1]

risk_df = customers.copy()
risk_df["churn_probability"] = churn_probs

def assign_risk(prob):
    if prob < 0.3:
        return "Low Risk"
    elif prob < 0.7:
        return "Medium Risk"
    else:
        return "High Risk"

risk_df["risk_level"] = risk_df["churn_probability"].apply(assign_risk)

r1, r2, r3 = st.columns(3)
r1.metric("High Risk", (risk_df["risk_level"] == "High Risk").sum())
r2.metric("Medium Risk", (risk_df["risk_level"] == "Medium Risk").sum())
r3.metric("Low Risk", (risk_df["risk_level"] == "Low Risk").sum())

risk_filter = st.selectbox(
    "Filter Risk Level",
    ["High Risk", "Medium Risk", "Low Risk", "All"]
)

if risk_filter != "All":
    display_df = risk_df[risk_df["risk_level"] == risk_filter]
else:
    display_df = risk_df

display_cols = [
    "customer_id",
    "age",
    "country",
    "membership_tier",
    "total_orders",
    "total_spend_usd",
    "days_since_last_purchase",
    "churn_probability",
    "risk_level"
]

display_cols = [col for col in display_cols if col in display_df.columns]

display_df = display_df[display_cols].sort_values(
    "churn_probability",
    ascending=False
)

st.dataframe(display_df.head(50), use_container_width=True)

csv = display_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Risk Customers",
    data=csv,
    file_name="risk_customers.csv",
    mime="text/csv"
)