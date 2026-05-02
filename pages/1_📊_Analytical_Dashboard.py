import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import load_data
from utils.style_loader import load_css

from utils.auth_guard import require_login


load_css("global.css")
load_css("analytics.css")


require_login()
from pathlib import Path
import streamlit as st

st.markdown('<div class="section-heading">📦 Data Status</div>', unsafe_allow_html=True)

user_email = st.session_state.get("user_email")
user_dir = Path("backend/uploads") / user_email

required_files = [
    "customers.csv",
    "orders.csv",
    "monthly_revenue.csv",
    "product_summary.csv"
]

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Uploaded Datasets")

    for file in required_files:
        if (user_dir / file).exists():
            st.success(f"✔ {file}")
        else:
            st.warning(f"✖ {file} missing")

with col2:
    st.markdown("### System Status")

    if user_dir.exists():
        st.info("Using uploaded user data")
    else:
        st.info("Using default demo data")
        

customers, orders, revenue, products = load_data()
st.markdown("""
<div class="insight-card">
    <h1>📊 Analytical Dashboard</h1>
    <p class="dashboard-subtitle">
        Executive-grade analytics for revenue growth, customer retention, product performance, and operations.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<p class="dashboard-subtitle">A client-ready analytics dashboard for revenue growth, customer retention, product performance, and operational decisions.</p>',
    unsafe_allow_html=True
)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
# -----------------------------
# ADVANCED SIDEBAR FILTERS
# -----------------------------

st.sidebar.header("🎯 Smart Business Filters")

# Date range filter
min_date = orders["order_date"].min().date()
max_date = orders["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Year filter
selected_years = st.sidebar.multiselect(
    "Select Year",
    sorted(orders["year"].dropna().unique()),
    default=sorted(orders["year"].dropna().unique())
)

# Month filter
selected_months = st.sidebar.multiselect(
    "Select Month",
    sorted(orders["month"].dropna().unique()),
    default=sorted(orders["month"].dropna().unique())
)

# Category filter
selected_categories = st.sidebar.multiselect(
    "Select Category",
    sorted(orders["category"].dropna().unique()),
    default=sorted(orders["category"].dropna().unique())
)

# Device filter
selected_devices = st.sidebar.multiselect(
    "Select Device",
    sorted(orders["device_used"].dropna().unique()),
    default=sorted(orders["device_used"].dropna().unique())
)

# Payment method filter
selected_payments = st.sidebar.multiselect(
    "Payment Method",
    sorted(orders["payment_method"].dropna().unique()),
    default=sorted(orders["payment_method"].dropna().unique())
)

# Order status filter
selected_status = st.sidebar.multiselect(
    "Order Status",
    sorted(orders["order_status"].dropna().unique()),
    default=sorted(orders["order_status"].dropna().unique())
)

# Order value filter
min_order_value = float(orders["total_amount_usd"].min())
max_order_value = float(orders["total_amount_usd"].max())

selected_order_value = st.sidebar.slider(
    "Order Value Range ($)",
    min_value=min_order_value,
    max_value=max_order_value,
    value=(min_order_value, max_order_value)
)

# Top N filter
top_n = st.sidebar.slider(
    "Top N Results",
    min_value=5,
    max_value=30,
    value=10
)

# -----------------------------
# APPLY FILTERS
# -----------------------------

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
]

if filtered_orders.empty:
    st.warning("No data found for selected filters. Please change filter values.")
    st.stop()

# -----------------------------
# SIDEBAR KPI SNAPSHOT
# -----------------------------

sidebar_revenue = filtered_orders["total_amount_usd"].sum()
sidebar_orders = filtered_orders["order_id"].nunique()
sidebar_customers = filtered_orders["customer_id"].nunique()
sidebar_aov = sidebar_revenue / sidebar_orders if sidebar_orders else 0

st.sidebar.divider()
st.sidebar.subheader("📌 Filtered Snapshot")
st.sidebar.metric("Revenue", f"${sidebar_revenue:,.0f}")
st.sidebar.metric("Orders", f"{sidebar_orders:,}")
st.sidebar.metric("Customers", f"{sidebar_customers:,}")
st.sidebar.metric("AOV", f"${sidebar_aov:,.2f}")

if filtered_orders.empty:
    st.warning("No data found for selected filters. Please change filter values.")
    st.stop()

# -----------------------------
# DOWNLOAD BUTTON
# -----------------------------

st.download_button(
    label="⬇️ Download Filtered Data",
    data=filtered_orders.to_csv(index=False).encode("utf-8"),
    file_name="filtered_orders.csv",
    mime="text/csv"
)

# -----------------------------
# KPI SECTION
# -----------------------------

st.markdown(
    '<div class="section-heading">🚀 Executive KPI Summary</div>',
    unsafe_allow_html=True
)

total_revenue = filtered_orders["total_amount_usd"].sum()
total_orders = filtered_orders["order_id"].nunique()
aov = total_revenue / total_orders if total_orders else 0
return_rate = filtered_orders["returned"].mean() * 100 if total_orders else 0
churn_rate = customers["churned"].mean() * 100 if "churned" in customers.columns else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Revenue", f"${total_revenue:,.0f}")
k2.metric("Orders", f"{total_orders:,}")
k3.metric("AOV", f"${aov:,.2f}")
k4.metric("Return Rate", f"{return_rate:.2f}%")
k5.metric("Churn Rate", f"{churn_rate:.2f}%")

st.divider()

# -----------------------------
# TABS
# -----------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Revenue",
    "👥 Customers",
    "🛍️ Products",
    "🚚 Operations",
    "⚠️ Risk Center",
    "💡 Executive Insights"
])

# -----------------------------
# REVENUE TAB
# -----------------------------

with tab1:
    st.markdown(
        '<div class="section-heading">Revenue Performance</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        monthly = (
            filtered_orders
            .groupby(pd.Grouper(key="order_date", freq="ME"))["total_amount_usd"]
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
        st.plotly_chart(fig, width="stretch", key="monthly_revenue_chart")

    with col2:
        yearly = (
            filtered_orders.groupby("year")["total_amount_usd"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            yearly,
            x="year",
            y="total_amount_usd",
            title="Yearly Revenue"
        )
        st.plotly_chart(fig, width="stretch", key="yearly_revenue_chart")

    col3, col4 = st.columns(2)

    with col3:
        category_revenue = (
            filtered_orders.groupby("category")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            category_revenue,
            x="category",
            y="total_amount_usd",
            title="Top 10 Categories by Revenue"
        )
        st.plotly_chart(fig, width="stretch", key="category_revenue_chart")

    with col4:
        device_revenue = (
            filtered_orders.groupby("device_used")["total_amount_usd"]
            .sum()
            .reset_index()
        )

        fig = px.pie(
            device_revenue,
            names="device_used",
            values="total_amount_usd",
            title="Revenue by Device"
        )
        st.plotly_chart(fig, width="stretch", key="device_revenue_chart")

# -----------------------------
# CUSTOMERS TAB
# -----------------------------

with tab2:
    st.markdown(
        '<div class="section-heading">Customer Analytics</div>',
        unsafe_allow_html=True
    )

    joined = filtered_orders.merge(customers, on="customer_id", how="left")

    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Customers", f"{joined['customer_id'].nunique():,}")
    c2.metric("Avg Customer Spend", f"${customers['total_spend_usd'].mean():,.2f}")
    c3.metric("Churn Rate", f"{customers['churned'].mean()*100:.2f}%")

    col1, col2 = st.columns(2)

    with col1:
        tier_revenue = (
            joined.groupby("membership_tier")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig = px.bar(
            tier_revenue,
            x="membership_tier",
            y="total_amount_usd",
            title="Revenue by Membership Tier"
        )
        st.plotly_chart(fig, width="stretch", key="membership_revenue_chart")

    with col2:
        country_revenue = (
            joined.groupby("country")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            country_revenue,
            x="country",
            y="total_amount_usd",
            title="Top 10 Countries by Revenue"
        )
        st.plotly_chart(fig, width="stretch", key="country_revenue_chart")

    col3, col4 = st.columns(2)

    with col3:
        acquisition_revenue = (
            joined.groupby("acquisition_channel")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig = px.bar(
            acquisition_revenue,
            x="acquisition_channel",
            y="total_amount_usd",
            title="Revenue by Acquisition Channel"
        )
        st.plotly_chart(fig, width="stretch", key="acquisition_revenue_chart")

    with col4:
        churn_split = customers["churned"].value_counts().reset_index()
        churn_split.columns = ["churned", "count"]

        fig = px.pie(
            churn_split,
            names="churned",
            values="count",
            title="Churned vs Active Customers"
        )
        st.plotly_chart(fig, width="stretch", key="customer_churn_chart")

# -----------------------------
# PRODUCTS TAB
# -----------------------------

with tab3:
    st.markdown(
        '<div class="section-heading">Product Performance</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        product_revenue = (
            filtered_orders.groupby("product_name")["total_amount_usd"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            product_revenue,
            x="product_name",
            y="total_amount_usd",
            title="Top 10 Products by Revenue"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="product_revenue_chart")

    with col2:
        product_volume = (
            filtered_orders.groupby("product_name")["order_id"]
            .nunique()
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            product_volume,
            x="product_name",
            y="order_id",
            title="Top 10 Products by Order Volume"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="product_volume_chart")

    col3, col4 = st.columns(2)

    with col3:
        high_return_products = (
            products.sort_values("return_rate", ascending=False)
            .head(10)
        )

        fig = px.bar(
            high_return_products,
            x="product_name",
            y="return_rate",
            color="category",
            title="Top 10 High Return Products"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="high_return_products_chart")

    with col4:
        top_rated = (
            products.sort_values("avg_rating", ascending=False)
            .head(10)
        )

        fig = px.bar(
            top_rated,
            x="product_name",
            y="avg_rating",
            color="category",
            title="Top Rated Products"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="top_rated_products_chart")

# -----------------------------
# OPERATIONS TAB
# -----------------------------

with tab4:
    st.markdown(
        '<div class="section-heading">Operational Performance</div>',
        unsafe_allow_html=True
    )

    avg_delivery = filtered_orders["delivery_days"].mean()
    cancel_rate = filtered_orders["order_status"].eq("Cancelled").mean() * 100
    return_rate = filtered_orders["returned"].mean() * 100

    o1, o2, o3 = st.columns(3)
    o1.metric("Avg Delivery Days", f"{avg_delivery:.2f}")
    o2.metric("Cancel Rate", f"{cancel_rate:.2f}%")
    o3.metric("Return Rate", f"{return_rate:.2f}%")

    col1, col2 = st.columns(2)

    with col1:
        status_data = filtered_orders["order_status"].value_counts().reset_index()
        status_data.columns = ["order_status", "count"]

        fig = px.pie(
            status_data,
            names="order_status",
            values="count",
            title="Order Status Distribution"
        )
        st.plotly_chart(fig, width="stretch", key="order_status_operations_chart")

    with col2:
        delivery_category = (
            filtered_orders.groupby("category")["delivery_days"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            delivery_category,
            x="category",
            y="delivery_days",
            title="Average Delivery Days by Category"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="delivery_category_operations_chart")

# -----------------------------
# RISK CENTER TAB
# -----------------------------

with tab5:
    st.markdown(
        '<div class="section-heading">Risk Center</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        return_category = (
            filtered_orders.groupby("category")["returned"]
            .mean()
            .mul(100)
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            return_category,
            x="category",
            y="returned",
            title="Top Categories by Return Rate"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="return_category_risk_chart")

    with col2:
        cancel_category = (
            filtered_orders.assign(
                cancelled=filtered_orders["order_status"].eq("Cancelled")
            )
            .groupby("category")["cancelled"]
            .mean()
            .mul(100)
            .sort_values(ascending=False)
            .reset_index()
            .head(10)
        )

        fig = px.bar(
            cancel_category,
            x="category",
            y="cancelled",
            title="Top Categories by Cancel Rate"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch", key="cancel_category_risk_chart")

    st.subheader("High Risk Products")

    high_risk_products = products.sort_values(
        ["return_rate", "total_revenue_usd"],
        ascending=[False, False]
    ).head(20)

    st.dataframe(high_risk_products, width="stretch")

# -----------------------------
# EXECUTIVE INSIGHTS TAB
# -----------------------------

with tab6:
    st.markdown(
        '<div class="section-heading">Executive Insights</div>',
        unsafe_allow_html=True
    )

    best_category = (
        filtered_orders.groupby("category")["total_amount_usd"]
        .sum()
        .idxmax()
    )

    best_product = (
        filtered_orders.groupby("product_name")["total_amount_usd"]
        .sum()
        .idxmax()
    )

    worst_return_category = (
        filtered_orders.groupby("category")["returned"]
        .mean()
        .idxmax()
    )

    st.markdown(f"""
### Business Summary

- Total revenue generated: **${total_revenue:,.2f}**
- Total orders processed: **{total_orders:,}**
- Average order value: **${aov:,.2f}**
- Best revenue category: **{best_category}**
- Best revenue product: **{best_product}**
- Highest return-risk category: **{worst_return_category}**

### Recommendations

1. Increase marketing budget for **{best_category}**.
2. Investigate return reasons in **{worst_return_category}**.
3. Use churn prediction to retain high-risk customers.
4. Improve delivery experience for slow categories.
5. Build revenue forecasting for inventory and budget planning.
""")