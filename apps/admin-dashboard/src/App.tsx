import axios from "axios";
import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { API_BASE, api } from "./api";

type Overview = {
  app_mode: string;
  primary_region: string;
  dr_region: string;
  active_region: string;
  failover_state: string;
  rto_target_min: number;
  rpo_target_min: number;
  recovery_readiness: number;
};

type SeriesBundle = {
  namespace: string;
  series: Record<string, { t: number; v: number }[]>;
};

const scenarios = [
  { id: "steady", label: "Steady state" },
  { id: "cpu_spike", label: "CPU spike" },
  { id: "request_surge", label: "Request surge" },
  { id: "network_degradation", label: "Network degradation" },
  { id: "instance_unhealthy", label: "Unhealthy instance" },
  { id: "periodic_failure", label: "Periodic pattern" },
];

export default function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [series, setSeries] = useState<SeriesBundle | null>(null);
  const [events, setEvents] = useState<unknown[]>([]);
  const [timeline, setTimeline] = useState<unknown[]>([]);
  const [alerts, setAlerts] = useState<unknown[]>([]);
  const [forecast, setForecast] = useState<number[]>([]);
  const [predLog, setPredLog] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);

  const refresh = useCallback(async () => {
    setApiError(null);
    try {
      const [h, o, s, e, tl, al] = await Promise.all([
        api.get("/health").catch(() => null),
        api.get<Overview>("/admin/overview"),
        api.get<SeriesBundle>("/admin/metrics/series", { params: { minutes: 90 } }),
        api.get("/admin/events"),
        api.get("/admin/timeline"),
        api.get("/admin/anomalies"),
      ]);
      setHealthOk(h !== null && h.data?.status === "ok");
      setOverview(o.data);
      setSeries(s.data);
      setEvents(e.data.events || []);
      setTimeline(tl.data.timeline || []);
      setAlerts(al.data.alerts || []);
      const fc = await api.get("/admin/charts/forecast").catch(() => ({ data: {} }));
      const f = fc.data.forecast as number[] | undefined;
      if (f?.length) setForecast(f.map((v) => (typeof v === "number" ? v : Number(v))));
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setApiError(
          `${err.message} — Open ${API_BASE.replace("/api", "")}/docs and confirm the FastAPI app is running (PYTHONPATH=. python -m uvicorn …).`
        );
      } else {
        setApiError(String(err));
      }
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [refresh]);

  const chartData = () => {
    if (!series?.series) return [];
    const keys = Object.keys(series.series);
    if (!keys.length) return [];
    const len = Math.max(...keys.map((k) => series.series[k].length));
    const rows: Record<string, number | string>[] = [];
    for (let idx = 0; idx < len; idx++) {
      const row: Record<string, number | string> = { i: idx };
      for (const k of keys) {
        const pt = series.series[k][idx];
        if (pt) row[k] = pt.v;
      }
      rows.push(row);
    }
    return rows;
  };

  const runScenario = async (scenario: string) => {
    setLoading(true);
    try {
      await api.post("/admin/scenario", { scenario });
      await refresh();
    } catch (e) {
      setApiError(axios.isAxiosError(e) ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const runPrediction = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/admin/prediction/run");
      setPredLog(JSON.stringify(data, null, 2));
      await refresh();
    } catch (e) {
      setApiError(axios.isAxiosError(e) ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const manualFailover = async () => {
    setLoading(true);
    try {
      await api.post("/admin/failover/manual", { target: "dr", reason: "admin console" });
      await refresh();
    } finally {
      setLoading(false);
    }
  };

  const failback = async () => {
    setLoading(true);
    try {
      await api.post("/admin/failover/manual", { target: "primary", reason: "admin failback" });
      await refresh();
    } finally {
      setLoading(false);
    }
  };

  const data = chartData();
  const active = overview?.active_region || "—";

  return (
    <div className="min-h-screen bg-gradient-to-b from-obsidian-950 via-obsidian-900 to-obsidian-950 text-slate-100">
      <header className="border-b border-white/5 bg-obsidian-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-6">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300/90">StreamVault · Operations</p>
            <h1 className="text-2xl font-bold text-white">Disaster recovery &amp; monitoring</h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-400">
              Live metrics (simulated CloudWatch), ED-LSTM forecast, Route&nbsp;53–style region state, EventBridge events,
              and failover drills — all backed by <code className="text-cyan-300/90">{API_BASE}</code>
            </p>
          </div>
          <div className="flex flex-col items-start gap-2 md:items-end">
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                healthOk ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
              }`}
            >
              API {healthOk === true ? "reachable" : healthOk === false ? "check failed" : "…"}
            </span>
            <span className="text-xs text-slate-500">Polls every 4s</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-8 px-4 py-8 md:px-6">
        {apiError && (
          <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 text-sm text-rose-100">{apiError}</div>
        )}

        {/* Region topology */}
        <section className="rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-cyan-950/40 to-slate-950/40 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-cyan-200">Traffic &amp; regions</h2>
          <p className="mt-1 text-xs text-slate-500">Primary us-west-2 · Standby / DR us-east-1 · Active traffic: {active}</p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <RegionCard
              label="Primary (us-west-2)"
              active={active === "primary"}
              detail="Normal user + API path (simulated ALB in mock mode)"
            />
            <RegionCard
              label="DR / standby (us-east-1)"
              active={active === "dr"}
              detail="Warm standby; receives traffic after failover or ML-driven shift"
            />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={manualFailover}
              className="rounded-full bg-rose-600 px-5 py-2 text-sm font-semibold text-white hover:bg-rose-500 disabled:opacity-40"
            >
              Failover to DR
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={failback}
              className="rounded-full border border-emerald-400/50 px-5 py-2 text-sm text-emerald-200 hover:bg-emerald-500/10 disabled:opacity-40"
            >
              Fail back to primary
            </button>
          </div>
        </section>

        {/* KPI row */}
        {overview && (
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Recovery KPIs</h2>
            <div className="grid gap-4 md:grid-cols-4">
              <Card title="Active region" value={overview.active_region.toUpperCase()} hint="Traffic anchor" accent="text-cyan-300" />
              <Card title="Failover state" value={overview.failover_state} hint="Orchestrator" accent="text-amber-300" />
              <Card title="RTO target" value={`${overview.rto_target_min} min`} hint="Recovery time" accent="text-emerald-300" />
              <Card
                title="Readiness"
                value={`${Math.round(overview.recovery_readiness * 100)}%`}
                hint="Synthetic KPI"
                accent="text-rose-300"
              />
            </div>
          </section>
        )}

        {/* Metrics */}
        <section className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-6 shadow-xl">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Infrastructure metrics</h2>
              <p className="text-sm text-slate-500">CPU, request rate, latency, network, errors — same shape as CloudWatch ingestion</p>
            </div>
            <span className="text-xs text-slate-500">{series?.namespace || "StreamVault/App"}</span>
          </div>
          <div className="h-80 w-full min-h-[280px]">
            {data.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center text-slate-500">
                <p className="text-sm">No metric points yet.</p>
                <p className="max-w-md text-xs">Start the backend — the lifespan task pushes metrics every ~3s. Wait 30 seconds and refresh.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="i" stroke="#64748b" fontSize={11} name="sample" />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
                  <Legend />
                  <Line type="monotone" dataKey="cpu_utilization" name="CPU" stroke="#22d3ee" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="request_rate" name="Req/s" stroke="#a78bfa" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="latency_ms" name="Latency ms" stroke="#fb7185" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="network_mbps" name="Net Mbps" stroke="#34d399" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="error_rate" name="Errors" stroke="#fbbf24" dot={false} strokeWidth={2} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5 lg:col-span-1">
            <h2 className="text-sm font-semibold text-white">Failure simulations</h2>
            <p className="mt-1 text-xs text-slate-500">Feeds the metric generator for DR demos</p>
            <div className="mt-4 flex flex-col gap-2">
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  disabled={loading}
                  onClick={() => runScenario(s.id)}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-sm text-slate-200 hover:border-cyan-400/40 disabled:opacity-40"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5 lg:col-span-1">
            <h2 className="text-sm font-semibold text-white">ML &amp; orchestration</h2>
            <p className="mt-1 text-xs text-slate-500">ED-LSTM window + recovery policy (monitor / warn / failover)</p>
            <button
              type="button"
              disabled={loading}
              onClick={runPrediction}
              className="mt-4 w-full rounded-full bg-cyan-500 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-40"
            >
              Run ED-LSTM + policy
            </button>
            {predLog && (
              <pre className="mt-3 max-h-48 overflow-auto rounded-lg bg-black/50 p-2 text-[10px] leading-relaxed text-slate-300">
                {predLog}
              </pre>
            )}
          </section>

          <section className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5 lg:col-span-1">
            <h2 className="text-sm font-semibold text-white">Error envelope</h2>
            <p className="mt-1 text-xs text-slate-500">Rolling view of application error rate</p>
            <div className="mt-4 h-40">
              {data.length === 0 ? (
                <p className="text-xs text-slate-600">Awaiting metrics…</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data}>
                    <defs>
                      <linearGradient id="errFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#fbbf24" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#fbbf24" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="i" hide />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <Tooltip />
                    <Area type="monotone" dataKey="error_rate" name="error_rate" stroke="#fbbf24" fill="url(#errFill)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </section>
        </div>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5">
            <h2 className="text-sm font-semibold text-white">ED-LSTM forecast (last window)</h2>
            <div className="mt-4 h-52">
              {forecast.length === 0 ? (
                <p className="text-xs text-slate-500">Train `services/ml_predictor/train.py` or run prediction above.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecast.map((v, i) => ({ i, v }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="i" hide />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip />
                    <Line type="monotone" dataKey="v" stroke="#38bdf8" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5">
            <h2 className="text-sm font-semibold text-white">Anomaly alerts</h2>
            <ul className="mt-4 max-h-52 space-y-2 overflow-auto text-xs text-slate-300">
              {alerts.length === 0 && <li className="text-slate-500">No anomalies yet — run a scenario + prediction.</li>}
              {alerts.map((a: unknown, i: number) => {
                const row = a as { message?: string } | Record<string, unknown>;
                const msg = typeof row === "object" && row && "message" in row && typeof row.message === "string" ? row.message : JSON.stringify(a);
                return (
                  <li key={i} className="rounded-lg bg-black/40 px-2 py-1">
                    {msg}
                  </li>
                );
              })}
            </ul>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5">
            <h2 className="text-sm font-semibold text-white">Recovery timeline</h2>
            <ul className="mt-4 max-h-64 space-y-2 overflow-auto font-mono text-[11px] text-slate-400">
              {timeline.length === 0 && <li className="text-slate-600">No events yet.</li>}
              {timeline.slice(-20).map((t: unknown, i: number) => (
                <li key={i}>{JSON.stringify(t)}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-white/10 bg-obsidian-900/50 p-5">
            <h2 className="text-sm font-semibold text-white">Event bus (mock EventBridge)</h2>
            <ul className="mt-4 max-h-64 space-y-2 overflow-auto font-mono text-[11px] text-slate-400">
              {events.length === 0 && <li className="text-slate-600">No events yet.</li>}
              {events.slice(-20).map((t: unknown, i: number) => (
                <li key={i}>{JSON.stringify(t)}</li>
              ))}
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}

function RegionCard({ label, active, detail }: { label: string; active: boolean; detail: string }) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        active ? "border-cyan-400/60 bg-cyan-500/10" : "border-white/10 bg-black/20"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="font-medium text-white">{label}</p>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
            active ? "bg-cyan-500 text-slate-950" : "bg-slate-700 text-slate-300"
          }`}
        >
          {active ? "Active" : "Standby"}
        </span>
      </div>
      <p className="mt-2 truncate font-mono text-[10px] text-slate-500">{detail}</p>
    </div>
  );
}

function Card({
  title,
  value,
  hint,
  accent,
}: {
  title: string;
  value: string;
  hint: string;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-white/5 bg-obsidian-900/70 p-4 shadow-lg shadow-black/30">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <p className={`mt-2 text-2xl font-semibold ${accent}`}>{value}</p>
      <p className="mt-1 text-xs text-slate-500">{hint}</p>
    </div>
  );
}
