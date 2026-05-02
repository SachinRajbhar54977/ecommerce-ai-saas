REQUIRED_COLUMNS = {
    "customers": [
        "customer_id", "age", "country", "membership_tier",
        "total_orders", "total_spend_usd", "days_since_last_purchase",
        "churned"
    ],
    "orders": [
        "order_id", "customer_id", "order_date", "category",
        "product_name", "total_amount_usd", "order_status",
        "returned"
    ],
    "monthly_revenue": [
        "year", "month"
    ],
    "product_summary": [
        "product_name", "category", "return_rate"
    ]
}


CANONICAL_FILENAMES = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "monthly_revenue": "monthly_revenue.csv",
    "product_summary": "product_summary.csv"
}


def detect_dataset_type(df):
    df_columns = set(df.columns)

    best_match = None
    best_score = 0

    for dataset_type, required_cols in REQUIRED_COLUMNS.items():
        required_set = set(required_cols)
        matched_cols = required_set.intersection(df_columns)
        score = len(matched_cols) / len(required_set)

        if score > best_score:
            best_score = score
            best_match = dataset_type

    if best_score >= 0.70:
        return best_match, best_score

    return None, best_score


def validate_schema(df):
    dataset_type, score = detect_dataset_type(df)

    if dataset_type is None:
        return False, None, f"Could not detect dataset type. Match score: {score:.2f}"

    required = REQUIRED_COLUMNS[dataset_type]
    missing = [col for col in required if col not in df.columns]

    if missing:
        return False, dataset_type, f"Detected {dataset_type}, but missing columns: {missing}"

    return True, dataset_type, "Valid file"


def get_canonical_filename(dataset_type):
    return CANONICAL_FILENAMES[dataset_type]