import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { useSession } from "../context/AuthContext";
import type { Video } from "../types";

/** Known-good MP4 when catalog URL or CDN blocks playback (Cast bucket often returns 403). */
const FALLBACK_MP4 =
  "https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4";

function pickStreamUrl(raw: Video): string {
  const u = raw.stream_url?.trim();
  if (u) return u;
  return FALLBACK_MP4;
}

export function PlayerPage() {
  const { id } = useParams();
  const { token } = useSession();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const triedFallback = useRef(false);
  const [video, setVideo] = useState<Video | null>(null);
  const [playSrc, setPlaySrc] = useState<string | null>(null);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      setMetaError(null);
      if (!id || Number.isNaN(Number(id))) {
        setMetaError("Invalid video link.");
        setVideo(null);
        setPlaySrc(null);
        return;
      }
      try {
        const { data } = await api.get<Video>(`/videos/${id}`);
        if (!cancelled) {
          setVideo(data);
          setPlaySrc(pickStreamUrl(data));
          setMediaError(null);
          triedFallback.current = false;
        }
      } catch {
        if (!cancelled) {
          setVideo(null);
          setPlaySrc(null);
          setMetaError("Could not load this title from the API. Is the backend running?");
        }
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!video || !token) return;
    const timer = window.setInterval(async () => {
      const v = videoRef.current;
      if (!v || v.paused) return;
      try {
        await api.post("/watch/progress", { video_id: video.id, progress_sec: Math.floor(v.currentTime) });
      } catch {
        /* demo */
      }
    }, 20000);
    return () => clearInterval(timer);
  }, [video, token]);

  if (metaError) {
    return <div className="p-12 text-center text-sv-accent">{metaError}</div>;
  }

  if (!video || !playSrc) {
    return <div className="p-12 text-center text-sv-muted">Loading player…</div>;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4 px-4 py-8 md:px-8">
      <div className="overflow-hidden rounded bg-black shadow-card ring-1 ring-white/10">
        <video
          key={playSrc}
          ref={videoRef}
          className="aspect-video w-full"
          controls
          playsInline
          preload="metadata"
          poster={video.poster_url}
          src={playSrc}
          onError={(e) => {
            const code = e.currentTarget.error?.code;
            if (code === MediaError.MEDIA_ERR_ABORTED) return;
            if (!triedFallback.current && playSrc !== FALLBACK_MP4) {
              triedFallback.current = true;
              setMediaError("Primary URL failed in the browser. Trying a known-good fallback (Big Buck Bunny).");
              setPlaySrc(FALLBACK_MP4);
            } else {
              setMediaError("Playback still failing — check network, VPN, or corporate blocking of video CDNs.");
            }
          }}
        />
      </div>
      {mediaError && (
        <p className="rounded border border-amber-700/50 bg-amber-950/40 px-3 py-2 text-sm text-amber-100">{mediaError}</p>
      )}
      <div>
        <h1 className="text-2xl font-bold text-sv-ink">{video.title}</h1>
        <p className="mt-1 break-all font-mono text-xs text-sv-dim">{playSrc}</p>
        <p className="mt-2 text-sm text-sv-muted">
          {token ? "Progress syncs to the API about every 20s while playing." : "Sign in to save progress."}
        </p>
      </div>
    </div>
  );
}
