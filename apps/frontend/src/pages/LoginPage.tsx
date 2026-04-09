import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { api, setAuth } from "../api";
import { STATIC_DEMO_ACCOUNTS, type DemoAccount } from "../demoData";
import { useSession } from "../context/AuthContext";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export function LoginPage() {
  const { login } = useSession();
  const nav = useNavigate();
  const [email, setEmail] = useState("demo@streamvault.io");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [demoRows, setDemoRows] = useState<DemoAccount[]>(STATIC_DEMO_ACCOUNTS);
  const [demoSource, setDemoSource] = useState<"static" | "api">("static");

  useEffect(() => {
    api
      .get<DemoAccount[]>("/auth/demo-accounts")
      .then(({ data }) => {
        if (data?.length) {
          setDemoRows(data);
          setDemoSource("api");
        }
      })
      .catch(() => {
        /* keep STATIC_DEMO_ACCOUNTS so credentials stay visible offline */
      });
  }, []);

  const applyDemo = (row: DemoAccount) => {
    setEmail(row.email);
    setPassword(row.password);
    setError(null);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const { data } = await api.post<{ access_token: string }>("/auth/login", { email, password });
      setAuth(data.access_token);
      login(data.access_token);
      nav("/");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (!err.response) {
          setError(
            `Cannot reach API at ${API_BASE}. From repo root (venv active): PYTHONPATH=. python -m uvicorn apps.backend.app.main:app --reload --port 8000`
          );
          return;
        }
        if (err.response.status === 401) {
          setError(
            "Invalid email or password. Re-run seed (creates/refreshes all demo users): PYTHONPATH=. python scripts/seed_data.py — then try again."
          );
          return;
        }
      }
      setError("Sign in failed. Check the API is running and the database is seeded.");
    }
  };

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6 px-4 py-16">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-sv-ink">Welcome back</h1>
          <p className="mt-1 text-sm text-sv-muted">JWT auth from the FastAPI backend.</p>
        </div>
        <Link
          to="/register"
          className="shrink-0 rounded border border-sv-line px-4 py-2 text-sm text-sv-muted transition hover:border-sv-muted hover:text-sv-ink"
        >
          Sign up
        </Link>
      </div>

      <div className="rounded border border-sv-line bg-sv-card p-4">
        <p className="text-xs font-bold uppercase tracking-wide text-sv-accent">
          Demo logins {demoSource === "api" ? "(from API)" : "(offline — same as seed)"}
        </p>
        <p className="mt-1 text-xs text-sv-dim">Click a row to fill the form, then Sign in.</p>
        <ul className="mt-3 space-y-2">
          {demoRows.map((row) => (
            <li key={row.email}>
              <button
                type="button"
                onClick={() => applyDemo(row)}
                className="w-full rounded border border-sv-line bg-black/20 px-3 py-2.5 text-left text-sm transition hover:border-sv-muted"
              >
                <span className="font-semibold text-sv-ink">{row.label}</span>
                <div className="mt-0.5 font-mono text-xs text-sv-muted">
                  {row.email}
                  <span className="text-sv-dim"> · </span>
                  <span className="text-sv-ink">{row.password}</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <form onSubmit={submit} className="space-y-4 rounded border border-sv-line bg-sv-card p-6 shadow-card">
        <label className="block text-sm text-sv-muted">
          Email
          <input
            className="mt-1 w-full rounded border border-sv-line bg-black/30 px-3 py-2.5 text-sv-ink outline-none placeholder:text-sv-dim focus:border-sv-muted focus:ring-1 focus:ring-white/15"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />
        </label>
        <label className="block text-sm text-sv-muted">
          Password
          <input
            className="mt-1 w-full rounded border border-sv-line bg-black/30 px-3 py-2.5 text-sv-ink outline-none placeholder:text-sv-dim focus:border-sv-muted focus:ring-1 focus:ring-white/15"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
        </label>
        {error && <p className="text-sm leading-relaxed text-sv-accent">{error}</p>}
        <button
          type="submit"
          className="w-full rounded bg-sv-accent py-2.5 text-sm font-bold text-white transition hover:bg-sv-accent-hover"
        >
          Sign in
        </button>
      </form>
    </div>
  );
}
