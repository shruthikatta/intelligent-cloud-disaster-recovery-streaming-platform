from __future__ import annotations

"""
Seeded demo users — same list is used by scripts/seed_data.py and /api/auth/demo-accounts (mock only).
Passwords are for local presentation only; never enable this endpoint in production with real users.

Frontend offline copy (keep in sync): apps/frontend/src/demoData.ts
"""

DEMO_ACCOUNTS: list[dict[str, str]] = [
    {
        "email": "demo@streamvault.io",
        "password": "demo1234",
        "label": "Primary viewer — Shruthi Katta",
    },
    {
        "email": "alex@streamvault.io",
        "password": "demo1234",
        "label": "Second household — Rohan Aren",
    },
    {
        "email": "jordan@streamvault.io",
        "password": "demo1234",
        "label": "Mobile-only tester — Rishikesh Reddy Aluguvelli",
    },
    {
        "email": "admin@streamvault.io",
        "password": "admin1234",
        "label": "Admin-style account — Vikramadithya Baddam (use admin UI separately)",
    },
]
