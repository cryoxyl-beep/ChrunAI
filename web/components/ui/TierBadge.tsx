import { tierStyles } from "@/lib/theme";
import type { RiskTier } from "@/lib/types";

interface TierBadgeProps {
  tier: RiskTier;
  className?: string;
}

export function TierBadge({ tier, className = "" }: TierBadgeProps) {
  const style = tierStyles[tier];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${style.badge} ${style.glow ?? ""} ${className}`}
    >
      {style.label}
    </span>
  );
}
