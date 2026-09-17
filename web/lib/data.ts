import type {
  FeatureImportanceRow,
  Metrics,
  ScoredCustomer,
} from "./types";
import { tenureBinLabels } from "./theme";

export async function loadDashboardData(): Promise<{
  customers: ScoredCustomer[];
  metrics: Metrics;
  importance: FeatureImportanceRow[];
}> {
  const [customersRes, metricsRes, importanceRes] = await Promise.all([
    fetch("/data/scored_customers.json"),
    fetch("/data/metrics.json"),
    fetch("/data/feature_importance.json"),
  ]);

  if (!customersRes.ok) {
    throw new Error(
      "Missing scored_customers.json — run `python train.py` from the repo root."
    );
  }

  const customers = (await customersRes.json()) as ScoredCustomer[];
  const metrics = metricsRes.ok
    ? ((await metricsRes.json()) as Metrics)
    : ({} as Metrics);
  const importance = importanceRes.ok
    ? ((await importanceRes.json()) as FeatureImportanceRow[])
    : [];

  return { customers, metrics, importance };
}

export function churnRateByContract(
  customers: ScoredCustomer[]
): { contract: string; churn_rate: number }[] {
  const map = new Map<string, { yes: number; total: number }>();
  for (const c of customers) {
    const entry = map.get(c.Contract) ?? { yes: 0, total: 0 };
    entry.total += 1;
    if (c.Churn === "Yes") entry.yes += 1;
    map.set(c.Contract, entry);
  }
  return Array.from(map.entries()).map(([contract, { yes, total }]) => ({
    contract,
    churn_rate: total ? yes / total : 0,
  }));
}

function tenureBin(tenure: number): string {
  if (tenure <= 12) return tenureBinLabels[0];
  if (tenure <= 24) return tenureBinLabels[1];
  if (tenure <= 48) return tenureBinLabels[2];
  return tenureBinLabels[3];
}

export function churnRateByTenure(
  customers: ScoredCustomer[]
): { bin: string; churn_rate: number }[] {
  const map = new Map<string, { yes: number; total: number }>();
  for (const label of tenureBinLabels) {
    map.set(label, { yes: 0, total: 0 });
  }
  for (const c of customers) {
    const bin = tenureBin(c.tenure);
    const entry = map.get(bin)!;
    entry.total += 1;
    if (c.Churn === "Yes") entry.yes += 1;
  }
  return tenureBinLabels.map((bin) => {
    const { yes, total } = map.get(bin)!;
    return { bin, churn_rate: total ? yes / total : 0 };
  });
}

export function countHighRisk(customers: ScoredCustomer[]): number {
  return customers.filter((c) =>
    c.risk_tier === "High" || c.risk_tier === "Critical"
  ).length;
}

export function customersToCsv(customers: ScoredCustomer[]): string {
  if (customers.length === 0) return "";
  const keys = Object.keys(customers[0]) as (keyof ScoredCustomer)[];
  const header = keys.join(",");
  const rows = customers.map((row) =>
    keys
      .map((k) => {
        const v = row[k];
        const s = String(v);
        return s.includes(",") ? `"${s}"` : s;
      })
      .join(",")
  );
  return [header, ...rows].join("\n");
}
