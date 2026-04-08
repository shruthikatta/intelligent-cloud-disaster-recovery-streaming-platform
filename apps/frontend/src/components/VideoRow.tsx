import { Link } from "react-router-dom";
import type { Video } from "../types";

export function VideoRow({ title, videos }: { title: string; videos: Video[] }) {
  if (!videos.length) return null;
  return (
    <section className="space-y-3">
      <div className="flex items-end justify-between">
        <h2 className="text-lg font-bold text-sv-ink">{title}</h2>
      </div>
      <div className="row-mask flex gap-4 overflow-x-auto pb-2">
        {videos.map((v) => (
          <Link
            key={v.id}
            to={`/video/${v.id}`}
            className="group w-40 shrink-0 md:w-48"
          >
            <div className="overflow-hidden rounded bg-sv-card shadow-card transition group-hover:z-10 group-hover:scale-[1.03] group-hover:shadow-card-hover">
              <img src={v.poster_url} alt="" className="aspect-[2/3] w-full object-cover" />
              <div className="space-y-0.5 p-2.5">
                <p className="truncate text-sm font-medium text-sv-ink">{v.title}</p>
                <p className="text-xs text-sv-muted">{v.category}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
