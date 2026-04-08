import { useEffect, useState } from "react";
import { api } from "../api";
import type { Video } from "../types";
import { Link } from "react-router-dom";

export function SearchBar() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Video[]>([]);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (q.length < 2) {
        setResults([]);
        return;
      }
      const { data } = await api.get<Video[]>("/videos", { params: { q } });
      if (!cancelled) setResults(data.slice(0, 8));
    };
    const t = setTimeout(run, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [q]);

  return (
    <div className="relative w-full max-w-xl">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search titles..."
        className="w-full rounded border border-sv-line bg-black/40 px-5 py-2.5 text-sm text-sv-ink outline-none ring-0 transition placeholder:text-sv-dim focus:border-sv-muted focus:ring-1 focus:ring-white/20"
      />
      {results.length > 0 && (
        <div className="absolute z-50 mt-1 w-full overflow-hidden rounded border border-sv-line bg-sv-card shadow-card">
          {results.map((v) => (
            <Link
              key={v.id}
              to={`/video/${v.id}`}
              className="flex items-center gap-3 px-3 py-2.5 text-sm text-sv-ink hover:bg-sv-line"
              onClick={() => setQ("")}
            >
              <img src={v.poster_url} alt="" className="h-10 w-7 rounded object-cover" />
              <span className="truncate">{v.title}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
