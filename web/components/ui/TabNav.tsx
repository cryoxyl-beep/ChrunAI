import type { TabId } from "@/lib/types";

const tabs: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "scoring", label: "Scoring & high risk" },
  { id: "lookup", label: "Customer lookup" },
];

interface TabNavProps {
  active: TabId;
  onChange: (id: TabId) => void;
}

export function TabNav({ active, onChange }: TabNavProps) {
  return (
    <nav
      className="inline-flex rounded-xl border border-white/10 bg-slate-900/60 p-1 backdrop-blur-md"
      role="tablist"
      aria-label="Main sections"
    >
      {tabs.map((tab) => {
        const isActive = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400 ${
              isActive
                ? "bg-gradient-to-r from-cyan-500/20 to-teal-500/20 text-cyan-100 shadow-inner"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
