import type { RiskTier } from "./types";

/** Midnight signal palette — shared by Tailwind classes and Recharts. */

export const tierStyles: Record<
  RiskTier,
  { label: string; badge: string; chart: string; glow?: string }
> = {
  Low: {
    label: "Low",
    badge:
      "bg-emerald-950/80 text-emerald-300/90 border border-emerald-800/60",
    chart: "#6ee7b7",
  },
  Medium: {
    label: "Medium",
    badge:
      "bg-amber-950/40 text-amber-200 border border-amber-500/50 border-dashed",
    chart: "#fbbf24",
  },
  High: {
    label: "High",
    badge: "bg-orange-600/90 text-orange-50 border border-orange-400/40",
    chart: "#fb923c",
  },
  Critical: {
    label: "Critical",
    badge:
      "bg-rose-600/90 text-rose-50 border border-rose-400/50 shadow-[0_0_20px_rgba(244,63,94,0.35)]",
    glow: "animate-tier-pulse",
    chart: "#fb7185",
  },
};

export const chartTheme = {
  grid: "rgba(148, 163, 184, 0.12)",
  axis: "rgba(148, 163, 184, 0.45)",
  barPrimary: "#22d3ee",
  barSecondary: "#2dd4bf",
  tooltipBg: "rgba(15, 23, 42, 0.92)",
  tooltipBorder: "rgba(255, 255, 255, 0.1)",
};

export const tenureBinLabels = ["0–12", "13–24", "25–48", "49+"] as const;
