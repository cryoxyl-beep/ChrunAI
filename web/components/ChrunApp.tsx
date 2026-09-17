"use client";

import { useEffect, useState } from "react";
import { TabNav } from "@/components/ui/TabNav";
import { OverviewTab } from "@/components/tabs/OverviewTab";
import { ScoringTab } from "@/components/tabs/ScoringTab";
import { LookupTab } from "@/components/tabs/LookupTab";
import { loadDashboardData } from "@/lib/data";
import type { FeatureImportanceRow, Metrics, ScoredCustomer, TabId } from "@/lib/types";

export function ChrunApp() {
  const [tab, setTab] = useState<TabId>("overview");
  const [customers, setCustomers] = useState<ScoredCustomer[] | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [importance, setImportance] = useState<FeatureImportanceRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData()
      .then((data) => {
        setCustomers(data.customers);
        setMetrics(data.metrics);
        setImportance(data.importance);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load data");
      });
  }, []);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <header className="sticky top-0 z-20 -mx-4 mb-8 border-b border-white/5 bg-[#0b0f1a]/80 px-4 py-4 backdrop-blur-xl sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="font-serif text-2xl tracking-tight text-slate-50 sm:text-3xl">
              Chrun<span className="text-cyan-300">AI</span>
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Telco churn signals · risk tiers · retention cockpit
            </p>
          </div>
          <TabNav active={tab} onChange={setTab} />
        </div>
      </header>

      {error && (
        <div
          className="rounded-xl border border-rose-500/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-100"
          role="alert"
        >
          {error}
        </div>
      )}

      {!customers && !error && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-2xl border border-white/5 bg-white/[0.03]"
            />
          ))}
        </div>
      )}

      {customers && metrics && (
        <main className="min-h-[480px]">
          {tab === "overview" && (
            <OverviewTab
              customers={customers}
              metrics={metrics}
              importance={importance}
            />
          )}
          {tab === "scoring" && <ScoringTab customers={customers} />}
          {tab === "lookup" && <LookupTab customers={customers} />}
        </main>
      )}
    </div>
  );
}
