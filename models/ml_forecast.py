import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


def create_ml_features(monthly):
    ml_df = monthly.copy()

    ml_df["month"] = ml_df["order_date"].dt.month
    ml_df["year"] = ml_df["order_date"].dt.year
    ml_df["t"] = np.arange(len(ml_df))

    return ml_df


def validate_random_forest(monthly, test_months=6):
    ml_df = create_ml_features(monthly)

    train_df = ml_df[:-test_months]
    test_df = ml_df[-test_months:]

    features = ["t", "month", "year"]

    X_train = train_df[features]
    y_train = train_df["total_amount_usd"]

    X_test = test_df[features]
    y_test = test_df["total_amount_usd"]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    accuracy = 100 - (mae / ml_df["total_amount_usd"].mean() * 100)

    comparison = pd.DataFrame({
        "ds": test_df["order_date"].values,
        "actual": y_test.values,
        "random_forest_prediction": preds,
        "error": abs(y_test.values - preds)
    })

    return mae, accuracy, comparison


def forecast_random_forest(monthly, forecast_months=6):
    ml_df = create_ml_features(monthly)

    features = ["t", "month", "year"]

    X = ml_df[features]
    y = ml_df["total_amount_usd"]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        random_state=42
    )

    model.fit(X, y)

    last_date = ml_df["order_date"].max()
    future_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=forecast_months,
        freq="ME"
    )

    future_df = pd.DataFrame({
        "order_date": future_dates
    })

    future_df["month"] = future_df["order_date"].dt.month
    future_df["year"] = future_df["order_date"].dt.year
    future_df["t"] = np.arange(len(ml_df), len(ml_df) + forecast_months)

    future_preds = model.predict(future_df[features])

    forecast_df = pd.DataFrame({
        "ds": future_dates,
        "random_forest_forecast": future_preds
    })

    return forecast_df