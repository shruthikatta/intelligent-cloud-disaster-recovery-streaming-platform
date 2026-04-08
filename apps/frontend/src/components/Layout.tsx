import { Link, Outlet } from "react-router-dom";
import { useSession } from "../context/AuthContext";

export function Layout() {
  const { token, logout } = useSession();
  return (
    <div className="flex min-h-screen flex-col bg-sv-page">
      <header className="sticky top-0 z-40 border-b border-sv-line bg-sv-page/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 md:px-8">
          <Link to="/" className="text-xl font-bold tracking-tight text-sv-ink">
            Stream<span className="text-sv-accent">Vault</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm text-sv-muted">
            <Link to="/" className="transition hover:text-sv-ink">
              Home
            </Link>
            {token ? (
              <button
                type="button"
                onClick={logout}
                className="rounded border border-sv-line px-3 py-1.5 transition hover:border-sv-muted hover:text-sv-ink"
              >
                Sign out
              </button>
            ) : (
              <>
                <Link to="/register" className="transition hover:text-sv-ink">
                  Sign up
                </Link>
                <Link
                  to="/login"
                  className="rounded bg-sv-accent px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-sv-accent-hover"
                >
                  Sign in
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-sv-line bg-black/30 py-8 text-center text-xs text-sv-dim">
        Academic demo · Intelligent Cloud Disaster Recovery · Not affiliated with any commercial streamer
      </footer>
    </div>
  );
}
