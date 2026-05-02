import pandas as pd

from models.prophet_forecast import validate_prophet
from models.ml_forecast import validate_random_forest


def compare_models(prophet_df, monthly, test_months=6):
    prophet_mae, prophet_accuracy, prophet_comparison = validate_prophet(
        prophet_df,
        test_months=test_months
    )

    rf_mae, rf_accuracy, rf_comparison = validate_random_forest(
        monthly,
        test_months=test_months
    )

    leaderboard = pd.DataFrame({
        "Model": ["Prophet", "Random Forest"],
        "MAE": [prophet_mae, rf_mae],
        "Accuracy": [prophet_accuracy, rf_accuracy]
    }).sort_values("MAE")

    best_model = leaderboard.iloc[0]["Model"]

    return {
        "leaderboard": leaderboard,
        "best_model": best_model,
        "prophet_comparison": prophet_comparison,
        "rf_comparison": rf_comparison
    }