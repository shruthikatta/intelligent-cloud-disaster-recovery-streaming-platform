/**
 * Offline copy of seeded demo users — keep in sync with apps/backend/app/demo_accounts.py
 * Shown when the API is down or GET /auth/demo-accounts is empty.
 */
export type DemoAccount = { email: string; password: string; label: string };

export const STATIC_DEMO_ACCOUNTS: DemoAccount[] = [
  { email: "demo@streamvault.io", password: "demo1234", label: "Primary viewer — Shruthi Katta" },
  { email: "alex@streamvault.io", password: "demo1234", label: "Second household — Rohan Aren" },
  { email: "jordan@streamvault.io", password: "demo1234", label: "Mobile-only tester — Rishikesh Reddy Aluguvelli" },
  {
    email: "admin@streamvault.io",
    password: "admin1234",
    label: "Admin-style account — Vikramadithya Baddam (use admin UI separately)",
  },
];
