interface StatTileProps {
  label: string;
  value: string;
  hint?: string;
}

export function StatTile({ label, value, hint }: StatTileProps) {
  return (
    <div
      className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-white/[0.02] px-5 py-4 backdrop-blur-sm"
    >
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <p className="mt-2 font-sans text-3xl font-semibold tabular-nums text-slate-50">
        {value}
      </p>
      {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
