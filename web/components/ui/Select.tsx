interface SelectProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}

export function Select({ label, value, options, onChange }: SelectProps) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-slate-500">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-white/10 bg-slate-900/80 px-3 py-2.5 font-mono text-sm text-slate-100 shadow-inner focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
      >
        {options.map((id) => (
          <option key={id} value={id} className="bg-slate-900">
            {id}
          </option>
        ))}
      </select>
    </label>
  );
}
