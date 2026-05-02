from prophet import Prophet
import pandas as pd
from sklearn.metrics import mean_absolute_error


def prepare_monthly_revenue(orders):
    monthly = (
        orders
        .groupby(pd.Grouper(key="order_date", freq="ME"))["total_amount_usd"]
        .sum()
        .reset_index()
        .sort_values("order_date")
    )

    prophet_df = monthly.rename(
        columns={
            "order_date": "ds",
            "total_amount_usd": "y"
        }
    )

    return monthly, prophet_df


def remove_outliers(prophet_df):
    q_low = prophet_df["y"].quantile(0.05)
    q_high = prophet_df["y"].quantile(0.95)

    return prophet_df[
        (prophet_df["y"] >= q_low) &
        (prophet_df["y"] <= q_high)
    ]


def train_prophet_model(prophet_df):
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=15
    )

    model.add_seasonality(
        name="monthly",
        period=30.5,
        fourier_order=5
    )

    model.fit(prophet_df)

    return model


def validate_prophet(prophet_df, test_months=6):
    train_df = prophet_df[:-test_months]
    test_df = prophet_df[-test_months:]

    model = train_prophet_model(train_df)

    future = model.make_future_dataframe(periods=test_months, freq="ME")
    forecast = model.predict(future)

    forecast_test = forecast[["ds", "yhat"]].tail(test_months)

    comparison = test_df.merge(forecast_test, on="ds")
    comparison["error"] = abs(comparison["y"] - comparison["yhat"])

    mae = comparison["error"].mean()
    accuracy = 100 - (mae / prophet_df["y"].mean() * 100)

    return mae, accuracy, comparison


def forecast_future(prophet_df, forecast_months=6):
    model = train_prophet_model(prophet_df)

    future = model.make_future_dataframe(
        periods=forecast_months,
        freq="ME"
    )

    forecast = model.predict(future)

    forecast_result = forecast[
        ["ds", "yhat", "yhat_lower", "yhat_upper"]
    ].tail(forecast_months)

    return forecast, forecast_result