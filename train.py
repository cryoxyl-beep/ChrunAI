"""Train churn model once; write model.joblib, scored_customers.csv, metrics.json."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "telco_customer_churn.csv"
MODEL_PATH = ROOT / "model.joblib"
SCORED_PATH = ROOT / "scored_customers.csv"
METRICS_PATH = ROOT / "metrics.json"
IMPORTANCE_PATH = ROOT / "feature_importance.json"

# Risk tier thresholds (explicit for judges)
TIER_LOW = 0.30
TIER_MEDIUM = 0.55
TIER_HIGH = 0.75

NUMERIC_FEATURES = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_FEATURES = [
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
]
RULE_COLUMNS = [
    "customerID",
    "Contract",
    "PaymentMethod",
    "tenure",
    "InternetService",
    "OnlineSecurity",
    "TechSupport",
    "MonthlyCharges",
    "Churn",
]


def risk_tier(probability: float) -> str:
    if probability < TIER_LOW:
        return "Low"
    if probability < TIER_MEDIUM:
        return "Medium"
    if probability < TIER_HIGH:
        return "High"
    return "Critical"


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    missing = df["TotalCharges"].isna()
    if missing.any():
        imputed = df.loc[missing, "tenure"] * df.loc[missing, "MonthlyCharges"]
        df.loc[missing, "TotalCharges"] = imputed
        still_missing = df["TotalCharges"].isna()
        if still_missing.any():
            df.loc[still_missing, "TotalCharges"] = df["TotalCharges"].median()
    return df


def build_pipeline() -> Pipeline:
    numeric_transformer = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )
    categorical_transformer = Pipeline(
        steps=[
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            )
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ]
    )


def export_feature_importance(pipeline: Pipeline) -> list[dict]:
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    feature_names = preprocessor.get_feature_names_out()
    importances = classifier.feature_importances_
    pairs = sorted(
        zip(feature_names, importances),
        key=lambda x: x[1],
        reverse=True,
    )
    return [
        {"feature": name, "importance": float(imp)} for name, imp in pairs[:25]
    ]


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = load_and_clean(DATA_PATH)
    y = (df["Churn"] == "Yes").astype(int)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "churn_rate": float(y.mean()),
    }

    joblib.dump(pipeline, MODEL_PATH)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(IMPORTANCE_PATH, "w", encoding="utf-8") as f:
        json.dump(export_feature_importance(pipeline), f, indent=2)

    probs = pipeline.predict_proba(X)[:, 1]
    preds = pipeline.predict(X)
    scored = df[RULE_COLUMNS].copy()
    scored["churn_probability"] = probs
    scored["predicted_churn"] = ["Yes" if p == 1 else "No" for p in preds]
    scored["risk_tier"] = [risk_tier(p) for p in probs]
    scored.to_csv(SCORED_PATH, index=False)

    print("Training complete.")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  ROC-AUC:  {metrics['roc_auc']:.4f}")
    print(f"  Saved: {MODEL_PATH.name}, {SCORED_PATH.name}, {METRICS_PATH.name}")


if __name__ == "__main__":
    main()
