# Run instructions — exact paths and commands

All paths below are relative to the repository root:

`/Users/shruthikatta/Desktop/CMPE281/intelligent-cloud-disaster-recovery-streaming-platform/`

On your machine, use your own clone path; the **relative** paths inside the repo are what matter.

---

## Prerequisites

- **Python** 3.10+ (3.9 works if `eval-type-backport` is installed — see `requirements.txt`)
- **Node.js** 18+ and npm
- **Git** (optional)

---

## 1. Python environment

```bash
cd /Users/shruthikatta/Desktop/CMPE281/intelligent-cloud-disaster-recovery-streaming-platform
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**If `pip install` fails on TensorFlow:** the repo pins a version available on PyPI for current Python (see `requirements.txt`). Use a **venv** (not system Python 3.13 unless TensorFlow publishes a wheel). If you only need the API and seeding without training ML locally, you can temporarily comment out the `tensorflow` line in `requirements.txt`, run `pip install -r requirements.txt` again, then install the rest — inference will fall back to the mock predictor until TensorFlow is installed.

**If you see `No module named 'greenlet'`** (seed or uvicorn startup): run `pip install greenlet` or reinstall deps — `requirements.txt` includes `greenlet` for SQLAlchemy async.

**If `uvicorn: command not found`:** activate the venv (`source .venv/bin/activate`) or run the module form:

`python -m uvicorn apps.backend.app.main:app --reload --host 0.0.0.0 --port 8000`

(same `PYTHONPATH=.` as below).

---

## 2. Configuration (local mock)

```bash
cp .env.example .env
```

Key files:

- **Environment template:** `.env.example`
- **Runtime settings (Pydantic):** `shared/config/settings.py`

Default mock DB URL: `sqlite+aiosqlite:///./data/streamvault.db` (file created at `./data/streamvault.db`).

---

## 3. Seed data (users + video catalog)

```bash
export PYTHONPATH=.
python scripts/seed_data.py
```

- **Script path:** `scripts/seed_data.py`
- **Re-run anytime:** demo accounts in `apps/backend/app/demo_accounts.py` are **upserted** (missing users are created; existing demo emails get passwords reset to match the seed). Use this if e.g. `admin@streamvault.io` was added after your first seed.
- **Demo users:** defined in `apps/backend/app/demo_accounts.py` (same list returned by `GET /api/auth/demo-accounts` when `APP_MODE=mock`). After seed, examples include `demo@streamvault.io` / `demo1234`, `alex@streamvault.io` / `demo1234`, `jordan@streamvault.io` / `demo1234`, `admin@streamvault.io` / `admin1234`.

---

## 4. Backend (FastAPI)

**Entry module:** `apps/backend/app/main.py`  
**ASGI app object:** `app`

```bash
export PYTHONPATH=.
python -m uvicorn apps.backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

| Item | Value |
|------|--------|
| **Port** | `8000` |
| **Base URL** | `http://127.0.0.1:8000` |
| **API prefix** | `/api` |
| **Health** | `GET http://127.0.0.1:8000/api/health` |
| **OpenAPI UI** | `http://127.0.0.1:8000/docs` (Swagger) |

**Stop:** `Ctrl+C` in the terminal running uvicorn.

---

## 5. End-user frontend (React + Vite)

**Directory:** `apps/frontend/`  
**Dev server port:** `5173`

```bash
cd apps/frontend
cp .env.example .env.local   # optional; defaults to http://127.0.0.1:8000/api
npm install
npm run dev
```

| Item | Value |
|------|--------|
| **URL** | `http://localhost:5173` |
| **API base env** | `VITE_API_URL` in `apps/frontend/.env.example` |

**Stop:** `Ctrl+C`.

---

## 6. Admin dashboard (React + Vite)

**Directory:** `apps/admin-dashboard/`  
**Dev server port:** `5174`

```bash
cd apps/admin-dashboard
cp .env.example .env.local   # optional
npm install
npm run dev
```

| Item | Value |
|------|--------|
| **URL** | `http://localhost:5174` |
| **API** | Same backend `/api` via `VITE_API_URL` |

**Stop:** `Ctrl+C`.

---

## 7. ML service options

### A. In-process (default)

The backend loads inference from `get_model_inference_adapter()` in `cloud_adapters/dependency_factory.py`.  
If the file **`services/ml_predictor/models/ed_lstm_demo.keras`** exists, **local TensorFlow** inference is used (`services/ml_predictor/inference/local_tensorflow.py`).

### B. Train ED-LSTM (generates the `.keras` file)

```bash
export PYTHONPATH=.
python services/ml_predictor/train.py
```

- **Training script:** `services/ml_predictor/train.py`
- **Model output:** `services/ml_predictor/models/ed_lstm_demo.keras`
- **Architecture:** `services/ml_predictor/ed_lstm/model.py`

### C. Standalone ML HTTP service (optional, port 8001)

```bash
export PYTHONPATH=.
python -m uvicorn services.ml_predictor.api:app --host 127.0.0.1 --port 8001
```

Set in `.env`:

- `ML_USE_STANDALONE_SERVICE=true`
- `ML_SERVICE_URL=http://127.0.0.1:8001`

**Stop:** `Ctrl+C`.

---

## 8. Demo simulations (scenarios + failover)

With the **backend running** on port 8000:

```bash
chmod +x scripts/demo_simulations.sh   # once
./scripts/demo_simulations.sh
```

- **Script path:** `scripts/demo_simulations.sh`
- **API base:** override with `API_BASE=http://127.0.0.1:8000/api ./scripts/demo_simulations.sh`

---

## 9. AWS connection verification (before real adapters)

```bash
export PYTHONPATH=.
python scripts/verify_aws_connection.py
```

- **Script:** `scripts/verify_aws_connection.py`
- **Session helpers:** `cloud_adapters/aws/config/aws_session.py`, `cloud_adapters/aws/config/aws_settings.py`

---

## 10. Order of execution (recommended)

1. `pip install -r requirements.txt`
2. `python scripts/seed_data.py`
3. `python -m uvicorn apps.backend.app.main:app --reload --port 8000` (with `PYTHONPATH=.` and venv active)
4. `cd apps/frontend && npm run dev`
5. `cd apps/admin-dashboard && npm run dev`
6. (Optional) `python services/ml_predictor/train.py` then restart API
7. (Optional) standalone ML on 8001 + `ML_USE_STANDALONE_SERVICE=true`

---

## 11. Optional Docker Compose

**File:** `docker-compose.yml` at repo root — installs deps inside containers and exposes API + frontend dev. For a graded demo, running natively with the commands above is usually simpler.

```bash
docker compose up --build
```

---

## 12. How to stop everything

- Stop each terminal process with **Ctrl+C** (backend, each npm dev server, optional ML uvicorn).
