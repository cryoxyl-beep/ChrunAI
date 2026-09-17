import { TierBadge } from "./TierBadge";
import type { ScoredCustomer } from "@/lib/types";

interface DataTableProps {
  rows: ScoredCustomer[];
}

export function DataTable({ rows }: DataTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-white/10">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-white/10 bg-white/[0.03] text-xs uppercase tracking-wider text-slate-500">
          <tr>
            <th className="px-4 py-3">Customer</th>
            <th className="px-4 py-3">Probability</th>
            <th className="px-4 py-3">Tier</th>
            <th className="px-4 py-3">Predicted</th>
            <th className="px-4 py-3">Contract</th>
            <th className="px-4 py-3">Tenure</th>
            <th className="px-4 py-3">Actual</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.customerID}
              className="border-b border-white/5 transition hover:bg-cyan-500/[0.04]"
            >
              <td className="px-4 py-2.5 font-mono text-xs text-cyan-100/90">
                {row.customerID}
              </td>
              <td className="px-4 py-2.5">
                <div className="flex min-w-[120px] items-center gap-2">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-400"
                      style={{
                        width: `${Math.min(100, row.churn_probability * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="w-12 text-right tabular-nums text-slate-300">
                    {(row.churn_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </td>
              <td className="px-4 py-2.5">
                <TierBadge tier={row.risk_tier} />
              </td>
              <td className="px-4 py-2.5 text-slate-300">{row.predicted_churn}</td>
              <td className="px-4 py-2.5 text-slate-400">{row.Contract}</td>
              <td className="px-4 py-2.5 tabular-nums text-slate-400">
                {row.tenure}
              </td>
              <td className="px-4 py-2.5 text-slate-400">{row.Churn}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <p className="px-4 py-8 text-center text-sm text-slate-500">
          No customers match this filter.
        </p>
      )}
    </div>
  );
}
