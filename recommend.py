"""Rule-based retention actions + optional Gemini polish (dataset-aware)."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd


def _get(row: pd.Series, *names: str):
    for n in names:
        if n in row.index and pd.notna(row.get(n)):
            return row.get(n)
    # case-insensitive fallback
    lower_map = {str(c).lower(): c for c in row.index}
    for n in names:
        key = n.lower()
        if key in lower_map:
            val = row.get(lower_map[key])
            if pd.notna(val):
                return val
    return None


def customer_risk_hints(row: pd.Series, dataset: str = "telco") -> list[str]:
    if dataset == "telco":
        return _telco_hints(row)
    return _orange_style_hints(row)


def rule_based_recommendations(
    row: pd.Series, dataset: str = "telco"
) -> list[dict[str, Any]]:
    if dataset == "telco":
        return _telco_rules(row)
    return _orange_style_rules(row)


def _telco_hints(row: pd.Series) -> list[str]:
    hints: list[str] = []
    if _get(row, "Contract") == "Month-to-month":
        hints.append("Month-to-month contract (higher churn risk)")
    if _get(row, "PaymentMethod") == "Electronic check":
        hints.append("Electronic check payment (often linked to churn)")
    tenure = _get(row, "tenure")
    if tenure is not None and float(tenure) < 12:
        hints.append(f"Short tenure ({int(tenure)} months)")
    if _get(row, "InternetService") == "Fiber optic":
        sec = _get(row, "OnlineSecurity")
        tech = _get(row, "TechSupport")
        if sec in ("No", "No internet service") or tech in ("No", "No internet service"):
            hints.append("Fiber customer without security/tech support add-ons")
    charges = _get(row, "MonthlyCharges")
    if charges is not None and float(charges) > 70:
        hints.append(f"High monthly charges (${float(charges):.2f})")
    return hints


def _telco_rules(row: pd.Series) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if _get(row, "Contract") == "Month-to-month":
        actions.append(
            {
                "priority": 1,
                "action": "Offer a discounted annual or two-year contract with loyalty perks.",
                "rationale": "Month-to-month subscribers churn more often without a commitment incentive.",
                "feature": "Contract",
            }
        )
    if _get(row, "PaymentMethod") == "Electronic check":
        actions.append(
            {
                "priority": 2,
                "action": "Migrate to automatic bank/card payment with a one-time bill credit.",
                "rationale": "Electronic check payers show higher churn in telco datasets.",
                "feature": "PaymentMethod",
            }
        )
    tenure = _get(row, "tenure")
    if tenure is not None and float(tenure) < 12:
        actions.append(
            {
                "priority": 2,
                "action": "Schedule an onboarding wellness call and highlight value-add services.",
                "rationale": f"Customer tenure is only {int(tenure)} months — early lifecycle is critical.",
                "feature": "tenure",
            }
        )
    if _get(row, "InternetService") == "Fiber optic":
        sec = _get(row, "OnlineSecurity")
        tech = _get(row, "TechSupport")
        if sec in ("No", "No internet service") or tech in ("No", "No internet service"):
            actions.append(
                {
                    "priority": 3,
                    "action": "Bundle Online Security and Tech Support at a promotional rate.",
                    "rationale": "Fiber customers without support add-ons are more likely to leave.",
                    "feature": "InternetService",
                }
            )
    charges = _get(row, "MonthlyCharges")
    if charges is not None and float(charges) > 70:
        actions.append(
            {
                "priority": 3,
                "action": "Review plan fit and offer a tailored downgrade or loyalty discount.",
                "rationale": f"Monthly charges are ${float(charges):.2f}, which may drive price-sensitive churn.",
                "feature": "MonthlyCharges",
            }
        )
    return actions or [_generic_fallback()]


def _norm_yes(val) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().rstrip(".").lower()
    return s in {"yes", "true", "y", "1"}


def _orange_style_hints(row: pd.Series) -> list[str]:
    hints: list[str] = []
    intl = _get(row, "International Plan", "International plan")
    if _norm_yes(intl):
        hints.append("Has international plan (often higher churn risk)")
    vmail = _get(row, "Voice mail Plan", "Voice mail plan")
    if vmail is not None and not _norm_yes(vmail):
        hints.append("No voice mail plan")
    svc = _get(
        row,
        "Number Customer Service calls",
        "Customer service calls",
    )
    if svc is not None and float(svc) >= 3:
        hints.append(f"High customer service calls ({int(float(svc))})")
    day = _get(row, "Total day Charge", "Total day charge")
    if day is not None and float(day) > 40:
        hints.append(f"High daytime charges ({float(day):.2f})")
    acct = _get(row, "Account Length", "Account length")
    if acct is not None and float(acct) < 50:
        hints.append(f"Short account length ({int(float(acct))} days/periods)")
    return hints


def _orange_style_rules(row: pd.Series) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    intl = _get(row, "International Plan", "International plan")
    if _norm_yes(intl):
        actions.append(
            {
                "priority": 1,
                "action": "Audit international plan value and offer a loyalty rate lock.",
                "rationale": "International-plan subscribers churn more often when charges feel high.",
                "feature": "International Plan",
            }
        )
    svc = _get(row, "Number Customer Service calls", "Customer service calls")
    if svc is not None and float(svc) >= 3:
        actions.append(
            {
                "priority": 1,
                "action": "Assign a retention specialist and resolve open support issues within 48h.",
                "rationale": f"Customer has {int(float(svc))} service calls — friction predicts churn.",
                "feature": "Customer service calls",
            }
        )
    vmail = _get(row, "Voice mail Plan", "Voice mail plan")
    if vmail is not None and not _norm_yes(vmail):
        actions.append(
            {
                "priority": 2,
                "action": "Offer a complimentary voice-mail / messaging trial for 1 month.",
                "rationale": "Customers without voice mail show higher churn in Orange/Singtel-style data.",
                "feature": "Voice mail Plan",
            }
        )
    day = _get(row, "Total day Charge", "Total day charge")
    if day is not None and float(day) > 40:
        actions.append(
            {
                "priority": 2,
                "action": "Propose a usage-based day plan or bundled minutes discount.",
                "rationale": f"Daytime charge is {float(day):.2f} — price sensitivity risk.",
                "feature": "Total day Charge",
            }
        )
    acct = _get(row, "Account Length", "Account length")
    if acct is not None and float(acct) < 50:
        actions.append(
            {
                "priority": 3,
                "action": "Run early-lifecycle welcome outreach with onboarding tips.",
                "rationale": f"Account length is only {int(float(acct))} — new customers need nurture.",
                "feature": "Account Length",
            }
        )
    return actions or [_generic_fallback()]


def _generic_fallback() -> dict[str, Any]:
    return {
        "priority": 3,
        "action": "Send a proactive satisfaction survey and personalized retention offer.",
        "rationale": "No single dominant rule fired; general retention outreach is appropriate.",
        "feature": "general",
    }


def format_rules_as_markdown(actions: list[dict[str, Any]]) -> str:
    lines = ["**Retention actions (rule-based):**"]
    for i, a in enumerate(actions, start=1):
        lines.append(f"{i}. **{a['action']}** — _{a['rationale']}_")
    return "\n".join(lines)


def decode_importance_label(encoded_name: str) -> str:
    name = encoded_name.replace("num__", "").replace("cat__", "")
    return name.replace("_", " ")


# Groq model IDs (developer tier) — see https://console.groq.com/docs/models
# Llama 3.1/3.3 IDs were deprecated Aug 2026; use OSS + Qwen instead.
GROQ_RECOMMENDATION_MODELS: dict[str, str] = {
    "GPT OSS 20B (fast)": "openai/gpt-oss-20b",
    "Qwen 3.6 27B": "qwen/qwen3.6-27b",
    "Groq Compound Mini": "groq/compound-mini",
}


def build_retention_prompt(
    row: pd.Series,
    probability: float,
    tier: str,
    actions: list[dict[str, Any]],
    dataset: str = "telco",
) -> str:
    rules_text = "\n".join(
        f"- [{a['priority']}] {a['action']} ({a['rationale']})" for a in actions
    )
    fields = {k: row.get(k) for k in row.index if k not in ("churn_probability",)}
    summary_keys = list(fields.keys())[:12]
    customer_summary = ", ".join(f"{k}={fields[k]}" for k in summary_keys)
    return f"""You are a telecom retention analyst for dataset "{dataset}".
Write a short actionable retention plan (4-6 bullets).

Facts only (do not invent):
- Churn probability: {probability:.1%}
- Risk tier: {tier}
- Customer snapshot: {customer_summary}
- Rule-based actions:
{rules_text}

Tone: professional CRM note. Mention probability and tier once."""


def polish_with_gemini(
    row: pd.Series,
    probability: float,
    tier: str,
    actions: list[dict[str, Any]],
    api_key: str | None = None,
    dataset: str = "telco",
) -> str:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")

    import google.generativeai as genai

    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-3.6-flash")
    prompt = build_retention_prompt(row, probability, tier, actions, dataset)
    response = model.generate_content(prompt)
    return response.text.strip()


def polish_with_groq(
    row: pd.Series,
    probability: float,
    tier: str,
    actions: list[dict[str, Any]],
    model_id: str,
    api_key: str | None = None,
    dataset: str = "telco",
) -> str:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not set")

    from groq import Groq

    client = Groq(api_key=key)
    prompt = build_retention_prompt(row, probability, tier, actions, dataset)
    completion = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1024,
    )
    return (completion.choices[0].message.content or "").strip()


def generate_multi_llm_recommendations(
    row: pd.Series,
    probability: float,
    tier: str,
    actions: list[dict[str, Any]],
    dataset: str,
    gemini_key: str | None,
    groq_key: str | None,
    use_gemini: bool = True,
    groq_model_ids: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Return list of (display_name, text_or_error)."""
    results: list[tuple[str, str]] = []

    if use_gemini and (gemini_key or os.environ.get("GEMINI_API_KEY")):
        try:
            text = polish_with_gemini(
                row, probability, tier, actions, api_key=gemini_key, dataset=dataset
            )
            results.append(("Gemini 3.6 Flash", text))
        except Exception as e:
            results.append(("Gemini 3.6 Flash", f"Error: {e}"))

    if groq_key or os.environ.get("GROQ_API_KEY"):
        ids = groq_model_ids or list(GROQ_RECOMMENDATION_MODELS.values())
        label_by_id = {v: k for k, v in GROQ_RECOMMENDATION_MODELS.items()}
        for model_id in ids:
            label = label_by_id.get(model_id, model_id)
            try:
                text = polish_with_groq(
                    row,
                    probability,
                    tier,
                    actions,
                    model_id=model_id,
                    api_key=groq_key,
                    dataset=dataset,
                )
                results.append((f"Groq · {label}", text))
            except Exception as e:
                results.append((f"Groq · {label}", f"Error: {e}"))

    return results
