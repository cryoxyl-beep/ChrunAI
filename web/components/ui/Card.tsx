import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
}

export function Card({ children, className = "", title, subtitle }: CardProps) {
  return (
    <section
      className={`rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-[0_8px_32px_rgba(0,0,0,0.35)] backdrop-blur-md transition hover:-translate-y-0.5 hover:border-cyan-500/20 hover:shadow-[0_12px_40px_rgba(34,211,238,0.08)] ${className}`}
    >
      {(title || subtitle) && (
        <header className="mb-4">
          {title && (
            <h3 className="font-serif text-lg text-slate-100">{title}</h3>
          )}
          {subtitle && (
            <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
          )}
        </header>
      )}
      {children}
    </section>
  );
}
