import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import type { Video } from "../types";

export function VideoDetailPage() {
  const { id } = useParams();
  const [video, setVideo] = useState<Video | null>(null);

  useEffect(() => {
    const run = async () => {
      const { data } = await api.get<Video>(`/videos/${id}`);
      setVideo(data);
    };
    run();
  }, [id]);

  if (!video) {
    return <div className="p-12 text-center text-sv-muted">Loading…</div>;
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 py-10 md:grid-cols-[0.9fr_1.1fr] md:px-8">
      <div className="overflow-hidden rounded bg-sv-card shadow-card">
        <img src={video.poster_url} alt="" className="h-full w-full object-cover" />
      </div>
      <div className="space-y-4">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-sv-accent">{video.category}</p>
        <h1 className="text-3xl font-bold text-sv-ink md:text-4xl">{video.title}</h1>
        <p className="leading-relaxed text-sv-muted">{video.description}</p>
        <div className="flex flex-wrap gap-3 text-sm text-sv-dim">
          <span>{video.year}</span>
          <span>·</span>
          <span>{video.rating.toFixed(1)} viewer score</span>
        </div>
        <Link
          to={`/watch/${video.id}`}
          className="inline-flex rounded bg-sv-ink px-10 py-3 text-sm font-bold text-sv-page transition hover:bg-sv-muted"
        >
          ▶ Play
        </Link>
      </div>
    </div>
  );
}
