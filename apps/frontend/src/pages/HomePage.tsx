import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { Hero } from "../components/Hero";
import { SearchBar } from "../components/SearchBar";
import { VideoRow } from "../components/VideoRow";
import { useSession } from "../context/AuthContext";
import type { Video } from "../types";

export function HomePage() {
  const { token } = useSession();
  const [all, setAll] = useState<Video[]>([]);
  const [trending, setTrending] = useState<Video[]>([]);
  const [cont, setCont] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      const [a, t] = await Promise.all([api.get<Video[]>("/videos"), api.get<Video[]>("/videos/trending")]);
      setAll(a.data);
      setTrending(t.data);
      if (token) {
        try {
          const c = await api.get<Video[]>("/watch/continue");
          setCont(c.data);
        } catch {
          setCont([]);
        }
      } else {
        setCont([]);
      }
      setLoading(false);
    };
    run();
  }, [token]);

  const byCat = useMemo(() => {
    const m = new Map<string, Video[]>();
    for (const v of all) {
      const k = v.category;
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(v);
    }
    return m;
  }, [all]);

  const featured = trending[0] || all[0] || null;

  return (
    <div className="mx-auto max-w-7xl space-y-10 px-4 py-8 md:px-8">
      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm text-sv-muted">Proactive resilience meets cinematic UX</p>
          <h1 className="mt-1 text-2xl font-bold text-sv-ink md:text-3xl">Tonight on StreamVault</h1>
        </div>
        <SearchBar />
      </div>

      {loading ? (
        <div className="py-24 text-center text-sv-muted">Loading catalog…</div>
      ) : (
        <>
          <Hero featured={featured} />
          {token && cont.length > 0 && <VideoRow title="Continue watching" videos={cont} />}
          <VideoRow title="Trending now" videos={trending} />
          {Array.from(byCat.entries()).map(([cat, vids]) => (
            <VideoRow key={cat} title={cat} videos={vids} />
          ))}
        </>
      )}
    </div>
  );
}
