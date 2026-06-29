// ui.jsx — themed building blocks. Colors come from CSS variables (see
// index.css / tailwind.config.js) so every piece adapts to light/dark.
import React from "react";

export function Card({ className = "", glow = false, children }) {
  return (
    <div
      className={
        "bg-surface rounded-2xl border border-hair shadow-card " +
        (glow ? "shadow-glow-soft " : "") +
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
    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-150 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed select-none titlebar-no-drag";
  const variants = {
    // Primary = the Tron glow action.
    primary:
      "bg-accent text-ink-inv hover:bg-accent-2 active:bg-accent-press active:scale-[0.99] shadow-glow",
    soft: "bg-accent-soft text-accent hover:shadow-glow-sm",
    subtle: "bg-surface-3 text-ink hover:bg-surface-2 border border-hair",
    ghost: "bg-transparent text-ink-2 hover:bg-surface-3 hover:text-ink",
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
    <div className="inline-flex bg-surface-3 rounded-xl p-1 gap-1 titlebar-no-drag border border-hair">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={
              "px-4 py-1.5 text-sm font-medium rounded-lg transition-all duration-150 " +
              (active
                ? "bg-surface text-ink shadow-glow-sm"
                : "text-ink-3 hover:text-ink-2")
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
        className={`text-[2rem] leading-none font-medium tabular-nums ${tones[tone]}`}
      >
        {value}
      </span>
      <span className="text-xs font-medium text-ink-3 mt-1.5 uppercase tracking-wide">
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
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

// A small status dot used in the sidebar / lists.
export function Dot({ tone = "accent", glow = false }) {
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
      className={`inline-block w-1.5 h-1.5 rounded-full ${tones[tone]} ${
        glow ? "shadow-glow-soft" : ""
      }`}
    />
  );
}
