// ui.jsx — themed building blocks. Colors come from CSS variables (see
// index.css / tailwind.config.js) so every piece adapts to light/dark.
import React from "react";

export function Card({ className = "", glow = false, children }) {
  return (
    <div
      className={
        // Hairline + soft depth; `glow` is accepted for compatibility but no
        // longer adds a halo.
        "bg-surface rounded-2xl border border-hair shadow-card " +
        className
      }
    >
      {children}
    </div>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled = false,
  className = "",
  type = "button",
}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-[9px] px-4 py-2 text-[13.5px] font-medium transition-[background-color,color,box-shadow,transform,filter] duration-150 focus:outline-none focus-visible:shadow-focus disabled:opacity-40 disabled:cursor-not-allowed select-none titlebar-no-drag";
  const variants = {
    primary:
      "bg-accent text-ink-inv font-semibold hover:brightness-[1.06] active:translate-y-px shadow-glow",
    soft: "bg-accent-soft text-accent hover:bg-accent/15",
    subtle: "bg-surface text-ink border border-hair shadow-raise hover:border-hair-strong",
    ghost: "bg-transparent text-ink-2 hover:bg-ink/[0.05] hover:text-ink",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Segmented({ options, value, onChange }) {
  return (
    <div className="inline-flex bg-surface-2 rounded-[9px] p-0.5 gap-0.5 titlebar-no-drag border border-hair">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={
              "px-3.5 py-[5px] text-[12.5px] font-medium rounded-[7px] transition-colors duration-150 " +
              (active
                ? "bg-surface text-ink shadow-raise"
                : "text-ink-2 hover:text-ink")
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export function Stat({ label, value, tone = "default" }) {
  const tones = {
    default: "text-ink",
    accent: "text-accent",
    ok: "text-success",
    warn: "text-warning",
    bad: "text-danger",
    manual: "text-manual",
  };
  return (
    <div className="flex flex-col">
      <span
        className={`text-[1.75rem] leading-none font-semibold tracking-[-0.02em] tabular-nums ${tones[tone]}`}
      >
        {value}
      </span>
      <span className="text-[12px] text-ink-3 mt-1.5">
        {label}
      </span>
    </div>
  );
}

export function Badge({ children, tone = "default" }) {
  const tones = {
    default: "bg-neutral-soft text-ink-2",
    ok: "bg-success-soft text-success",
    warn: "bg-warning-soft text-warning",
    bad: "bg-danger-soft text-danger",
    manual: "bg-manual-soft text-manual",
    accent: "bg-accent-soft text-accent",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11.5px] font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

// A small status dot used in the sidebar / lists.
export function Dot({ tone = "accent" }) {
  const tones = {
    accent: "bg-accent",
    ok: "bg-success",
    warn: "bg-warning",
    bad: "bg-danger",
    manual: "bg-manual",
    idle: "bg-ink-3",
  };
  return (
    <span
      className={`inline-block w-1.5 h-1.5 rounded-full ${tones[tone]}`}
    />
  );
}
