import pandas as pd
from sklearn.metrics import mean_absolute_error

from models.prophet_forecast import validate_prophet, forecast_future
from models.ml_forecast import validate_random_forest, forecast_random_forest


def validate_ensemble(prophet_df, monthly, test_months=6):
    prophet_mae, prophet_accuracy, prophet_comp = validate_prophet(
        prophet_df,
        test_months=test_months
    )

    rf_mae, rf_accuracy, rf_comp = validate_random_forest(
        monthly,
        test_months=test_months
    )

    prophet_temp = prophet_comp.rename(
        columns={
            "ds": "Month",
            "y": "Actual Revenue",
            "yhat": "Prophet Prediction"
        }
    )

    rf_temp = rf_comp.rename(
        columns={
            "ds": "Month",
            "random_forest_prediction": "Random Forest Prediction"
        }
    )

    merged = prophet_temp[["Month", "Actual Revenue", "Prophet Prediction"]].merge(
        rf_temp[["Month", "Random Forest Prediction"]],
        on="Month",
        how="inner"
    )

    merged["Ensemble Prediction"] = (
        merged["Prophet Prediction"] + merged["Random Forest Prediction"]
    ) / 2

    merged["Ensemble Error"] = abs(
        merged["Actual Revenue"] - merged["Ensemble Prediction"]
    )

    ensemble_mae = mean_absolute_error(
        merged["Actual Revenue"],
        merged["Ensemble Prediction"]
    )

    avg_revenue = monthly["total_amount_usd"].mean()
    ensemble_accuracy = 100 - (ensemble_mae / avg_revenue * 100)

    return ensemble_mae, ensemble_accuracy, merged


def forecast_ensemble(prophet_df, monthly, prophet_mae, rf_mae, forecast_months=6):
    prophet_forecast, prophet_result = forecast_future(
        prophet_df,
        forecast_months=forecast_months
    )

    rf_result = forecast_random_forest(
        monthly,
        forecast_months=forecast_months
    )

    prophet_final = prophet_result.rename(
        columns={
            "ds": "Month",
            "yhat": "Prophet Forecast",
            "yhat_lower": "Prophet Lower",
            "yhat_upper": "Prophet Upper"
        }
    )

    rf_final = rf_result.rename(
        columns={
            "ds": "Month",
            "random_forest_forecast": "Random Forest Forecast"
        }
    )

    ensemble = prophet_final[
        ["Month", "Prophet Forecast", "Prophet Lower", "Prophet Upper"]
    ].merge(
        rf_final[["Month", "Random Forest Forecast"]],
        on="Month",
        how="inner"
    )

   # Weight based on inverse MAE
    w_prophet = 1 / (prophet_mae + 1e-6)
    w_rf = 1 / (rf_mae + 1e-6)

    w_total = w_prophet + w_rf

    ensemble["Forecast Revenue"] = (
        (w_prophet * ensemble["Prophet Forecast"]) +
        (w_rf * ensemble["Random Forest Forecast"])
    ) / w_total

    ensemble["Lower Estimate"] = ensemble[
        ["Prophet Lower", "Random Forest Forecast"]
    ].min(axis=1)

    ensemble["Upper Estimate"] = ensemble[
        ["Prophet Upper", "Random Forest Forecast"]
    ].max(axis=1)

    return ensemble