"""Train Singtel telecom churn model → artifacts/singtel/."""

from pathlib import Path

from ml_train import DatasetConfig, clean_generic, train_and_export

ROOT = Path(__file__).resolve().parent

SINGTEL_CONFIG = DatasetConfig(
    name="singtel",
    label="Singtel Telecom",
    csv_path=ROOT / "data" / "singtel" / "Telecom Churn Data SingTel.csv",
    target_col="Churn",
    positive_values=("True", "true", " True.", "1", True),
    id_col="Phone Number",
    numeric_features=[
        "Account Length",
        "Area Code",
        "Num of Voice mail Messages",
        "Total Day Minutes",
        "Total Day Calls",
        "Total day Charge",
        "Total Eve Minutes",
        "Total Eve Calls",
        "Total Eve Charge",
        "Total Night Minutes",
        "Total Night Calls",
        "Total Night Charge",
        "Total International Minutes",
        "Total Intl  Calls",
        "Total Intl Charge",
        "Number Customer Service calls",
    ],
    categorical_features=[
        "State",
        "International Plan",
        "Voice mail Plan",
    ],
    rule_columns=[
        "Phone Number",
        "International Plan",
        "Voice mail Plan",
        "Account Length",
        "Total day Charge",
        "Number Customer Service calls",
        "Churn",
    ],
    display_columns=[
        "Phone Number",
        "State",
        "International Plan",
        "Account Length",
        "Number Customer Service calls",
        "Total day Charge",
        "Churn",
    ],
    clean_fn=clean_generic,
)

if __name__ == "__main__":
    train_and_export(SINGTEL_CONFIG)
