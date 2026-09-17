"""Multi-dataset Streamlit demo: Telco / Singtel / Mnassrib + CSV upload scoring."""

from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from ml_train import ARTIFACTS_ROOT, score_dataframe, strip_columns
from recommend import (
    GROQ_RECOMMENDATION_MODELS,
    customer_risk_hints,
    decode_importance_label,
    format_rules_as_markdown,
    generate_multi_llm_recommendations,
    rule_based_recommendations,
)
from train import TELCO_CONFIG
from train2 import SINGTEL_CONFIG
from train3 import MNASSRIB_CONFIG

DATASETS = {
    "telco": TELCO_CONFIG,
    "singtel": SINGTEL_CONFIG,
    "mnassrib": MNASSRIB_CONFIG,
}

st.set_page_config(
    page_title="ChrunAI — Customer Churn",
    page_icon="📉",
    layout="wide",
)


def artifact_paths(name: str) -> dict[str, Path]:
    d = ARTIFACTS_ROOT / name
    return {
        "dir": d,
        "scored": d / "scored.csv",
        "metrics": d / "metrics.json",
        "importance": d / "feature_importance.json",
        "model": d / "model.joblib",
        "config": d / "config.json",
    }


@st.cache_data
def load_scored(name: str) -> pd.DataFrame:
    path = artifact_paths(name)["scored"]
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "row_id" not in df.columns:
        df.insert(0, "row_id", range(1, len(df) + 1))
    return df


@st.cache_data
def load_metrics(name: str) -> dict:
    path = artifact_paths(name)["metrics"]
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_importance(name: str) -> pd.DataFrame:
    path = artifact_paths(name)["importance"]
    if not path.exists():
        return pd.DataFrame(columns=["feature", "importance"])
    with open(path, encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))


@st.cache_resource
def load_model(name: str):
    path = artifact_paths(name)["model"]
    if not path.exists():
        return None
    return joblib.load(path)


def id_column(cfg, df: pd.DataFrame) -> str:
    if cfg.id_col and cfg.id_col in df.columns:
        return cfg.id_col
    return "row_id"


def tab_overview(df: pd.DataFrame, metrics: dict, cfg) -> None:
    st.subheader(f"Overview — {cfg.label}")
    churn_rate = (df["Churn"] == "Yes").mean() if "Churn" in df.columns else None
    c1, c2, c3 = st.columns(3)
    c1.metric("Customers", f"{len(df):,}")
    if churn_rate is not None:
        c2.metric("Historical churn rate", f"{churn_rate:.1%}")
    if metrics:
        c3.metric("Model ROC-AUC (holdout)", f"{metrics.get('roc_auc', 0):.3f}")
    if metrics:
        st.caption(
            f"Holdout accuracy: **{metrics.get('accuracy', 0):.3f}** "
            f"(train {metrics.get('train_rows', '?')} / test {metrics.get('test_rows', '?')})"
        )

    col_a, col_b = st.columns(2)
    with col_a:
        # Prefer Contract-like or International plan
        cat = None
        for c in ("Contract", "International Plan", "International plan", "State"):
            if c in df.columns and "Churn" in df.columns:
                cat = c
                break
        if cat:
            by = (
                df.groupby(cat)["Churn"]
                .apply(lambda s: (s == "Yes").mean())
                .reset_index(name="churn_rate")
            )
            st.markdown(f"**Churn rate by {cat}**")
            st.bar_chart(by.set_index(cat)["churn_rate"])
    with col_b:
        tenure_col = None
        for c in ("tenure", "Account Length", "Account length"):
            if c in df.columns:
                tenure_col = c
                break
        if tenure_col and "Churn" in df.columns:
            series = pd.to_numeric(df[tenure_col], errors="coerce")
            bins = pd.qcut(series, q=4, duplicates="drop")
            by = (
                df.assign(_bin=bins)
                .groupby("_bin", observed=True)["Churn"]
                .apply(lambda s: (s == "Yes").mean())
                .reset_index(name="churn_rate")
            )
            by["_bin"] = by["_bin"].astype(str)
            st.markdown(f"**Churn rate by {tenure_col} quartile**")
            st.bar_chart(by.set_index("_bin")["churn_rate"])

    imp = load_importance(cfg.name)
    if not imp.empty:
        st.markdown("**Global feature importance**")
        top = imp.head(12).copy()
        top["label"] = top["feature"].map(decode_importance_label)
        st.bar_chart(top.set_index("label")["importance"])


def tab_scoring(df: pd.DataFrame, cfg) -> None:
    st.subheader("Scoring & high-risk customers")
    high_only = st.toggle("Show only High + Critical risk", value=True)
    view = df.sort_values("churn_probability", ascending=False)
    if high_only:
        view = view[view["risk_tier"].isin(["High", "Critical"])]

    id_col = id_column(cfg, df)
    cols = []
    for c in [id_col, "churn_probability", "predicted_churn", "risk_tier"] + list(
        cfg.display_columns
    ):
        if c in view.columns and c not in cols:
            cols.append(c)
    st.dataframe(view[cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Download scored CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"scored_{cfg.name}.csv",
        mime="text/csv",
    )


def tab_lookup(df: pd.DataFrame, cfg) -> None:
    st.subheader("Customer lookup")
    id_col = id_column(cfg, df)
    ids = df[id_col].astype(str).tolist()
    selected = st.selectbox(f"Select {id_col}", ids, index=0)
    row = df[df[id_col].astype(str) == selected].iloc[0]

    prob = float(row["churn_probability"])
    tier = row["risk_tier"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Churn probability", f"{prob:.1%}")
    c2.metric("Risk tier", tier)
    c3.metric("Predicted churn", row["predicted_churn"])

    hints = customer_risk_hints(row, dataset=cfg.name)
    if hints:
        st.markdown("**Why this customer may be at risk**")
        for h in hints:
            st.markdown(f"- {h}")

    actions = rule_based_recommendations(row, dataset=cfg.name)
    st.markdown(format_rules_as_markdown(actions))

    st.markdown("---")
    gemini_key = st.session_state.get("gemini_api_key") or ""
    groq_key = st.session_state.get("groq_api_key") or ""
    use_gemini = st.checkbox(
        "Include Gemini",
        value=bool(gemini_key or os.environ.get("GEMINI_API_KEY")),
        key=f"use_gemini_{cfg.name}",
    )
    groq_labels = list(GROQ_RECOMMENDATION_MODELS.keys())
    selected_groq = st.multiselect(
        "Groq models (small)",
        options=groq_labels,
        default=groq_labels if groq_key else [],
        key=f"groq_models_{cfg.name}",
        help="Requires Groq API key in the sidebar.",
    )
    groq_ids = [GROQ_RECOMMENDATION_MODELS[l] for l in selected_groq]

    if st.button("Generate AI retention plans", type="primary"):
        if not use_gemini and not groq_ids:
            st.warning("Enable Gemini or select at least one Groq model, and add API keys in the sidebar.")
        else:
            with st.spinner("Calling LLM providers…"):
                plans = generate_multi_llm_recommendations(
                    row,
                    prob,
                    tier,
                    actions,
                    dataset=cfg.name,
                    gemini_key=gemini_key or None,
                    groq_key=groq_key or None,
                    use_gemini=use_gemini,
                    groq_model_ids=groq_ids if groq_ids else None,
                )
            if not plans:
                st.warning("No API keys configured. Add Gemini or Groq keys in the sidebar.")
                st.markdown(format_rules_as_markdown(actions))
            else:
                for name, text in plans:
                    with st.expander(name, expanded=True):
                        if text.startswith("Error:"):
                            st.error(text)
                        else:
                            st.markdown(text)


def tab_upload(cfg) -> None:
    st.subheader("Score your CSV")
    st.caption(
        f"Upload a CSV with the **same feature columns** as **{cfg.label}**. "
        "No retraining — inference only with the selected model."
    )
    st.code(", ".join(cfg.feature_columns), language=None)
    uploaded = st.file_uploader("Drop CSV here", type=["csv"], key=f"upload_{cfg.name}")
    if not uploaded:
        return

    model = load_model(cfg.name)
    if model is None:
        st.error(f"Missing model — run the matching train script for `{cfg.name}` first.")
        return

    raw = pd.read_csv(uploaded)
    raw = strip_columns(raw)
    try:
        scored = score_dataframe(model, raw, cfg.feature_columns)
    except Exception as e:
        st.error(str(e))
        return

    # optional actual vs predicted
    if cfg.target_col in scored.columns:
        actual = scored[cfg.target_col].map(
            lambda v: "Yes"
            if str(v).strip().rstrip(".").lower() in {"yes", "true", "1"} or v is True
            else "No"
        )
        scored["actual_churn"] = actual
        scored["match"] = scored["actual_churn"] == scored["predicted_churn"]

    st.success(f"Scored {len(scored):,} rows")
    show_cols = [c for c in scored.columns if c in cfg.feature_columns[:6]]
    show_cols += ["churn_probability", "predicted_churn", "risk_tier"]
    if "actual_churn" in scored.columns:
        show_cols += ["actual_churn", "match"]
    show_cols = [c for c in show_cols if c in scored.columns]
    st.dataframe(
        scored[show_cols].sort_values("churn_probability", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download upload scores",
        data=scored.to_csv(index=False).encode("utf-8"),
        file_name=f"upload_scored_{cfg.name}.csv",
        mime="text/csv",
    )


def main() -> None:
    st.title("ChrunAI — Customer Churn Prediction")
    st.caption("Multi-dataset classification, risk tiers, upload scoring, retention tips")

    with st.sidebar:
        st.header("Dataset")
        labels = {k: v.label for k, v in DATASETS.items()}
        choice = st.selectbox(
            "Active model",
            options=list(DATASETS.keys()),
            format_func=lambda k: labels[k],
        )
        cfg = DATASETS[choice]
        paths = artifact_paths(choice)
        if not paths["scored"].exists():
            cmds = {
                "telco": "python train.py",
                "singtel": "python train2.py",
                "mnassrib": "python train3.py",
            }
            st.error(f"Artifacts missing for **{cfg.label}**. Run `{cmds[choice]}` first.")
        else:
            st.success(f"Loaded `{paths['dir'].name}/`")

        st.header("Settings")
        if "gemini_api_key" not in st.session_state:
            st.session_state["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", "")
        st.session_state["gemini_api_key"] = st.text_input(
            "Gemini API key",
            value=st.session_state["gemini_api_key"],
            type="password",
            help="Optional. Used for Gemini retention plans on Lookup.",
        )
        if "groq_api_key" not in st.session_state:
            st.session_state["groq_api_key"] = os.environ.get("GROQ_API_KEY", "")
        st.session_state["groq_api_key"] = st.text_input(
            "Groq API key",
            value=st.session_state["groq_api_key"],
            type="password",
            help="Optional. GPT-OSS / Qwen / Compound Mini on Customer lookup (see Groq docs for current IDs).",
        )

    cfg = DATASETS[choice]
    df = load_scored(cfg.name)
    metrics = load_metrics(cfg.name)

    if df.empty:
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Overview", "Scoring & high risk", "Customer lookup", "Upload & score"]
    )
    with tab1:
        tab_overview(df, metrics, cfg)
    with tab2:
        tab_scoring(df, cfg)
    with tab3:
        tab_lookup(df, cfg)
    with tab4:
        tab_upload(cfg)


if __name__ == "__main__":
    main()
