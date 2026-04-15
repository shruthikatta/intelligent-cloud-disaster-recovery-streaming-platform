# Quick AWS demo — one EC2, mock mode (no extra AWS services)

Use this when you only need to **prove the app runs in AWS** (API + optional static UIs). The backend uses **`APP_MODE=mock`** and **`USE_REAL_AWS=false`** (default): SQLite on disk, in-memory “cloud” adapters — **no S3, RDS, SNS, Lambda billing or setup**.

---

## 1. Launch one EC2 instance

- **AMI:** Amazon Linux 2023  
- **Instance type:** `t3.micro` or `t3.small` (Free Tier eligible where available)  
- **Network:** Default VPC, **public IP** enabled  
- **Security group inbound:**
  - **SSH (22)** — your IP only (`x.x.x.x/32`)
  - **HTTP (8000)** — `0.0.0.0/0` for a quick demo (tighten or remove after class)

Create or use a key pair and download `.pem`.

---

## 2. SSH and install dependencies

```bash
chmod 600 /path/to/your-key.pem
ssh -i /path/to/your-key.pem ec2-user@YOUR_PUBLIC_IP
```

On the instance:

```bash
sudo dnf update -y
sudo dnf install -y git python3.11 python3.11-pip gcc python3.11-devel
git clone https://github.com/YOUR_ORG/intelligent-cloud-disaster-recovery-streaming-platform.git
cd intelligent-cloud-disaster-recovery-streaming-platform
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **TensorFlow:** If `pip install` fails on a small instance or Python version, see README troubleshooting — for API-only demo you can temporarily remove the `tensorflow` line from `requirements.txt` and reinstall; ML falls back to the mock predictor.

---

## 3. Configure env (stay in mock mode)

```bash
cp .env.example .env
# Ensure these (defaults are usually fine):
# APP_MODE=mock
# USE_REAL_AWS=false
```

---

## 4. Seed and run the API

```bash
export PYTHONPATH=.
python scripts/seed_data.py
python -m uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000
```

**Check:**

- Browser: `http://YOUR_PUBLIC_IP:8000/docs` (Swagger)  
- Or: `curl -s http://YOUR_PUBLIC_IP:8000/api/health`

Leave this terminal open or use `tmux`/`screen`.

---

## 5. (Optional) User / admin UIs

**Option A — Build on your laptop, upload static files**

```bash
# On laptop, with VITE_API_URL pointing at your EC2 API
cd apps/frontend && echo "VITE_API_URL=http://YOUR_PUBLIC_IP:8000/api" > .env.local && npm ci && npm run build
scp -i your-key.pem -r dist/* ec2-user@YOUR_PUBLIC_IP:~/sv-user/
```

On EC2, serve the folder (quick and dirty):

```bash
cd ~/sv-user && python3.11 -m http.server 8080 --bind 0.0.0.0
```

Open security group **port 8080**, then visit `http://YOUR_PUBLIC_IP:8080`.

Repeat for `apps/admin-dashboard` on another port (e.g. 8081) with `VITE_API_URL` set the same way.

**Option B — SSH tunnel (no open extra ports)**

```bash
# On laptop
ssh -i your-key.pem -L 5173:localhost:5173 ec2-user@YOUR_PUBLIC_IP
# On EC2 in another session run uvicorn as above; on laptop run npm run dev with VITE_API_URL=http://localhost:8000 — tunnel 8000 too if needed
```

Simplest tunnel for API only:

```bash
ssh -i your-key.pem -L 8000:localhost:8000 ec2-user@YOUR_PUBLIC_IP
```

Then open `http://127.0.0.1:8000/docs` locally.

---

## 6. Cost / cleanup

- Stop or **terminate** the instance when done to avoid charges.  
- This path uses **no** RDS, S3, or other services — **EC2 (+ optional data transfer)** only.

---

## When you need “full” AWS adapters

Follow **`docs/AWS_DEPLOYMENT_CLI.md`** (bootstrap script, RDS, IAM, etc.).
