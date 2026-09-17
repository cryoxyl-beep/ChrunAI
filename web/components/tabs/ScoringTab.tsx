"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { customersToCsv } from "@/lib/data";
import type { ScoredCustomer } from "@/lib/types";

interface ScoringTabProps {
  customers: ScoredCustomer[];
}

export function ScoringTab({ customers }: ScoringTabProps) {
  const [highOnly, setHighOnly] = useState(true);

  const rows = useMemo(() => {
    let view = [...customers].sort(
      (a, b) => b.churn_probability - a.churn_probability
    );
    if (highOnly) {
      view = view.filter((c) =>
        c.risk_tier === "High" || c.risk_tier === "Critical"
      );
    }
    return view;
  }, [customers, highOnly]);

  function downloadCsv() {
    const blob = new Blob([customersToCsv(customers)], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scored_customers.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <Card
        title="Scored portfolio"
        subtitle={`Showing ${rows.length.toLocaleString()} of ${customers.length.toLocaleString()} customers`}
      >
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={highOnly}
              onChange={(e) => setHighOnly(e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900 text-cyan-500 focus:ring-cyan-500/40"
            />
            High + Critical only
          </label>
          <Button variant="ghost" onClick={downloadCsv}>
            Download full CSV
          </Button>
        </div>
        <DataTable rows={rows} />
      </Card>
    </div>
  );
}
