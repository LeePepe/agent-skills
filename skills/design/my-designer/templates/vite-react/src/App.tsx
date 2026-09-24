import { Card, CardInner, Metric, Sparkline, RingGauge, StatusPill, SectionHeader } from "./shared/components";
import { ThemeControl } from "./shared/ThemeControl";

const trend = [12, 18, 15, 24, 21, 30, 28, 36];

/**
 * Demo dashboard — proves the design language: max content width, independent
 * KPI cards in a grid, data-viz next to numbers, colored pills, ≥3 type levels.
 * Swap the seed (top-right) to re-theme everything.
 */
export function App() {
  return (
    <div className="min-h-dvh bg-bg text-text-1">
      <header className="border-b border-border">
        <div className="content flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="size-6 rounded-[var(--radius-inner)] bg-primary" />
            <span className="font-semibold">Dashboard</span>
            <span className="num text-text-3 text-xs">v1.0.0</span>
          </div>
          <ThemeControl />
        </div>
      </header>

      <main className="content px-6 py-6">
        <SectionHeader>Overview</SectionHeader>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <Metric value="$48,250" label="Balance" delta={{ value: "12.4%", positive: true }} />
            <Sparkline data={trend} color="var(--chart-1)" />
          </Card>
          <Card>
            <Metric value="1,284" label="Active users" delta={{ value: "3.1%", positive: true }} />
            <Sparkline data={[...trend].reverse()} color="var(--chart-3)" />
          </Card>
          <Card>
            <Metric value="$3,910" label="Spend" delta={{ value: "1.8%", positive: false }} />
            <Sparkline data={[8, 14, 10, 20, 16, 12, 18, 9]} color="var(--chart-5)" />
          </Card>
          <Card className="flex items-center justify-between">
            <Metric value="72%" label="Savings goal" />
            <RingGauge value={0.72} />
          </Card>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <SectionHeader>Recent activity</SectionHeader>
            <div className="mt-3 flex flex-col gap-2">
              {[
                { t: "Payment received", s: "success", v: "+$1,200" },
                { t: "Subscription renewed", s: "primary", v: "-$29" },
                { t: "Card declined", s: "danger", v: "$0" },
                { t: "Review pending", s: "warning", v: "—" },
              ].map((r) => (
                <CardInner key={r.t} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <StatusPill tone={r.s as "success" | "primary" | "danger" | "warning"}>
                      {r.s}
                    </StatusPill>
                    <span className="text-sm">{r.t}</span>
                  </div>
                  <span className="num text-sm">{r.v}</span>
                </CardInner>
              ))}
            </div>
          </Card>

          <Card>
            <SectionHeader>Chart palette</SectionHeader>
            <div className="mt-3 flex gap-1.5">
              {Array.from({ length: 8 }, (_, i) => (
                <div key={i} className="flex-1">
                  <div
                    className="h-12 rounded-[var(--radius-inner)]"
                    style={{ background: `var(--chart-${i + 1})` }}
                  />
                  <span className="num text-text-3 mt-1 block text-center text-[10px]">{i + 1}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
