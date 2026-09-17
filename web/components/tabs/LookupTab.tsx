"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { TierBadge } from "@/components/ui/TierBadge";
import {
  customerRiskHints,
  ruleBasedRecommendations,
} from "@/lib/recommendations";
import { tierStyles } from "@/lib/theme";
import type { ScoredCustomer } from "@/lib/types";

interface LookupTabProps {
  customers: ScoredCustomer[];
}

function ProbabilityRing({ probability, tier }: { probability: number; tier: ScoredCustomer["risk_tier"] }) {
  const pct = Math.round(probability * 100);
  const color = tierStyles[tier].chart;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference * (1 - probability);

  return (
    <div className="relative mx-auto h-36 w-36">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="10"
        />
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold tabular-nums text-slate-50">
          {pct}%
        </span>
        <span className="text-xs text-slate-500">churn risk</span>
      </div>
    </div>
  );
}

export function LookupTab({ customers }: LookupTabProps) {
  const ids = useMemo(() => customers.map((c) => c.customerID), [customers]);
  const [selectedId, setSelectedId] = useState(ids[0] ?? "");
  const [geminiText, setGeminiText] = useState<string | null>(null);
  const [geminiError, setGeminiError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const customer = useMemo(
    () => customers.find((c) => c.customerID === selectedId),
    [customers, selectedId]
  );

  if (!customer) {
    return (
      <p className="text-slate-500">No customers loaded. Run python train.py.</p>
    );
  }

  const hints = customerRiskHints(customer);
  const actions = ruleBasedRecommendations(customer);

  async function generateGemini() {
    setLoading(true);
    setGeminiError(null);
    setGeminiText(null);
    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer, actions }),
      });
      const data = (await res.json()) as { text?: string; error?: string };
      if (!res.ok) {
        throw new Error(data.error ?? `Request failed (${res.status})`);
      }
      setGeminiText(data.text ?? "");
    } catch (e) {
      setGeminiError(
        e instanceof Error ? e.message : "Gemini unavailable — rules shown below."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(240px,280px)_1fr] animate-in fade-in duration-300">
      <Card title="Find customer">
        <Select
          label="Customer ID"
          value={selectedId}
          options={ids}
          onChange={(id) => {
            setSelectedId(id);
            setGeminiText(null);
            setGeminiError(null);
          }}
        />
        <dl className="mt-6 space-y-2 text-sm text-slate-400">
          <div className="flex justify-between gap-2">
            <dt>Contract</dt>
            <dd className="text-slate-200">{customer.Contract}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt>Payment</dt>
            <dd className="text-right text-slate-200">{customer.PaymentMethod}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt>Tenure</dt>
            <dd className="text-slate-200">{customer.tenure} mo</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt>Monthly</dt>
            <dd className="text-slate-200">${customer.MonthlyCharges.toFixed(2)}</dd>
          </div>
        </dl>
      </Card>

      <div className="space-y-6">
        <Card className={customer.risk_tier === "Critical" ? "ring-1 ring-rose-500/30" : ""}>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="text-center sm:text-left">
              <p className="font-serif text-xl text-slate-100">Risk snapshot</p>
              <p className="mt-1 font-mono text-sm text-cyan-200/80">
                {customer.customerID}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <TierBadge tier={customer.risk_tier} />
                <span className="text-sm text-slate-400">
                  Predicted:{" "}
                  <span className="text-slate-200">{customer.predicted_churn}</span>
                  {" · "}
                  Actual:{" "}
                  <span className="text-slate-200">{customer.Churn}</span>
                </span>
              </div>
            </div>
            <ProbabilityRing
              probability={customer.churn_probability}
              tier={customer.risk_tier}
            />
          </div>
        </Card>

        {hints.length > 0 && (
          <Card title="Why at risk" subtitle="Heuristic signals from profile">
            <ul className="space-y-2 text-sm text-slate-300">
              {hints.map((h) => (
                <li key={h} className="flex gap-2">
                  <span className="text-amber-400/80">▸</span>
                  {h}
                </li>
              ))}
            </ul>
          </Card>
        )}

        <Card title="Retention playbook" subtitle="Rule-based actions (priority order)">
          <ul className="space-y-3">
            {actions.map((a) => (
              <li
                key={`${a.feature}-${a.priority}-${a.action.slice(0, 24)}`}
                className="relative rounded-xl border border-white/5 bg-white/[0.02] py-3 pl-4 pr-3"
              >
                <span
                  className="absolute left-0 top-3 bottom-3 w-1 rounded-full bg-gradient-to-b from-cyan-400 to-teal-500"
                  style={{ opacity: a.priority === 1 ? 1 : 0.5 }}
                />
                <p className="text-sm font-medium text-slate-100">{a.action}</p>
                <p className="mt-1 text-xs text-slate-500">{a.rationale}</p>
              </li>
            ))}
          </ul>

          <div className="mt-6 border-t border-white/10 pt-5">
            <Button onClick={generateGemini} loading={loading}>
              Generate recommendation (Gemini)
            </Button>
            {geminiError && (
              <p className="mt-3 text-sm text-amber-200/90">{geminiError}</p>
            )}
            {geminiText && (
              <div
                className="mt-4 rounded-xl border border-cyan-500/20 bg-gradient-to-br from-cyan-950/40 to-slate-900/60 p-4 text-sm leading-relaxed text-slate-200 shadow-[inset_3px_0_0_#22d3ee]"
              >
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-cyan-300/80">
                  AI retention briefing
                </p>
                <div className="whitespace-pre-wrap">{geminiText}</div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
