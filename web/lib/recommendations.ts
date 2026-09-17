/**
 * Rule-based retention logic — port of recommend.py.
 * Keep behavior aligned with Python for Streamlit parity.
 */

import type { RetentionAction, ScoredCustomer } from "./types";

type HintFn = (row: ScoredCustomer) => string | null;

function hintContract(row: ScoredCustomer): string | null {
  if (row.Contract === "Month-to-month") {
    return "Month-to-month contract (higher churn risk)";
  }
  return null;
}

function hintPayment(row: ScoredCustomer): string | null {
  if (row.PaymentMethod === "Electronic check") {
    return "Electronic check payment (often linked to churn)";
  }
  return null;
}

function hintTenure(row: ScoredCustomer): string | null {
  const tenure = row.tenure;
  if (tenure != null && tenure < 12) {
    return `Short tenure (${tenure} months)`;
  }
  return null;
}

function hintFiberAddons(row: ScoredCustomer): string | null {
  if (row.InternetService === "Fiber optic") {
    const sec = row.OnlineSecurity;
    const tech = row.TechSupport;
    if (
      sec === "No" ||
      sec === "No internet service" ||
      tech === "No" ||
      tech === "No internet service"
    ) {
      return "Fiber customer without security/tech support add-ons";
    }
  }
  return null;
}

function hintCharges(row: ScoredCustomer): string | null {
  const charges = row.MonthlyCharges;
  if (charges != null && charges > 70) {
    return `High monthly charges ($${charges.toFixed(2)})`;
  }
  return null;
}

const RISKY_VALUE_CHECKS: HintFn[] = [
  hintContract,
  hintPayment,
  hintTenure,
  hintFiberAddons,
  hintCharges,
];

export function customerRiskHints(row: ScoredCustomer): string[] {
  const hints: string[] = [];
  for (const check of RISKY_VALUE_CHECKS) {
    const msg = check(row);
    if (msg) hints.push(msg);
  }
  return hints;
}

export function ruleBasedRecommendations(row: ScoredCustomer): RetentionAction[] {
  const actions: RetentionAction[] = [];

  if (row.Contract === "Month-to-month") {
    actions.push({
      priority: 1,
      action:
        "Offer a discounted annual or two-year contract with loyalty perks.",
      rationale:
        "Month-to-month subscribers churn more often without a commitment incentive.",
      feature: "Contract",
    });
  }

  if (row.PaymentMethod === "Electronic check") {
    actions.push({
      priority: 2,
      action:
        "Migrate to automatic bank/card payment with a one-time bill credit.",
      rationale: "Electronic check payers show higher churn in telco datasets.",
      feature: "PaymentMethod",
    });
  }

  const tenure = row.tenure ?? 0;
  if (tenure < 12) {
    actions.push({
      priority: 2,
      action:
        "Schedule an onboarding wellness call and highlight value-add services.",
      rationale: `Customer tenure is only ${tenure} months — early lifecycle is critical.`,
      feature: "tenure",
    });
  }

  if (row.InternetService === "Fiber optic") {
    const sec = row.OnlineSecurity;
    const tech = row.TechSupport;
    if (
      sec === "No" ||
      sec === "No internet service" ||
      tech === "No" ||
      tech === "No internet service"
    ) {
      actions.push({
        priority: 3,
        action:
          "Bundle Online Security and Tech Support at a promotional rate.",
        rationale:
          "Fiber customers without support add-ons are more likely to leave.",
        feature: "InternetService",
      });
    }
  }

  const charges = row.MonthlyCharges ?? 0;
  if (charges > 70) {
    actions.push({
      priority: 3,
      action:
        "Review plan fit and offer a tailored downgrade or loyalty discount.",
      rationale: `Monthly charges are $${charges.toFixed(2)}, which may drive price-sensitive churn.`,
      feature: "MonthlyCharges",
    });
  }

  if (actions.length === 0) {
    actions.push({
      priority: 3,
      action:
        "Send a proactive satisfaction survey and personalized retention offer.",
      rationale:
        "No single dominant rule fired; general retention outreach is appropriate.",
      feature: "general",
    });
  }

  actions.sort((a, b) => a.priority - b.priority);
  return actions;
}

export function formatRulesAsMarkdown(actions: RetentionAction[]): string {
  const lines = ["**Retention actions (rule-based):**"];
  actions.forEach((a, i) => {
    lines.push(`${i + 1}. **${a.action}** — _${a.rationale}_`);
  });
  return lines.join("\n");
}

export function decodeImportanceLabel(encodedName: string): string {
  let name = encodedName.replace("num__", "").replace("cat__", "");
  if (name.startsWith("Contract_")) return "Contract type";
  if (name.startsWith("PaymentMethod_")) return "Payment method";
  if (name === "tenure") return "Tenure (months)";
  if (name === "MonthlyCharges") return "Monthly charges";
  if (name === "TotalCharges") return "Total charges";
  if (name.startsWith("InternetService_")) return "Internet service";
  if (name.startsWith("OnlineSecurity_")) return "Online security";
  return name.replace(/_/g, " ");
}
