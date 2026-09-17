"""Train mnassrib (BigML Orange) telecom churn model → artifacts/mnassrib/."""

from pathlib import Path

from ml_train import DatasetConfig, clean_generic, train_and_export

ROOT = Path(__file__).resolve().parent

MNASSRIB_CONFIG = DatasetConfig(
    name="mnassrib",
    label="Mnassrib BigML",
    csv_path=ROOT / "data" / "mnassrib" / "churn-bigml-80.csv",
    target_col="Churn",
    positive_values=(True, "True", "true", "1", "yes"),
    id_col=None,  # no customer id — synthetic index used in UI
    numeric_features=[
        "Account length",
        "Area code",
        "Number vmail messages",
        "Total day minutes",
        "Total day calls",
        "Total day charge",
        "Total eve minutes",
        "Total eve calls",
        "Total eve charge",
        "Total night minutes",
        "Total night calls",
        "Total night charge",
        "Total intl minutes",
        "Total intl calls",
        "Total intl charge",
        "Customer service calls",
    ],
    categorical_features=[
        "State",
        "International plan",
        "Voice mail plan",
    ],
    rule_columns=[
        "International plan",
        "Voice mail plan",
        "Account length",
        "Total day charge",
        "Customer service calls",
        "Churn",
    ],
    display_columns=[
        "State",
        "International plan",
        "Account length",
        "Customer service calls",
        "Total day charge",
        "Churn",
    ],
    clean_fn=clean_generic,
    extra_paths=[ROOT / "data" / "mnassrib" / "churn-bigml-20.csv"],
)

if __name__ == "__main__":
    train_and_export(MNASSRIB_CONFIG)
