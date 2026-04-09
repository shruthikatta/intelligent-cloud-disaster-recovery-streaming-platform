import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setAuth } from "../api";
import { STATIC_DEMO_ACCOUNTS, type DemoAccount } from "../demoData";
import { useSession } from "../context/AuthContext";

export function RegisterPage() {
  const { login } = useSession();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [hints, setHints] = useState<DemoAccount[]>(STATIC_DEMO_ACCOUNTS);

  useEffect(() => {
    api
      .get<DemoAccount[]>("/auth/demo-accounts")
      .then(({ data }) => {
        if (data?.length) setHints(data);
      })
      .catch(() => {});
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const { data } = await api.post<{ access_token: string }>("/auth/register", { email, password });
      setAuth(data.access_token);
      login(data.access_token);
      nav("/");
    } catch {
      setError("Sign up failed — email may already exist. Try a demo email from the list or sign in.");
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6 px-4 py-16">
      <h1 className="text-2xl font-bold text-sv-ink">Create an account</h1>
      <p className="text-sm text-sv-muted">
        Or use a pre-seeded demo account on the{" "}
        <Link to="/login" className="font-semibold text-sv-ink underline decoration-sv-accent underline-offset-2 hover:text-white">
          sign in
        </Link>{" "}
        page.
      </p>
      <form onSubmit={submit} className="space-y-4 rounded border border-sv-line bg-sv-card p-6 shadow-card">
        <label className="block text-sm text-sv-muted">
          Email
          <input
            className="mt-1 w-full rounded border border-sv-line bg-black/30 px-3 py-2.5 text-sv-ink outline-none placeholder:text-sv-dim focus:border-sv-muted focus:ring-1 focus:ring-white/15"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
            placeholder="you@example.com"
          />
        </label>
        <label className="block text-sm text-sv-muted">
          Password (min 4 characters)
          <input
            className="mt-1 w-full rounded border border-sv-line bg-black/30 px-3 py-2.5 text-sv-ink outline-none placeholder:text-sv-dim focus:border-sv-muted focus:ring-1 focus:ring-white/15"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
            minLength={4}
          />
        </label>
        {error && <p className="text-sm text-sv-accent">{error}</p>}
        <button
          type="submit"
          className="w-full rounded border border-sv-line bg-transparent py-2.5 text-sm font-bold text-sv-ink transition hover:bg-white/10"
        >
          Sign up
        </button>
      </form>

      <div className="rounded border border-amber-700/40 bg-amber-950/30 p-4 text-sm text-amber-100/95">
        <p className="font-semibold text-amber-200">Already seeded (use Sign in, not Sign up)</p>
        <ul className="mt-2 list-inside list-disc space-y-1 text-amber-100/90">
          {hints.map((h) => (
            <li key={h.email}>
              <span className="font-mono text-amber-50">{h.email}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
