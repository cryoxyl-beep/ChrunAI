import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "ghost";
  loading?: boolean;
}

export function Button({
  children,
  variant = "primary",
  loading,
  className = "",
  disabled,
  ...rest
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400 disabled:cursor-not-allowed disabled:opacity-50";
  const variants = {
    primary:
      "border border-cyan-400/40 bg-gradient-to-r from-cyan-500/15 to-teal-500/15 text-cyan-50 shadow-[0_0_24px_rgba(34,211,238,0.15)] hover:border-cyan-300/60 hover:shadow-[0_0_32px_rgba(34,211,238,0.25)]",
    ghost:
      "border border-white/10 bg-white/5 text-slate-200 hover:bg-white/10",
  };

  return (
    <button
      type="button"
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-300/30 border-t-cyan-300"
          aria-hidden
        />
      )}
      {children}
    </button>
  );
}
