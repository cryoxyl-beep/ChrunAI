"""Rule-based retention actions + optional Gemini polish."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd


def _hint_contract(row: pd.Series) -> str | None:
    if row.get("Contract") == "Month-to-month":
        return "Month-to-month contract (higher churn risk)"
    return None


def _hint_payment(row: pd.Series) -> str | None:
    if row.get("PaymentMethod") == "Electronic check":
        return "Electronic check payment (often linked to churn)"
    return None


def _hint_tenure(row: pd.Series) -> str | None:
    tenure = row.get("tenure")
    if tenure is not None and float(tenure) < 12:
        return f"Short tenure ({int(tenure)} months)"
    return None


def _hint_fiber_addons(row: pd.Series) -> str | None:
    if row.get("InternetService") == "Fiber optic":
        sec = row.get("OnlineSecurity")
        tech = row.get("TechSupport")
        if sec in ("No", "No internet service") or tech in ("No", "No internet service"):
            return "Fiber customer without security/tech support add-ons"
    return None


def _hint_charges(row: pd.Series) -> str | None:
    charges = row.get("MonthlyCharges")
    if charges is not None and float(charges) > 70:
        return f"High monthly charges (${float(charges):.2f})"
    return None


RISKY_VALUE_CHECKS = [
    _hint_contract,
    _hint_payment,
    _hint_tenure,
    _hint_fiber_addons,
    _hint_charges,
]


def rule_based_recommendations(row: pd.Series) -> list[dict[str, Any]]:
    """Return structured retention actions from business rules."""
    actions: list[dict[str, Any]] = []

    if row.get("Contract") == "Month-to-month":
        actions.append(
            {
                "priority": 1,
                "action": "Offer a discounted annual or two-year contract with loyalty perks.",
                "rationale": "Month-to-month subscribers churn more often without a commitment incentive.",
                "feature": "Contract",
            }
        )

    if row.get("PaymentMethod") == "Electronic check":
        actions.append(
            {
                "priority": 2,
                "action": "Migrate to automatic bank/card payment with a one-time bill credit.",
                "rationale": "Electronic check payers show higher churn in telco datasets.",
                "feature": "PaymentMethod",
            }
        )

    tenure = float(row.get("tenure", 0))
    if tenure < 12:
        actions.append(
            {
                "priority": 2,
                "action": "Schedule an onboarding wellness call and highlight value-add services.",
                "rationale": f"Customer tenure is only {int(tenure)} months — early lifecycle is critical.",
                "feature": "tenure",
            }
        )

    if row.get("InternetService") == "Fiber optic":
        sec = row.get("OnlineSecurity")
        tech = row.get("TechSupport")
        if sec in ("No", "No internet service") or tech in ("No", "No internet service"):
            actions.append(
                {
                    "priority": 3,
                    "action": "Bundle Online Security and Tech Support at a promotional rate.",
                    "rationale": "Fiber customers without support add-ons are more likely to leave.",
                    "feature": "InternetService",
                }
            )

    charges = float(row.get("MonthlyCharges", 0))
    if charges > 70:
        actions.append(
            {
                "priority": 3,
                "action": "Review plan fit and offer a tailored downgrade or loyalty discount.",
                "rationale": f"Monthly charges are ${charges:.2f}, which may drive price-sensitive churn.",
                "feature": "MonthlyCharges",
            }
        )

    if not actions:
        actions.append(
            {
                "priority": 3,
                "action": "Send a proactive satisfaction survey and personalized retention offer.",
                "rationale": "No single dominant rule fired; general retention outreach is appropriate.",
                "feature": "general",
            }
        )

    actions.sort(key=lambda x: x["priority"])
    return actions


def format_rules_as_markdown(actions: list[dict[str, Any]]) -> str:
    lines = ["**Retention actions (rule-based):**"]
    for i, a in enumerate(actions, start=1):
        lines.append(f"{i}. **{a['action']}** — _{a['rationale']}_")
    return "\n".join(lines)


def customer_risk_hints(row: pd.Series) -> list[str]:
    hints: list[str] = []
    for check in RISKY_VALUE_CHECKS:
        msg = check(row)
        if msg:
            hints.append(msg)
    return hints


def decode_importance_label(encoded_name: str) -> str:
    """Turn sklearn feature name into a short label."""
    name = encoded_name.replace("num__", "").replace("cat__", "")
    if name.startswith("Contract_"):
        return "Contract type"
    if name.startswith("PaymentMethod_"):
        return "Payment method"
    if name == "tenure":
        return "Tenure (months)"
    if name == "MonthlyCharges":
        return "Monthly charges"
    if name == "TotalCharges":
        return "Total charges"
    if name.startswith("InternetService_"):
        return "Internet service"
    if name.startswith("OnlineSecurity_"):
        return "Online security"
    return name.replace("_", " ")


def polish_with_gemini(
    row: pd.Series,
    probability: float,
    tier: str,
    actions: list[dict[str, Any]],
    api_key: str | None = None,
) -> str:
    """Single-shot Gemini call; raises on failure so caller can fall back."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")

    import google.generativeai as genai

    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-3.6-flash")

    rules_text = "\n".join(
        f"- [{a['priority']}] {a['action']} ({a['rationale']})" for a in actions
    )
    customer_summary = (
        f"customerID={row.get('customerID')}, Contract={row.get('Contract')}, "
        f"tenure={row.get('tenure')}, PaymentMethod={row.get('PaymentMethod')}, "
        f"InternetService={row.get('InternetService')}, "
        f"MonthlyCharges={row.get('MonthlyCharges')}"
    )

    prompt = f"""You are a telco customer retention analyst. Write a short, actionable retention plan (4-6 bullet points) for this at-risk customer.

Use ONLY these facts (do not invent data):
- Churn probability: {probability:.1%}
- Risk tier: {tier}
- Customer: {customer_summary}
- Rule-based actions already identified:
{rules_text}

Tone: professional, specific, suitable for a CRM note. Mention probability and tier once."""

    response = model.generate_content(prompt)
    return response.text.strip()
