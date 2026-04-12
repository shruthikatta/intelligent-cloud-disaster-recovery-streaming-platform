"""
Playable HTTPS MP4 catalog for local demo.

The former Google Cast sample bucket (gtv-videos-bucket on commondatastorage.googleapis.com)
often returns HTTP 403 to direct browser/media fetches, so we rotate known-good public clips
(Blender Foundation, W3Schools, MDN, FileSamples).
"""

from __future__ import annotations

# Verified reachable for <video src> playback in typical browsers (no hotlink restrictions observed).
_DEMO_CLIPS: list[str] = [
    "https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4",
    "https://www.w3schools.com/html/mov_bbb.mp4",
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
    "https://filesamples.com/samples/video/mp4/sample_640x360.mp4",
    "https://filesamples.com/samples/video/mp4/sample_960x540.mp4",
]

_CATALOG_META: list[dict] = [
    {"title": "Northern Lights", "description": "Arctic relay drama.", "category": "Sci-Fi", "year": 2024, "rating": 4.6, "trending": True, "poster": "https://picsum.photos/seed/nl/400/600"},
    {"title": "Midnight Express", "description": "Last train out.", "category": "Thriller", "year": 2023, "rating": 4.3, "trending": True, "poster": "https://picsum.photos/seed/me/400/600"},
    {"title": "Cloud Atlas Foundry", "description": "Hyperscale migration story.", "category": "Documentary", "year": 2024, "rating": 4.7, "trending": False, "poster": "https://picsum.photos/seed/caf/400/600"},
    {"title": "River of Stars", "description": "Family across continents.", "category": "Drama", "year": 2022, "rating": 4.1, "trending": False, "poster": "https://picsum.photos/seed/ros/400/600"},
    {"title": "Signal/Noise", "description": "SREs chase a metric ghost.", "category": "Sci-Fi", "year": 2025, "rating": 4.5, "trending": True, "poster": "https://picsum.photos/seed/sn/400/600"},
    {"title": "Glass Harbor", "description": "Coastal corporate intrigue.", "category": "Thriller", "year": 2021, "rating": 4.0, "trending": False, "poster": "https://picsum.photos/seed/gh/400/600"},
    {"title": "Meltdown Shift", "description": "Short stress-test clip.", "category": "Action", "year": 2024, "rating": 4.2, "trending": True, "poster": "https://picsum.photos/seed/md/400/600"},
    {"title": "Sintel: Prologue", "description": "Blender open movie excerpt.", "category": "Animation", "year": 2010, "rating": 4.8, "trending": True, "poster": "https://picsum.photos/seed/si/400/600"},
    {"title": "Tears of Steel", "description": "Sci-fi short (full sample).", "category": "Sci-Fi", "year": 2012, "rating": 4.4, "trending": False, "poster": "https://picsum.photos/seed/tos/400/600"},
    {"title": "Weatherman Trek", "description": "Outdoor demo footage.", "category": "Documentary", "year": 2019, "rating": 4.0, "trending": False, "poster": "https://picsum.photos/seed/wt/400/600"},
    {"title": "GTI Lap", "description": "Car review sample.", "category": "Sports", "year": 2018, "rating": 3.9, "trending": False, "poster": "https://picsum.photos/seed/gti/400/600"},
    {"title": "Grand Challenge", "description": "What can you get for a grand?", "category": "Comedy", "year": 2017, "rating": 3.8, "trending": False, "poster": "https://picsum.photos/seed/gc/400/600"},
    {"title": "MDN Flower", "description": "CC0 nature clip (Mozilla).", "category": "Nature", "year": 2020, "rating": 4.5, "trending": True, "poster": "https://picsum.photos/seed/fl/400/600"},
    {"title": "W3C Big Buck Sample", "description": "Classic HTML5 tutorial asset.", "category": "Animation", "year": 2015, "rating": 4.3, "trending": False, "poster": "https://picsum.photos/seed/w3/400/600"},
    {"title": "Volcano Bay", "description": "Another Cast sample.", "category": "Action", "year": 2020, "rating": 4.1, "trending": False, "poster": "https://picsum.photos/seed/vb/400/600"},
    {"title": "Neon Drift", "description": "Joyrides loop.", "category": "Sci-Fi", "year": 2026, "rating": 4.0, "trending": True, "poster": "https://picsum.photos/seed/nd/400/600"},
    {"title": "Quiet Room", "description": "Escapes variant.", "category": "Drama", "year": 2023, "rating": 4.2, "trending": False, "poster": "https://picsum.photos/seed/qr/400/600"},
    {"title": "Laugh Track Zero", "description": "Fun sample loop.", "category": "Comedy", "year": 2024, "rating": 3.7, "trending": False, "poster": "https://picsum.photos/seed/lt/400/600"},
    {"title": "Edge of Tomorrow", "description": "Blazes short.", "category": "Thriller", "year": 2025, "rating": 4.4, "trending": True, "poster": "https://picsum.photos/seed/eot/400/600"},
    {"title": "Pacific Run", "description": "Elephants Dream opener.", "category": "Animation", "year": 2011, "rating": 4.6, "trending": False, "poster": "https://picsum.photos/seed/pr/400/600"},
    {"title": "Bunny Hop Classic", "description": "Big Buck Bunny full sample.", "category": "Family", "year": 2008, "rating": 4.9, "trending": True, "poster": "https://picsum.photos/seed/bbc/400/600"},
    {"title": "Steel City", "description": "Tears of Steel excerpt.", "category": "Sci-Fi", "year": 2012, "rating": 4.3, "trending": False, "poster": "https://picsum.photos/seed/sc/400/600"},
    {"title": "Sintel Redux", "description": "Sintel sample.", "category": "Fantasy", "year": 2010, "rating": 4.7, "trending": False, "poster": "https://picsum.photos/seed/sr/400/600"},
    {"title": "Outback Dawn", "description": "Subaru sample loop.", "category": "Documentary", "year": 2019, "rating": 3.9, "trending": False, "poster": "https://picsum.photos/seed/od/400/600"},
    {"title": "Hot Hatch", "description": "GTI review sample.", "category": "Sports", "year": 2018, "rating": 4.0, "trending": False, "poster": "https://picsum.photos/seed/hh/400/600"},
    {"title": "Budget Wheels", "description": "Grand challenge sample.", "category": "Reality", "year": 2017, "rating": 3.8, "trending": False, "poster": "https://picsum.photos/seed/bw/400/600"},
    {"title": "Field Notes", "description": "Flower macro (MDN).", "category": "Nature", "year": 2020, "rating": 4.4, "trending": True, "poster": "https://picsum.photos/seed/fn/400/600"},
    {"title": "Tutorial Loop", "description": "W3C mov_bbb.", "category": "Animation", "year": 2015, "rating": 4.2, "trending": False, "poster": "https://picsum.photos/seed/tl/400/600"},
    {"title": "Meltdown Replay", "description": "Stress clip.", "category": "Action", "year": 2024, "rating": 3.9, "trending": False, "poster": "https://picsum.photos/seed/mr/400/600"},
    {"title": "Joyride Nights", "description": "Night drive sample.", "category": "Crime", "year": 2025, "rating": 4.1, "trending": True, "poster": "https://picsum.photos/seed/jn/400/600"},
]

CATALOG: list[dict] = [
    {**row, "stream": _DEMO_CLIPS[i % len(_DEMO_CLIPS)]} for i, row in enumerate(_CATALOG_META)
]
