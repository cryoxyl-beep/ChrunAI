"""Streamlit demo: Overview, Scoring & high risk, Customer lookup."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from recommend import (
    customer_risk_hints,
    decode_importance_label,
    format_rules_as_markdown,
    polish_with_gemini,
    rule_based_recommendations,
)

ROOT = Path(__file__).resolve().parent
SCORED_PATH = ROOT / "scored_customers.csv"
METRICS_PATH = ROOT / "metrics.json"
IMPORTANCE_PATH = ROOT / "feature_importance.json"

st.set_page_config(
    page_title="Customer Churn Prediction Agent",
    page_icon="📉",
    layout="wide",
)


@st.cache_data
def load_scored() -> pd.DataFrame:
    if not SCORED_PATH.exists():
        st.error(
            f"Missing `{SCORED_PATH.name}`. Run `python train.py` first."
        )
        st.stop()
    return pd.read_csv(SCORED_PATH)


@st.cache_data
def load_metrics() -> dict:
    if METRICS_PATH.exists():
        with open(METRICS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data
def load_importance() -> pd.DataFrame:
    if not IMPORTANCE_PATH.exists():
        return pd.DataFrame(columns=["feature", "importance"])
    with open(IMPORTANCE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def tab_overview(df: pd.DataFrame, metrics: dict) -> None:
    st.subheader("Dataset overview")
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
            f"(train {metrics.get('train_rows', '?')} / test {metrics.get('test_rows', '?')} rows)"
        )

    col_a, col_b = st.columns(2)
    with col_a:
        if "Contract" in df.columns and "Churn" in df.columns:
            by_contract = (
                df.groupby("Contract")["Churn"]
                .apply(lambda s: (s == "Yes").mean())
                .reset_index(name="churn_rate")
            )
            st.markdown("**Churn rate by contract**")
            st.bar_chart(by_contract.set_index("Contract")["churn_rate"])
    with col_b:
        if "tenure" in df.columns and "Churn" in df.columns:
            bins = pd.cut(df["tenure"], bins=[0, 12, 24, 48, 72], labels=["0-12", "13-24", "25-48", "49+"])
            by_tenure = (
                df.assign(tenure_bin=bins)
                .groupby("tenure_bin", observed=True)["Churn"]
                .apply(lambda s: (s == "Yes").mean())
                .reset_index(name="churn_rate")
            )
            st.markdown("**Churn rate by tenure (months)**")
            st.bar_chart(by_tenure.set_index("tenure_bin")["churn_rate"])

    imp = load_importance()
    if not imp.empty:
        st.markdown("**Global feature importance (model)**")
        top = imp.head(12).copy()
        top["label"] = top["feature"].map(decode_importance_label)
        st.bar_chart(top.set_index("label")["importance"])


def tab_scoring(df: pd.DataFrame) -> None:
    st.subheader("Scoring & high-risk customers")
    high_only = st.toggle("Show only High + Critical risk", value=True)

    view = df.sort_values("churn_probability", ascending=False)
    if high_only:
        view = view[view["risk_tier"].isin(["High", "Critical"])]

    st.dataframe(
        view[
            [
                "customerID",
                "churn_probability",
                "predicted_churn",
                "risk_tier",
                "Contract",
                "tenure",
                "PaymentMethod",
                "MonthlyCharges",
                "Churn",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download scored CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="scored_customers.csv",
        mime="text/csv",
    )


def tab_lookup(df: pd.DataFrame) -> None:
    st.subheader("Customer lookup")
    ids = df["customerID"].tolist()
    selected = st.selectbox("Customer ID", ids, index=0)
    row = df[df["customerID"] == selected].iloc[0]

    prob = float(row["churn_probability"])
    tier = row["risk_tier"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Churn probability", f"{prob:.1%}")
    c2.metric("Risk tier", tier)
    c3.metric("Predicted churn", row["predicted_churn"])

    hints = customer_risk_hints(row)
    if hints:
        st.markdown("**Why this customer may be at risk**")
        for h in hints:
            st.markdown(f"- {h}")

    actions = rule_based_recommendations(row)
    st.markdown(format_rules_as_markdown(actions))

    st.markdown("---")
    gemini_key = st.session_state.get("gemini_api_key") or ""
    if st.button("Generate recommendation (Gemini)", type="primary"):
        try:
            with st.spinner("Calling Gemini…"):
                text = polish_with_gemini(row, prob, tier, actions, api_key=gemini_key or None)
            st.markdown("**AI retention plan**")
            st.markdown(text)
        except Exception as e:
            st.warning(f"Gemini unavailable ({e}). Showing rule-based plan only.")
            st.markdown(format_rules_as_markdown(actions))


def main() -> None:
    st.title("Customer Churn Prediction Agent")
    st.caption("Telco churn classification, risk tiers, and retention recommendations")

    with st.sidebar:
        st.header("Settings")
        if "gemini_api_key" not in st.session_state:
            st.session_state["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", "")
        st.session_state["gemini_api_key"] = st.text_input(
            "Gemini API key",
            value=st.session_state["gemini_api_key"],
            type="password",
            help="Optional. Falls back to rules-only if empty or call fails.",
        )

    df = load_scored()
    metrics = load_metrics()

    tab1, tab2, tab3 = st.tabs(["Overview", "Scoring & high risk", "Customer lookup"])
    with tab1:
        tab_overview(df, metrics)
    with tab2:
        tab_scoring(df)
    with tab3:
        tab_lookup(df)


if __name__ == "__main__":
    main()
