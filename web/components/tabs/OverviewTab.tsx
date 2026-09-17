"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import {
  churnRateByContract,
  churnRateByTenure,
  countHighRisk,
} from "@/lib/data";
import { decodeImportanceLabel } from "@/lib/recommendations";
import { chartTheme } from "@/lib/theme";
import type { FeatureImportanceRow, Metrics, ScoredCustomer } from "@/lib/types";

interface OverviewTabProps {
  customers: ScoredCustomer[];
  metrics: Metrics;
  importance: FeatureImportanceRow[];
}

function DarkTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const val = payload[0].value;
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-xl"
      style={{
        background: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
      }}
    >
      <p className="text-slate-400">{label}</p>
      <p className="font-semibold text-cyan-200">{(val * 100).toFixed(1)}%</p>
    </div>
  );
}

export function OverviewTab({
  customers,
  metrics,
  importance,
}: OverviewTabProps) {
  const historicalChurn =
    customers.filter((c) => c.Churn === "Yes").length / customers.length;
  const byContract = churnRateByContract(customers);
  const byTenure = churnRateByTenure(customers);
  const topImportance = importance
    .slice(0, 12)
    .map((row) => ({
      label: decodeImportanceLabel(row.feature),
      importance: row.importance,
      full: row.feature,
    }))
    .reverse();

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Customers scored"
          value={customers.length.toLocaleString()}
        />
        <StatTile
          label="Historical churn"
          value={`${(historicalChurn * 100).toFixed(1)}%`}
        />
        <StatTile
          label="Model ROC-AUC"
          value={metrics.roc_auc ? metrics.roc_auc.toFixed(3) : "—"}
          hint={
            metrics.accuracy
              ? `Holdout accuracy ${metrics.accuracy.toFixed(3)}`
              : undefined
          }
        />
        <StatTile
          label="High + critical"
          value={countHighRisk(customers).toLocaleString()}
          hint="Flagged for retention outreach"
        />
      </div>

      {metrics.train_rows && (
        <p className="text-sm text-slate-500">
          Train / test split:{" "}
          <span className="text-slate-400">
            {metrics.train_rows.toLocaleString()} /{" "}
            {metrics.test_rows?.toLocaleString()} rows
          </span>
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Churn by contract" subtitle="Historical rate in dataset">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byContract} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid stroke={chartTheme.grid} vertical={false} />
                <XAxis
                  dataKey="contract"
                  tick={{ fill: chartTheme.axis, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  tick={{ fill: chartTheme.axis, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                />
                <Tooltip content={<DarkTooltip />} />
                <Bar
                  dataKey="churn_rate"
                  fill={chartTheme.barPrimary}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Churn by tenure" subtitle="Months on service (binned)">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byTenure} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid stroke={chartTheme.grid} vertical={false} />
                <XAxis
                  dataKey="bin"
                  tick={{ fill: chartTheme.axis, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  tick={{ fill: chartTheme.axis, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                />
                <Tooltip content={<DarkTooltip />} />
                <Bar
                  dataKey="churn_rate"
                  fill={chartTheme.barSecondary}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {topImportance.length > 0 && (
        <Card
          title="Feature importance"
          subtitle="Random Forest — top encoded drivers"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={topImportance}
                margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
              >
                <CartesianGrid stroke={chartTheme.grid} horizontal={false} />
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="label"
                  width={120}
                  tick={{ fill: chartTheme.axis, fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0].payload as {
                      label: string;
                      importance: number;
                      full: string;
                    };
                    return (
                      <div
                        className="rounded-lg border px-3 py-2 text-xs"
                        style={{
                          background: chartTheme.tooltipBg,
                          borderColor: chartTheme.tooltipBorder,
                        }}
                      >
                        <p className="text-slate-300">{p.label}</p>
                        <p className="text-slate-500">{p.full}</p>
                        <p className="font-mono text-cyan-200">
                          {p.importance.toFixed(4)}
                        </p>
                      </div>
                    );
                  }}
                />
                <Bar
                  dataKey="importance"
                  fill={chartTheme.barPrimary}
                  radius={[0, 6, 6, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}
