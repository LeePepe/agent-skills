import * as React from "react";
import { cn } from "./utils";

// ============================================================================
//  Design-language components. ONE set of names/roles/rules, seed-themed.
//  Elevation = luminance tiers (L0 bg < L1 card < L2 inner) + 1px border.
// ============================================================================

// MARK: Card (L1) + CardInner (L2)

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "bg-card border border-border rounded-[var(--radius-card)] p-5",
        className,
      )}
      {...props}
    />
  );
}

export function CardInner({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "bg-inner border border-border rounded-[var(--radius-inner)] p-4",
        className,
      )}
      {...props}
    />
  );
}

// MARK: Metric — tabular number + label, ≥3 type levels rule

export function Metric({
  value,
  label,
  delta,
  className,
}: {
  value: React.ReactNode;
  label?: React.ReactNode;
  delta?: { value: string; positive: boolean };
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <span className="num text-[26px] font-semibold leading-none">{value}</span>
      <div className="flex items-center gap-2">
        {label ? <span className="text-text-2 text-xs">{label}</span> : null}
        {delta ? (
          <span
            className="num text-xs font-medium"
            style={{ color: delta.positive ? "var(--success)" : "var(--danger)" }}
          >
            {delta.positive ? "▲" : "▼"} {delta.value}
          </span>
        ) : null}
      </div>
    </div>
  );
}

// MARK: Sparkline — area+line, data-viz next to the number

export function Sparkline({
  data,
  width = 120,
  height = 36,
  color = "var(--chart-1)",
}: {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}) {
  if (data.length < 2) return <svg width={width} height={height} />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const step = width / (data.length - 1);
  const pts = data.map((d, i) => [i * step, height - ((d - min) / span) * height]);
  const line = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  const id = React.useId();
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

// MARK: RingGauge — ratio as an arc

export function RingGauge({
  value,
  size = 56,
  stroke = 6,
  color = "var(--primary)",
  label,
}: {
  value: number; // 0..1
  size?: number;
  stroke?: number;
  color?: string;
  label?: React.ReactNode;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.min(1, Math.max(0, value));
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - clamped)}
        />
      </svg>
      <span className="num absolute text-xs font-semibold">
        {label ?? `${Math.round(clamped * 100)}%`}
      </span>
    </div>
  );
}

// MARK: StatusPill — colored pill, never grey text

type PillTone = "primary" | "success" | "warning" | "danger" | "neutral";

const TONE_VAR: Record<PillTone, string> = {
  primary: "--primary",
  success: "--success",
  warning: "--warning",
  danger: "--danger",
  neutral: "--text-3",
};

export function StatusPill({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: PillTone;
  className?: string;
}) {
  const v = TONE_VAR[tone];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        className,
      )}
      style={{ background: `color-mix(in srgb, var(${v}) 16%, transparent)`, color: `var(${v})` }}
    >
      {children}
    </span>
  );
}

// MARK: SectionHeader

export function SectionHeader({
  icon,
  children,
}: {
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 text-text-2">
      {icon}
      <span className="text-xs font-semibold uppercase tracking-wide">{children}</span>
    </div>
  );
}
