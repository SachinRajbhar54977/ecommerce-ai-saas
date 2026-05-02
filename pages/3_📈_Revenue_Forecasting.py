import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_data
from utils.style_loader import load_css

from models.prophet_forecast import (
    prepare_monthly_revenue,
    remove_outliers,
    validate_prophet,
    forecast_future
)

from models.ml_forecast import (
    validate_random_forest,
    forecast_random_forest
)

from models.ensemble_forecast import (
    validate_ensemble,
    forecast_ensemble
)

from models.xgboost_forecast import (
    validate_xgboost,
    forecast_xgboost
)

from models.model_comparison import compare_models

from utils.auth_guard import require_login
# -----------------------------
# LOAD CSS + DATA
# -----------------------------

load_css("global.css")
load_css("analytics.css")


require_login()

customers, orders, revenue, products = load_data()


# -----------------------------
# PAGE HEADER
# -----------------------------

st.markdown("""
<div class="insight-card">
    <h1>📈 Revenue Forecasting</h1>
    <p class="dashboard-subtitle">
        Advanced revenue forecasting using Prophet, Random Forest, model validation, and automatic best model selection.
    </p>
</div>
""", unsafe_allow_html=True)


# -----------------------------
# PREPARE DATA
# -----------------------------

monthly, prophet_df = prepare_monthly_revenue(orders)

# Remove outliers for Prophet stability
prophet_df_clean = remove_outliers(prophet_df)


# -----------------------------
# SIDEBAR SETTINGS
# -----------------------------

st.sidebar.header("📈 Forecast Settings")

forecast_months = st.sidebar.slider(
    "Select Forecast Months",
    min_value=3,
    max_value=12,
    value=6
)

test_months = st.sidebar.slider(
    "Validation Test Months",
    min_value=3,
    max_value=12,
    value=6
)


# -----------------------------
# MODEL VALIDATION
# -----------------------------

st.markdown(
    '<div class="section-heading">🧪 Model Validation</div>',
    unsafe_allow_html=True
)

prophet_mae, prophet_accuracy, prophet_comparison = validate_prophet(
    prophet_df_clean,
    test_months=test_months
)

rf_mae, rf_accuracy, rf_comparison = validate_random_forest(
    monthly,
    test_months=test_months
)

ensemble_mae, ensemble_accuracy, ensemble_comparison = validate_ensemble(
    prophet_df_clean,
    monthly,
    test_months=test_months
)

xgb_mae, xgb_accuracy, xgb_comparison = validate_xgboost(
    monthly,
    test_months=test_months
)

v1, v2, v3, v4 = st.columns(4)

v1.metric("Prophet MAE", f"${prophet_mae:,.0f}", f"{prophet_accuracy:.2f}% Acc")
v2.metric("Random Forest MAE", f"${rf_mae:,.0f}", f"{rf_accuracy:.2f}% Acc")
v3.metric("XGBoost MAE", f"${xgb_mae:,.0f}", f"{xgb_accuracy:.2f}% Acc")
v4.metric("Ensemble MAE", f"${ensemble_mae:,.0f}", f"{ensemble_accuracy:.2f}% Acc")


# -----------------------------
# MODEL COMPARISON
# -----------------------------

st.markdown(
    '<div class="section-heading">⚔️ Model Leaderboard</div>',
    unsafe_allow_html=True
)

comparison_result = compare_models(
    prophet_df_clean,
    monthly,
    test_months=test_months
)

leaderboard = pd.DataFrame({
    "Model": ["Prophet", "Random Forest", "XGBoost", "Ensemble"],
    "MAE": [prophet_mae, rf_mae, xgb_mae, ensemble_mae],
    "Accuracy": [prophet_accuracy, rf_accuracy, xgb_accuracy, ensemble_accuracy]
}).sort_values("MAE")

best_model = leaderboard.iloc[0]["Model"]

st.dataframe(leaderboard, width="stretch")
st.success(f"🏆 Best Model Selected: {best_model}")

import plotly.express as px

fig = px.bar(
    leaderboard,
    x="Model",
    y="MAE",
    color="Model",
    title="Model Performance Comparison (Lower MAE is Better)"
)

st.plotly_chart(fig, width="stretch", key="model_comparison_chart")




# -----------------------------
# VALIDATION COMPARISON TABLE
# -----------------------------

st.markdown(
    '<div class="section-heading">📊 Validation Comparison</div>',
    unsafe_allow_html=True
)

prophet_val = prophet_comparison.rename(
    columns={
        "ds": "Month",
        "y": "Actual Revenue",
        "yhat": "Prophet Prediction",
        "error": "Prophet Error"
    }
)

rf_val = rf_comparison.rename(
    columns={
        "ds": "Month",
        "actual": "Actual Revenue",
        "random_forest_prediction": "Random Forest Prediction",
        "error": "Random Forest Error"
    }
)

validation_table = prophet_val[["Month", "Actual Revenue", "Prophet Prediction", "Prophet Error"]].merge(
    rf_val[["Month", "Random Forest Prediction", "Random Forest Error"]],
    on="Month",
    how="inner"
)

st.dataframe(validation_table, width="stretch")


# -----------------------------
# FUTURE FORECASTS
# -----------------------------

prophet_forecast, prophet_forecast_result = forecast_future(
    prophet_df_clean,
    forecast_months=forecast_months
)

rf_forecast_result = forecast_random_forest(
    monthly,
    forecast_months=forecast_months
)

xgb_forecast_result = forecast_xgboost(
    monthly,
    forecast_months=forecast_months
)


ensemble_forecast_result = forecast_ensemble(
    prophet_df_clean,
    monthly,
    prophet_mae,
    rf_mae,
    forecast_months=forecast_months
)

# -----------------------------
# SELECT FINAL FORECAST
# -----------------------------

if best_model == "Prophet":
    final_forecast_df = prophet_forecast_result.copy()
    final_forecast_df = final_forecast_df.rename(
        columns={
            "ds": "Month",
            "yhat": "Forecast Revenue",
            "yhat_lower": "Lower Estimate",
            "yhat_upper": "Upper Estimate"
        }
    )

elif best_model == "Random Forest":
    final_forecast_df = rf_forecast_result.copy()
    final_forecast_df = final_forecast_df.rename(
        columns={
            "ds": "Month",
            "random_forest_forecast": "Forecast Revenue"
        }
    )
    final_forecast_df["Lower Estimate"] = final_forecast_df["Forecast Revenue"] - rf_mae
    final_forecast_df["Upper Estimate"] = final_forecast_df["Forecast Revenue"] + rf_mae
elif best_model == "XGBoost":
    final_forecast_df = xgb_forecast_result.copy()
    final_forecast_df = final_forecast_df.rename(
        columns={
            "ds": "Month",
            "xgboost_forecast": "Forecast Revenue"
        }
    )

    final_forecast_df["Lower Estimate"] = final_forecast_df["Forecast Revenue"] - xgb_mae
    final_forecast_df["Upper Estimate"] = final_forecast_df["Forecast Revenue"] + xgb_mae    

else:
    final_forecast_df = ensemble_forecast_result.copy()

# -----------------------------
# FORECAST SUMMARY
# -----------------------------

st.markdown(
    '<div class="section-heading">📊 Forecast Summary</div>',
    unsafe_allow_html=True
)

last_actual = monthly["total_amount_usd"].iloc[-1]
next_forecast = final_forecast_df["Forecast Revenue"].iloc[0]
final_forecast = final_forecast_df["Forecast Revenue"].iloc[-1]

k1, k2, k3 = st.columns(3)

k1.metric("Last Actual Revenue", f"${last_actual:,.0f}")
k2.metric("Next Month Forecast", f"${next_forecast:,.0f}")
k3.metric(f"{forecast_months}-Month Forecast", f"${final_forecast:,.0f}")

trend = "📈 Increasing" if final_forecast > next_forecast else "📉 Decreasing"
st.info(f"Forecast Trend: {trend}")

# -----------------------------
# PREPARE DATA FOR CHART
# -----------------------------

# Actual data
history_df = monthly.rename(
    columns={
        "order_date": "Month",
        "total_amount_usd": "Revenue"
    }
)

history_df["Type"] = "Actual"

# Forecast data
forecast_chart_df = final_forecast_df.rename(
    columns={
        "Forecast Revenue": "Revenue"
    }
)

forecast_chart_df["Type"] = f"Forecast ({best_model})"

# Combine both
combined_chart = pd.concat(
    [
        history_df[["Month", "Revenue", "Type"]],
        forecast_chart_df[["Month", "Revenue", "Type"]]
    ],
    ignore_index=True
)

st.markdown(
    '<div class="section-heading">📊 Forecast Visualization</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

# -----------------------------
# LEFT: Actual vs Forecast
# -----------------------------
with col1:

    fig1 = px.line(
        combined_chart,
        x="Month",
        y="Revenue",
        color="Type",
        markers=True,
        title=f"Actual vs Forecast ({best_model})"
    )

    st.plotly_chart(fig1, width="stretch", key="forecast_chart_left")


# -----------------------------
# RIGHT: Confidence Band
# -----------------------------
with col2:

    fig2 = go.Figure()

    # Upper bound
    fig2.add_trace(go.Scatter(
        x=final_forecast_df["Month"],
        y=final_forecast_df["Upper Estimate"],
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))

    # Lower bound with fill
    fig2.add_trace(go.Scatter(
        x=final_forecast_df["Month"],
        y=final_forecast_df["Lower Estimate"],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0, 123, 255, 0.2)',  # smooth blue shade
        line=dict(width=0),
        name="Confidence Range"
    ))

    # Forecast line
    fig2.add_trace(go.Scatter(
        x=final_forecast_df["Month"],
        y=final_forecast_df["Forecast Revenue"],
        mode='lines+markers',
        line=dict(color='cyan', width=3),
        name="Forecast"
    ))

    fig2.update_layout(
        title="Forecast Confidence Range",
        xaxis_title="Month",
        yaxis_title="Revenue",
        template="plotly_dark"
    )

    st.plotly_chart(fig2, width="stretch", key="forecast_chart_right")

# -----------------------------
# FORECAST TABLE
# -----------------------------

st.markdown(
    '<div class="section-heading">📅 Final Forecast Table</div>',
    unsafe_allow_html=True
)

display_forecast = final_forecast_df.copy()

display_forecast["Forecast Revenue"] = display_forecast["Forecast Revenue"].round(2)
display_forecast["Lower Estimate"] = display_forecast["Lower Estimate"].round(2)
display_forecast["Upper Estimate"] = display_forecast["Upper Estimate"].round(2)

st.dataframe(display_forecast, width="stretch")


# -----------------------------
# DOWNLOAD FORECAST
# -----------------------------

csv = display_forecast.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Forecast Data",
    data=csv,
    file_name="revenue_forecast.csv",
    mime="text/csv"
)

if best_model == "Prophet":
    best_accuracy = prophet_accuracy
    best_mae = prophet_mae

elif best_model == "Random Forest":
    best_accuracy = rf_accuracy
    best_mae = rf_mae

elif best_model == "XGBoost":
    best_accuracy = xgb_accuracy
    best_mae = xgb_mae

else:  # Ensemble
    best_accuracy = ensemble_accuracy
    best_mae = ensemble_mae
# -----------------------------
# BUSINESS INSIGHTS
# -----------------------------
st.markdown('<div class="section-heading">💡 Business Insights</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

# -----------------------------
# LEFT: Forecast Interpretation
# -----------------------------
with col1:
    st.markdown(f"""
    <div class="insight-card">
        <h3>📊 Forecast Interpretation</h3>
        <ul>
            <li><b>Best Model:</b> {best_model}</li>
            <li><b>Accuracy:</b> {best_accuracy:.2f}%</li>
            <li><b>Avg Error:</b> ${best_mae:,.0f}</li>
            <li><b>Last Revenue:</b> ${last_actual:,.0f}</li>
            <li><b>Next Month:</b> ${next_forecast:,.0f}</li>
            <li><b>{forecast_months}-Month:</b> ${final_forecast:,.0f}</li>
            <li><b>Trend:</b> {trend}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------
# RIGHT: Business Recommendations
# -----------------------------
with col2:
    st.markdown("""
    <div class="insight-card">
        <h3>📈 Business Recommendations</h3>
        <ul>
            <li>Use forecast range, not exact values</li>
            <li>Increase inventory if demand rising</li>
            <li>Run promotions if revenue declining</li>
            <li>Track forecast vs actual monthly</li>
            <li>Plan budgets using trend direction</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------
# FULL WIDTH: Decision Insight
# -----------------------------
st.markdown(f"""
<div class="insight-card" style="margin-top: 20px;">
    <h3>💼 Business Decision Insight</h3>
    <p style="font-size:16px;">
        Based on current data, the system selected <b>{best_model}</b> as the most reliable model.
        The forecast indicates a <b>{trend.lower()}</b> revenue trend.
        Expected variation range should be considered for planning decisions.
    </p>
</div>
""", unsafe_allow_html=True)