"""Shared churn training helpers for multi-dataset pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

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
ARTIFACTS_ROOT = ROOT / "artifacts"

TIER_LOW = 0.30
TIER_MEDIUM = 0.55
TIER_HIGH = 0.75


def risk_tier(probability: float) -> str:
    if probability < TIER_LOW:
        return "Low"
    if probability < TIER_MEDIUM:
        return "Medium"
    if probability < TIER_HIGH:
        return "High"
    return "Critical"


@dataclass
class DatasetConfig:
    name: str
    label: str
    csv_path: Path
    target_col: str
    positive_values: tuple
    id_col: str | None
    numeric_features: list[str]
    categorical_features: list[str]
    rule_columns: list[str]
    display_columns: list[str]
    clean_fn: Callable[[pd.DataFrame], pd.DataFrame] | None = None
    extra_paths: list[Path] = field(default_factory=list)

    @property
    def feature_columns(self) -> list[str]:
        return self.numeric_features + self.categorical_features

    @property
    def artifact_dir(self) -> Path:
        return ARTIFACTS_ROOT / self.name


def strip_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def clean_telco(df: pd.DataFrame) -> pd.DataFrame:
    df = strip_columns(df)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    missing = df["TotalCharges"].isna()
    if missing.any():
        imputed = df.loc[missing, "tenure"] * df.loc[missing, "MonthlyCharges"]
        df.loc[missing, "TotalCharges"] = imputed
        still = df["TotalCharges"].isna()
        if still.any():
            df.loc[still, "TotalCharges"] = df["TotalCharges"].median()
    return df


def clean_generic(df: pd.DataFrame) -> pd.DataFrame:
    return strip_columns(df)


def build_pipeline(numeric: list[str], categorical: list[str]) -> Pipeline:
    transformers = []
    if numeric:
        transformers.append(
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        )
                    ]
                ),
                categorical,
            )
        )
    preprocessor = ColumnTransformer(transformers=transformers)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    return Pipeline([("preprocessor", preprocessor), ("classifier", clf)])


def encode_target(series: pd.Series, positive_values: tuple) -> pd.Series:
    normalized = series.map(
        lambda v: str(v).strip().rstrip(".").lower() if not isinstance(v, bool) else v
    )
    positives = {str(p).strip().rstrip(".").lower() for p in positive_values}
    # bool True and "true" / "yes" / "1"
    def is_pos(v):
        if isinstance(v, bool):
            return v
        return str(v).strip().rstrip(".").lower() in positives or v is True

    return series.map(is_pos).astype(int)


def export_feature_importance(pipeline: Pipeline) -> list[dict]:
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    names = preprocessor.get_feature_names_out()
    importances = classifier.feature_importances_
    pairs = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)
    return [{"feature": n, "importance": float(i)} for n, i in pairs[:25]]


def load_dataset(config: DatasetConfig) -> pd.DataFrame:
    paths = [config.csv_path] + list(config.extra_paths)
    frames = []
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {p}")
        frames.append(pd.read_csv(p))
    df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    clean = config.clean_fn or clean_generic
    return clean(df)


def train_and_export(config: DatasetConfig) -> dict:
    df = load_dataset(config)
    missing_feats = [c for c in config.feature_columns if c not in df.columns]
    if missing_feats:
        raise ValueError(f"{config.name}: missing features {missing_feats}")
    if config.target_col not in df.columns:
        raise ValueError(f"{config.name}: missing target {config.target_col}")

    y = encode_target(df[config.target_col], config.positive_values)
    X = df[config.feature_columns]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipeline = build_pipeline(config.numeric_features, config.categorical_features)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    metrics = {
        "dataset": config.name,
        "label": config.label,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "churn_rate": float(y.mean()),
    }

    out = config.artifact_dir
    out.mkdir(parents=True, exist_ok=True)
    model_path = out / "model.joblib"
    scored_path = out / "scored.csv"
    metrics_path = out / "metrics.json"
    importance_path = out / "feature_importance.json"
    config_path = out / "config.json"

    joblib.dump(pipeline, model_path)
    importance = export_feature_importance(pipeline)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(importance_path, "w", encoding="utf-8") as f:
        json.dump(importance, f, indent=2)

    meta = {
        "name": config.name,
        "label": config.label,
        "id_col": config.id_col,
        "target_col": config.target_col,
        "numeric_features": config.numeric_features,
        "categorical_features": config.categorical_features,
        "feature_columns": config.feature_columns,
        "rule_columns": config.rule_columns,
        "display_columns": config.display_columns,
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    probs = pipeline.predict_proba(X)[:, 1]
    preds = pipeline.predict(X)
    keep = []
    if config.id_col and config.id_col in df.columns:
        keep.append(config.id_col)
    for c in config.rule_columns:
        if c not in keep and c in df.columns:
            keep.append(c)
    for c in config.display_columns:
        if c not in keep and c in df.columns:
            keep.append(c)
    if config.target_col not in keep and config.target_col in df.columns:
        keep.append(config.target_col)

    scored = df[keep].copy()
    scored["churn_probability"] = probs
    scored["predicted_churn"] = ["Yes" if p == 1 else "No" for p in preds]
    scored["risk_tier"] = [risk_tier(float(p)) for p in probs]
    # Normalize target display
    scored["Churn"] = ["Yes" if v == 1 else "No" for v in y]
    scored.to_csv(scored_path, index=False)

    print(f"[{config.name}] Training complete.")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  ROC-AUC:  {metrics['roc_auc']:.4f}")
    print(f"  Saved: {out.relative_to(ROOT)}/")
    return metrics


def score_dataframe(pipeline: Pipeline, df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Upload missing required columns: {missing}")
    X = df[feature_columns]
    probs = pipeline.predict_proba(X)[:, 1]
    preds = pipeline.predict(X)
    out = df.copy()
    out["churn_probability"] = probs
    out["predicted_churn"] = ["Yes" if p == 1 else "No" for p in preds]
    out["risk_tier"] = [risk_tier(float(p)) for p in probs]
    return out
