# app.py
# Premium AI-Powered E-commerce Executive Dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="AI E-commerce Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #111827, #1f2937);
    border: 1px solid #334155;
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
}
div[data-testid="metric-container"] label {
    color: #d1d5db !important;
}
div[data-testid="metric-container"] div {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] {
    background-color: #0f172a;
}
.small-note {
    color: #94a3b8;
    font-size: 0.9rem;
}
.insight-box {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
DATA_DIR = Path(".")

@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    revenue = pd.read_csv(DATA_DIR / "monthly_revenue.csv")
    products = pd.read_csv(DATA_DIR / "product_summary.csv")

    customers.columns = customers.columns.str.strip()
    orders.columns = orders.columns.str.strip()
    revenue.columns = revenue.columns.str.strip()
    products.columns = products.columns.str.strip()

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    if "delivery_date" in orders.columns:
        orders["delivery_date"] = pd.to_datetime(orders["delivery_date"], errors="coerce")

    if "registration_date" in customers.columns:
        customers["registration_date"] = pd.to_datetime(customers["registration_date"], errors="coerce")

    if {"year", "month"}.issubset(revenue.columns):
        revenue["date"] = pd.to_datetime(
            revenue["year"].astype(str) + "-" + revenue["month"].astype(str) + "-01",
            errors="coerce"
        )

    return customers, orders, revenue, products

customers, orders, revenue, products = load_data()

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def safe_mean(series):
    return series.mean() if len(series) else 0


def pct_change(current, previous):
    if previous == 0 or pd.isna(previous):
        return None
    return ((current - previous) / previous) * 100


def format_delta(value):
    if value is None:
        return None
    return f"{value:.2f}%"


def make_download_button(df, filename):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered Data",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("📊 AI-Powered E-commerce Executive Dashboard")
st.markdown(
    "A client-ready analytics dashboard for revenue growth, customer retention, product performance, and operational decisions."
)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.title("🎯 Smart Business Filters")
st.sidebar.caption("Use filters to investigate revenue, customers, products, and operations.")

min_date = orders["order_date"].min().date()
max_date = orders["order_date"].max().date()

selected_date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date, end_date = min_date, max_date

selected_years = st.sidebar.multiselect(
    "Year",
    sorted(orders["year"].dropna().unique()),
    default=sorted(orders["year"].dropna().unique())
)

selected_months = st.sidebar.multiselect(
    "Month",
    sorted(orders["month"].dropna().unique()),
    default=sorted(orders["month"].dropna().unique())
)

selected_categories = st.sidebar.multiselect(
    "Category",
    sorted(orders["category"].dropna().unique()),
    default=sorted(orders["category"].dropna().unique())
)

selected_devices = st.sidebar.multiselect(
    "Device Used",
    sorted(orders["device_used"].dropna().unique()),
    default=sorted(orders["device_used"].dropna().unique())
)

selected_payments = st.sidebar.multiselect(
    "Payment Method",
    sorted(orders["payment_method"].dropna().unique()),
    default=sorted(orders["payment_method"].dropna().unique())
)

selected_status = st.sidebar.multiselect(
    "Order Status",
    sorted(orders["order_status"].dropna().unique()),
    default=sorted(orders["order_status"].dropna().unique())
)

order_value_min = float(orders["total_amount_usd"].min())
order_value_max = float(orders["total_amount_usd"].max())

selected_order_value = st.sidebar.slider(
    "Order Value Range ($)",
    min_value=order_value_min,
    max_value=order_value_max,
    value=(order_value_min, order_value_max)
)

top_n = st.sidebar.slider("Top N Records", 5, 30, 10)

show_raw_data = st.sidebar.toggle("Show Raw Filtered Data", value=False)

# --------------------------------------------------
# FILTER DATA
# --------------------------------------------------
filtered_orders = orders[
    (orders["order_date"].dt.date >= start_date) &
    (orders["order_date"].dt.date <= end_date) &
    (orders["year"].isin(selected_years)) &
    (orders["month"].isin(selected_months)) &
    (orders["category"].isin(selected_categories)) &
    (orders["device_used"].isin(selected_devices)) &
    (orders["payment_method"].isin(selected_payments)) &
    (orders["order_status"].isin(selected_status)) &
    (orders["total_amount_usd"] >= selected_order_value[0]) &
    (orders["total_amount_usd"] <= selected_order_value[1])
].copy()

filtered_revenue = revenue[
    (revenue["date"].dt.date >= start_date) &
    (revenue["date"].dt.date <= end_date) &
    (revenue["year"].isin(selected_years))
].copy()

if filtered_orders.empty:
    st.error("No records found for the selected filters. Please adjust filters from the sidebar.")
    st.stop()

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
total_revenue = filtered_orders["total_amount_usd"].sum()
total_orders = filtered_orders["order_id"].nunique()
aov = total_revenue / total_orders if total_orders else 0
unique_customers = filtered_orders["customer_id"].nunique()
return_rate = safe_mean(filtered_orders["returned"]) * 100
cancel_rate = (filtered_orders["order_status"].eq("Cancelled").mean()) * 100
repeat_customer_rate = safe_mean(filtered_orders["is_repeat_customer"]) * 100
churn_rate = safe_mean(customers["churned"]) * 100
avg_discount = filtered_orders["discount_amount_usd"].mean() if "discount_amount_usd" in filtered_orders else 0

# Previous period comparison
period_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
previous_end = pd.to_datetime(start_date) - pd.Timedelta(days=1)
previous_start = previous_end - pd.Timedelta(days=period_days - 1)

previous_orders = orders[
    (orders["order_date"] >= previous_start) &
    (orders["order_date"] <= previous_end) &
    (orders["category"].isin(selected_categories)) &
    (orders["device_used"].isin(selected_devices)) &
    (orders["payment_method"].isin(selected_payments)) &
    (orders["order_status"].isin(selected_status))
]

prev_revenue = previous_orders["total_amount_usd"].sum()
prev_orders_count = previous_orders["order_id"].nunique()
prev_aov = prev_revenue / prev_orders_count if prev_orders_count else 0

revenue_delta = pct_change(total_revenue, prev_revenue)
orders_delta = pct_change(total_orders, prev_orders_count)
aov_delta = pct_change(aov, prev_aov)

# --------------------------------------------------
# SIDEBAR SNAPSHOT
# --------------------------------------------------
st.sidebar.divider()
st.sidebar.subheader("📌 Filtered Snapshot")
st.sidebar.metric("Revenue", f"${total_revenue:,.0f}")
st.sidebar.metric("Orders", f"{total_orders:,}")
st.sidebar.metric("Customers", f"{unique_customers:,}")
st.sidebar.metric("AOV", f"${aov:,.2f}")
make_download_button(filtered_orders, "filtered_orders.csv")

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------
st.subheader("🚀 Executive KPI Summary")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Revenue", f"${total_revenue:,.0f}", format_delta(revenue_delta))
k2.metric("Orders", f"{total_orders:,}", format_delta(orders_delta))
k3.metric("AOV", f"${aov:,.2f}", format_delta(aov_delta))
k4.metric("Customers", f"{unique_customers:,}")
k5.metric("Return Rate", f"{return_rate:.2f}%")
k6.metric("Churn Rate", f"{churn_rate:.2f}%")

st.caption(f"Comparison is against previous matching period: {previous_start.date()} to {previous_end.date()}.")
st.divider()

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Revenue",
    "👥 Customers",
    "🛍️ Products",
    "🚚 Operations",
    "⚠️ Risk Center",
    "💡 Executive Insights"
])

# --------------------------------------------------
# REVENUE TAB
# --------------------------------------------------
with tab1:
    st.subheader("Revenue Performance")

    col1, col2 = st.columns(2)

    with col1:
        monthly = (
            filtered_orders
            .groupby(pd.Grouper(key="order_date", freq="M"))["total_amount_usd"]
            .sum()
            .reset_index()
        )
        fig = px.line(
            monthly,
            x="order_date",
            y="total_amount_usd",
            markers=True,
            title="Monthly Revenue Trend"
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        yearly = filtered_orders.groupby("year")["total_amount_usd"].sum().reset_index()
        fig = px.bar(
            yearly,
            x="year",
            y="total_amount_usd",
            title="Yearly Revenue"
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        category_revenue = (
            filtered_orders.groupby("category")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(
            category_revenue,
            x="category",
            y="total_amount_usd",
            title=f"Top {top_n} Categories by Revenue"
        )
        fig.update_layout(xaxis_tickangle=-35, height=430)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        device_revenue = filtered_orders.groupby("device_used")["total_amount_usd"].sum().reset_index()
        fig = px.pie(
            device_revenue,
            names="device_used",
            values="total_amount_usd",
            title="Revenue by Device"
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# CUSTOMERS TAB
# --------------------------------------------------
with tab2:
    st.subheader("Customer Intelligence")

    joined = filtered_orders.merge(
        customers,
        on="customer_id",
        how="left",
        suffixes=("_order", "_customer")
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Buying Customers", f"{unique_customers:,}")
    c2.metric("Repeat Customer Rate", f"{repeat_customer_rate:.2f}%")
    c3.metric("Newsletter Subscribed", f"{safe_mean(customers['newsletter_subscribed']) * 100:.2f}%")
    c4.metric("Avg Customer Spend", f"${customers['total_spend_usd'].mean():,.2f}")

    col1, col2 = st.columns(2)

    with col1:
        churn_split = customers["churned"].value_counts().reset_index()
        churn_split.columns = ["churned", "customers"]
        fig = px.pie(churn_split, names="churned", values="customers", title="Churned vs Active Customers")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        tier_revenue = (
            joined.groupby("membership_tier")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig = px.bar(tier_revenue, x="membership_tier", y="total_amount_usd", title="Revenue by Membership Tier")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        country_revenue = (
            joined.groupby("country")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(country_revenue, x="country", y="total_amount_usd", title=f"Top {top_n} Countries by Revenue")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        acquisition_revenue = (
            joined.groupby("acquisition_channel")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig = px.bar(acquisition_revenue, x="acquisition_channel", y="total_amount_usd", title="Revenue by Acquisition Channel")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)
    # ==============================
# 🔮 CHURN INTELLIGENCE
# ==============================

import joblib

st.divider()
st.subheader("🔮 Customer Churn Intelligence")

# Load model
model = joblib.load("churn_model.pkl")
label_encoders = joblib.load("label_encoders.pkl")
feature_names = joblib.load("feature_names.pkl")

# Select customer
selected_customer = st.selectbox(
    "Select Customer ID",
    customers["customer_id"].unique()
)

customer_data = customers[customers["customer_id"] == selected_customer].copy()

# Show customer snapshot
st.write("### Customer Snapshot")
st.dataframe(customer_data, use_container_width=True)

# Prepare data
input_df = customer_data.copy()

# Drop unused columns
drop_cols = ["customer_id", "registration_date"]
input_df = input_df.drop(columns=[col for col in drop_cols if col in input_df.columns])

# Encode categorical
for col in label_encoders:
    if col in input_df.columns:
        input_df[col] = label_encoders[col].transform(input_df[col])

# Ensure order
input_df = input_df[feature_names]

# Predict
if st.button("Analyze Churn Risk"):

    proba = model.predict_proba(input_df)[0][1]

    # Risk logic
    if proba < 0.3:
        risk = "LOW 🟢"
        color = "green"
        recommendation = "Customer is safe"
    elif proba < 0.7:
        risk = "MEDIUM 🟡"
        color = "orange"
        recommendation = "Send engagement email"
    else:
        risk = "HIGH 🔴"
        color = "red"
        recommendation = "Offer discount immediately"

    st.markdown(f"## Risk Level: :{color}[{risk}]")
    st.metric("Churn Probability", f"{proba*100:.2f}%")

    st.success(f"Recommendation: {recommendation}")   


# ==============================
# 🚨 HIGH RISK CUSTOMER LIST
# ==============================

st.divider()
st.subheader("🚨 High Risk Customer List")

# Prepare all customers for prediction
all_customers_input = customers.copy()

customer_ids = all_customers_input["customer_id"]

drop_cols = ["customer_id", "registration_date"]
all_customers_input = all_customers_input.drop(
    columns=[col for col in drop_cols if col in all_customers_input.columns]
)

# Encode categorical columns
for col in label_encoders:
    if col in all_customers_input.columns:
        all_customers_input[col] = label_encoders[col].transform(all_customers_input[col])

# Keep same feature order
all_customers_input = all_customers_input[feature_names]

# Predict probabilities
churn_probs = model.predict_proba(all_customers_input)[:, 1]

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

# Filter option
risk_filter = st.selectbox(
    "Filter Customers by Risk",
    ["High Risk", "Medium Risk", "Low Risk", "All"]
)

if risk_filter != "All":
    filtered_risk_df = risk_df[risk_df["risk_level"] == risk_filter]
else:
    filtered_risk_df = risk_df

# Show top risky customers
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

display_cols = [col for col in display_cols if col in filtered_risk_df.columns]

top_risk_customers = (
    filtered_risk_df[display_cols]
    .sort_values("churn_probability", ascending=False)
    .head(20)
)

st.dataframe(top_risk_customers, use_container_width=True)

# KPI summary
high_risk_count = (risk_df["risk_level"] == "High Risk").sum()
medium_risk_count = (risk_df["risk_level"] == "Medium Risk").sum()
low_risk_count = (risk_df["risk_level"] == "Low Risk").sum()

r1, r2, r3 = st.columns(3)

r1.metric("High Risk Customers", high_risk_count)
r2.metric("Medium Risk Customers", medium_risk_count)
r3.metric("Low Risk Customers", low_risk_count)

# Download high risk customers
high_risk_download = risk_df[risk_df["risk_level"] == "High Risk"]

csv = high_risk_download.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download High Risk Customers",
    data=csv,
    file_name="high_risk_customers.csv",
    mime="text/csv"
)     

# --------------------------------------------------
# PRODUCTS TAB
# --------------------------------------------------
with tab3:
    st.subheader("Product Performance Intelligence")

    p1, p2 = st.columns(2)

    with p1:
        top_products = (
            filtered_orders.groupby("product_name")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(top_products, x="product_name", y="total_amount_usd", title=f"Top {top_n} Products by Revenue")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    with p2:
        product_orders = (
            filtered_orders.groupby("product_name")["order_id"]
            .nunique()
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(product_orders, x="product_name", y="order_id", title=f"Top {top_n} Products by Order Volume")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    p3, p4 = st.columns(2)

    with p3:
        high_return = products.sort_values("return_rate", ascending=False).head(top_n)
        fig = px.bar(high_return, x="product_name", y="return_rate", color="category", title=f"Top {top_n} High Return Products")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    with p4:
        top_rated = products.sort_values("avg_rating", ascending=False).head(top_n)
        fig = px.bar(top_rated, x="product_name", y="avg_rating", color="category", title=f"Top {top_n} Rated Products")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# OPERATIONS TAB
# --------------------------------------------------
with tab4:
    st.subheader("Operations & Fulfillment")

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Return Rate", f"{return_rate:.2f}%")
    o2.metric("Cancel Rate", f"{cancel_rate:.2f}%")
    o3.metric("Avg Delivery Days", f"{filtered_orders['delivery_days'].mean():.2f}")
    o4.metric("Avg Discount", f"${avg_discount:.2f}")

    col1, col2 = st.columns(2)

    with col1:
        status = filtered_orders["order_status"].value_counts().reset_index()
        status.columns = ["status", "count"]
        fig = px.pie(status, names="status", values="count", title="Order Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        delivery = (
            filtered_orders.groupby("category")["delivery_days"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(delivery, x="category", y="delivery_days", title=f"Top {top_n} Slowest Categories by Delivery Days")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    discount_category = (
        filtered_orders.groupby("category")[["discount_amount_usd", "total_amount_usd"]]
        .sum()
        .sort_values("discount_amount_usd", ascending=False)
        .reset_index()
        .head(top_n)
    )
    fig = px.bar(
        discount_category,
        x="category",
        y=["discount_amount_usd", "total_amount_usd"],
        title="Discount Spend vs Revenue by Category",
        barmode="group"
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# RISK CENTER TAB
# --------------------------------------------------
with tab5:
    st.subheader("Risk Center")

    r1, r2 = st.columns(2)

    with r1:
        return_by_category = (
            filtered_orders.groupby("category")["returned"]
            .mean()
            .mul(100)
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(return_by_category, x="category", y="returned", title=f"Top {top_n} Categories by Return Rate")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    with r2:
        cancel_by_category = (
            filtered_orders.assign(cancelled=filtered_orders["order_status"].eq("Cancelled"))
            .groupby("category")["cancelled"]
            .mean()
            .mul(100)
            .sort_values(ascending=False)
            .reset_index()
            .head(top_n)
        )
        fig = px.bar(cancel_by_category, x="category", y="cancelled", title=f"Top {top_n} Categories by Cancel Rate")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### High Risk Products")
    high_risk_products = products.sort_values(["return_rate", "total_revenue_usd"], ascending=[False, False]).head(top_n)
    st.dataframe(high_risk_products, use_container_width=True)

# --------------------------------------------------
# EXECUTIVE INSIGHTS TAB
# --------------------------------------------------
with tab6:
    st.subheader("Executive Insights & Recommendations")

    best_category = filtered_orders.groupby("category")["total_amount_usd"].sum().idxmax()
    best_product = filtered_orders.groupby("product_name")["total_amount_usd"].sum().idxmax()
    worst_return_category = filtered_orders.groupby("category")["returned"].mean().idxmax()
    highest_device = filtered_orders.groupby("device_used")["total_amount_usd"].sum().idxmax()

    st.markdown(f"""
<div class="insight-box">
<h3>Executive Summary</h3>
<p>The filtered business segment generated <b>${total_revenue:,.2f}</b> from <b>{total_orders:,}</b> orders and <b>{unique_customers:,}</b> customers.</p>
</div>

<div class="insight-box">
<h3>Key Business Findings</h3>
<ul>
<li><b>{best_category}</b> is the strongest revenue category.</li>
<li><b>{best_product}</b> is the highest revenue product.</li>
<li><b>{highest_device}</b> contributes the highest revenue by device.</li>
<li><b>{worst_return_category}</b> has the highest return risk among categories.</li>
<li>Current return rate is <b>{return_rate:.2f}%</b> and cancel rate is <b>{cancel_rate:.2f}%</b>.</li>
</ul>
</div>

<div class="insight-box">
<h3>Recommended Business Actions</h3>
<ol>
<li>Increase marketing investment in <b>{best_category}</b>.</li>
<li>Investigate product quality and descriptions in <b>{worst_return_category}</b>.</li>
<li>Launch personalized retention offers for inactive and low-order customers.</li>
<li>Build a churn prediction model to prioritize high-risk customers.</li>
<li>Use revenue forecasting to plan inventory and campaign budgets.</li>
<li>Build a recommendation system to increase average order value.</li>
</ol>
</div>

<div class="insight-box">
<h3>Next AI Modules</h3>
<ul>
<li>Customer Churn Prediction</li>
<li>Revenue Forecasting</li>
<li>Customer Segmentation</li>
<li>Product Recommendation Engine</li>
<li>Return Risk Prediction</li>
</ul>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# RAW DATA VIEW
# --------------------------------------------------
if show_raw_data:
    st.divider()
    st.subheader("Raw Filtered Orders Data")
    st.dataframe(filtered_orders, use_container_width=True)

