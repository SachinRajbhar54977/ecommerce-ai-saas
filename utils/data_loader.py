from pathlib import Path
import pandas as pd
import streamlit as st

DEFAULT_DATA_DIR = Path("data")
UPLOAD_DIR = Path("backend/uploads")


def get_user_upload_dir():
    user_email = st.session_state.get("user_email")

    if user_email:
        return UPLOAD_DIR / user_email

    return None


def read_csv_safely(file_path):
    if file_path.exists():
        return pd.read_csv(file_path)
    return None


@st.cache_data
def load_default_data():
    customers = pd.read_csv(DEFAULT_DATA_DIR / "customers.csv")
    orders = pd.read_csv(DEFAULT_DATA_DIR / "orders.csv")
    revenue = pd.read_csv(DEFAULT_DATA_DIR / "monthly_revenue.csv")
    products = pd.read_csv(DEFAULT_DATA_DIR / "product_summary.csv")

    return customers, orders, revenue, products


def load_data():
    default_customers, default_orders, default_revenue, default_products = load_default_data()

    user_dir = get_user_upload_dir()

    if user_dir and user_dir.exists():
        uploaded_customers = read_csv_safely(user_dir / "customers.csv")
        uploaded_orders = read_csv_safely(user_dir / "orders.csv")
        uploaded_revenue = read_csv_safely(user_dir / "monthly_revenue.csv")
        uploaded_products = read_csv_safely(user_dir / "product_summary.csv")

        customers = uploaded_customers if uploaded_customers is not None else default_customers
        orders = uploaded_orders if uploaded_orders is not None else default_orders
        revenue = uploaded_revenue if uploaded_revenue is not None else default_revenue
        products = uploaded_products if uploaded_products is not None else default_products
    else:
        customers, orders, revenue, products = (
            default_customers,
            default_orders,
            default_revenue,
            default_products
        )

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