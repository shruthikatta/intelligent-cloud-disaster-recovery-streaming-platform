import { Link } from "react-router-dom";
import type { Video } from "../types";

export function Hero({ featured }: { featured: Video | null }) {
  if (!featured) return null;
  return (
    <section className="hero-gradient relative overflow-hidden rounded-md">
      <div className="grid gap-8 p-8 md:grid-cols-[1.2fr_0.8fr] md:p-10 md:pr-12">
        <div className="space-y-4">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sv-accent">Spotlight</p>
          <h1 className="text-4xl font-bold leading-tight text-sv-ink drop-shadow-sm md:text-5xl md:leading-[1.1]">
            {featured.title}
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-sv-muted line-clamp-3">{featured.description}</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              to={`/watch/${featured.id}`}
              className="inline-flex items-center gap-2 rounded bg-sv-ink px-8 py-2.5 text-sm font-bold text-sv-page transition hover:bg-sv-muted"
            >
              ▶ Play
            </Link>
            <Link
              to={`/video/${featured.id}`}
              className="inline-flex items-center gap-2 rounded border border-white/30 bg-white/5 px-8 py-2.5 text-sm font-semibold text-sv-ink backdrop-blur-sm transition hover:border-white/50 hover:bg-white/10"
            >
              More info
            </Link>
          </div>
        </div>
        <div className="relative">
          <div className="aspect-[3/4] overflow-hidden rounded-md border border-white/10 shadow-card">
            <img src={featured.poster_url} alt="" className="h-full w-full object-cover" />
          </div>
          <div className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-sv-accent/15 blur-3xl" />
        </div>
      </div>
    </section>
  );
}
