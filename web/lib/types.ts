/** Shared types for ChrunAI web UI. Keep in sync with recommend.py / scored export. */

export type RiskTier = "Low" | "Medium" | "High" | "Critical";

export interface ScoredCustomer {
  customerID: string;
  Contract: string;
  PaymentMethod: string;
  tenure: number;
  InternetService: string;
  OnlineSecurity: string;
  TechSupport: string;
  MonthlyCharges: number;
  Churn: string;
  churn_probability: number;
  predicted_churn: string;
  risk_tier: RiskTier;
}

export interface Metrics {
  accuracy: number;
  roc_auc: number;
  confusion_matrix: number[][];
  train_rows: number;
  test_rows: number;
  churn_rate: number;
}

export interface FeatureImportanceRow {
  feature: string;
  importance: number;
}

export interface RetentionAction {
  priority: number;
  action: string;
  rationale: string;
  feature: string;
}

export type TabId = "overview" | "scoring" | "lookup";

export interface RecommendRequestBody {
  customer: ScoredCustomer;
  actions: RetentionAction[];
}
