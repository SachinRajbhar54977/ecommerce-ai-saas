from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
import pandas as pd

from backend.auth import decode_token

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

from models.xgboost_forecast import (
    validate_xgboost,
    forecast_xgboost
)

from models.ensemble_forecast import (
    validate_ensemble,
    forecast_ensemble
)

router = APIRouter(prefix="/forecast", tags=["Forecast"])
security = HTTPBearer()

BASE_UPLOAD_DIR = Path("backend/uploads")
DEFAULT_DATA_DIR = Path("data")


def get_user_email_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    user_email = decode_token(token)

    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_email


def load_user_orders(user_email: str):
    user_orders_path = BASE_UPLOAD_DIR / user_email / "orders.csv"
    default_orders_path = DEFAULT_DATA_DIR / "orders.csv"

    if user_orders_path.exists():
        orders = pd.read_csv(user_orders_path)
        data_source = "uploaded_user_data"
    elif default_orders_path.exists():
        orders = pd.read_csv(default_orders_path)
        data_source = "default_demo_data"
    else:
        raise HTTPException(status_code=404, detail="orders.csv not found")

    if "order_date" not in orders.columns:
        raise HTTPException(status_code=400, detail="orders.csv must contain order_date column")

    if "total_amount_usd" not in orders.columns:
        raise HTTPException(status_code=400, detail="orders.csv must contain total_amount_usd column")

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders = orders.dropna(subset=["order_date"])

    if orders.empty:
        raise HTTPException(status_code=400, detail="No valid order_date values found in orders.csv")

    return orders, data_source


@router.post("/run")
def run_forecast(
    forecast_months: int = 6,
    test_months: int = 6,
    user_email: str = Depends(get_user_email_from_token)
):
    if forecast_months < 1 or forecast_months > 24:
        raise HTTPException(
            status_code=400,
            detail="forecast_months must be between 1 and 24"
        )

    if test_months < 3 or test_months > 12:
        raise HTTPException(
            status_code=400,
            detail="test_months must be between 3 and 12"
        )

    orders, data_source = load_user_orders(user_email)

    monthly, prophet_df = prepare_monthly_revenue(orders)
    prophet_df_clean = remove_outliers(prophet_df)

    if len(monthly) <= test_months + 6:
        raise HTTPException(
            status_code=400,
            detail="Not enough monthly data for forecasting. Upload at least 12+ months of orders."
        )

    prophet_mae, prophet_accuracy, _ = validate_prophet(
        prophet_df_clean,
        test_months=test_months
    )

    rf_mae, rf_accuracy, _ = validate_random_forest(
        monthly,
        test_months=test_months
    )

    xgb_mae, xgb_accuracy, _ = validate_xgboost(
        monthly,
        test_months=test_months
    )

    ensemble_mae, ensemble_accuracy, _ = validate_ensemble(
        prophet_df_clean,
        monthly,
        test_months=test_months
    )

    leaderboard = pd.DataFrame({
        "model": ["Prophet", "Random Forest", "XGBoost", "Ensemble"],
        "mae": [prophet_mae, rf_mae, xgb_mae, ensemble_mae],
        "accuracy": [prophet_accuracy, rf_accuracy, xgb_accuracy, ensemble_accuracy]
    }).sort_values("mae")

    best_model = leaderboard.iloc[0]["model"]

    _, prophet_forecast_result = forecast_future(
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

    if best_model == "Prophet":
        final_forecast_df = prophet_forecast_result.rename(
            columns={
                "ds": "month",
                "yhat": "forecast_revenue",
                "yhat_lower": "lower_estimate",
                "yhat_upper": "upper_estimate"
            }
        )

    elif best_model == "Random Forest":
        final_forecast_df = rf_forecast_result.rename(
            columns={
                "ds": "month",
                "random_forest_forecast": "forecast_revenue"
            }
        )
        final_forecast_df["lower_estimate"] = final_forecast_df["forecast_revenue"] - rf_mae
        final_forecast_df["upper_estimate"] = final_forecast_df["forecast_revenue"] + rf_mae

    elif best_model == "XGBoost":
        final_forecast_df = xgb_forecast_result.rename(
            columns={
                "ds": "month",
                "xgboost_forecast": "forecast_revenue"
            }
        )
        final_forecast_df["lower_estimate"] = final_forecast_df["forecast_revenue"] - xgb_mae
        final_forecast_df["upper_estimate"] = final_forecast_df["forecast_revenue"] + xgb_mae

    else:
        final_forecast_df = ensemble_forecast_result.rename(
            columns={
                "Month": "month",
                "Forecast Revenue": "forecast_revenue",
                "Lower Estimate": "lower_estimate",
                "Upper Estimate": "upper_estimate"
            }
        )

    final_forecast_df["month"] = pd.to_datetime(
        final_forecast_df["month"]
    ).dt.strftime("%Y-%m-%d")

    last_actual = float(monthly["total_amount_usd"].iloc[-1])
    next_forecast = float(final_forecast_df["forecast_revenue"].iloc[0])
    final_forecast = float(final_forecast_df["forecast_revenue"].iloc[-1])

    trend = "Increasing" if final_forecast > next_forecast else "Decreasing"

    return {
        "user": user_email,
        "data_source": data_source,
        "forecast_months": forecast_months,
        "test_months": test_months,
        "best_model": best_model,
        "leaderboard": leaderboard.to_dict(orient="records"),
        "summary": {
            "last_actual_revenue": last_actual,
            "next_month_forecast": next_forecast,
            "final_month_forecast": final_forecast,
            "trend": trend
        },
        "forecast": final_forecast_df[
            ["month", "forecast_revenue", "lower_estimate", "upper_estimate"]
        ].to_dict(orient="records")
    }