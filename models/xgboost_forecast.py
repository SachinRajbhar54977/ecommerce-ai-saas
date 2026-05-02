import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error


def create_xgb_features(monthly):
    df = monthly.copy()

    df["month"] = df["order_date"].dt.month
    df["year"] = df["order_date"].dt.year
    df["quarter"] = df["order_date"].dt.quarter
    df["t"] = np.arange(len(df))

    return df


def validate_xgboost(monthly, test_months=6):
    df = create_xgb_features(monthly)

    train_df = df[:-test_months]
    test_df = df[-test_months:]

    features = ["t", "month", "year", "quarter"]

    X_train = train_df[features]
    y_train = train_df["total_amount_usd"]

    X_test = test_df[features]
    y_test = test_df["total_amount_usd"]

    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        objective="reg:squarederror"
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    accuracy = 100 - (mae / df["total_amount_usd"].mean() * 100)

    comparison = pd.DataFrame({
        "ds": test_df["order_date"].values,
        "actual": y_test.values,
        "xgboost_prediction": preds,
        "error": abs(y_test.values - preds)
    })

    return mae, accuracy, comparison


def forecast_xgboost(monthly, forecast_months=6):
    df = create_xgb_features(monthly)

    features = ["t", "month", "year", "quarter"]

    X = df[features]
    y = df["total_amount_usd"]

    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        objective="reg:squarederror"
    )

    model.fit(X, y)

    last_date = df["order_date"].max()

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
    future_df["quarter"] = future_df["order_date"].dt.quarter
    future_df["t"] = np.arange(len(df), len(df) + forecast_months)

    preds = model.predict(future_df[features])

    forecast_df = pd.DataFrame({
        "ds": future_dates,
        "xgboost_forecast": preds
    })

    return forecast_df