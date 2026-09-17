"""Train IBM Telco churn model → artifacts/telco/."""

from pathlib import Path

from ml_train import DatasetConfig, clean_telco, train_and_export

ROOT = Path(__file__).resolve().parent

TELCO_CONFIG = DatasetConfig(
    name="telco",
    label="IBM Telco",
    csv_path=ROOT / "data" / "telco_customer_churn.csv",
    target_col="Churn",
    positive_values=("Yes", "yes", "1", "true", True),
    id_col="customerID",
    numeric_features=["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges"],
    categorical_features=[
        "gender",
        "Partner",
        "Dependents",
        "PhoneService",
        "MultipleLines",
        "InternetService",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
        "Contract",
        "PaperlessBilling",
        "PaymentMethod",
    ],
    rule_columns=[
        "customerID",
        "Contract",
        "PaymentMethod",
        "tenure",
        "InternetService",
        "OnlineSecurity",
        "TechSupport",
        "MonthlyCharges",
        "Churn",
    ],
    display_columns=[
        "customerID",
        "Contract",
        "tenure",
        "PaymentMethod",
        "MonthlyCharges",
        "Churn",
    ],
    clean_fn=clean_telco,
)

if __name__ == "__main__":
    train_and_export(TELCO_CONFIG)
