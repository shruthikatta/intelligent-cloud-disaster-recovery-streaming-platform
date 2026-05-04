# StreamVault — Component implementation

**Project:** StreamVault (intelligent cloud disaster recovery for video streaming)

**Contributors**

| Name |
|------|
| Shruthi Katta |
| Rohan Aren |
| Rishikesh Reddy Aluguvelli |
| Vikramadithya Baddam |

---

## 1. What we built (objective)

This repository implements the main pieces of the architecture: a streaming-facing web app, an admin control plane for disaster recovery and monitoring, a FastAPI backend, persistence, and ML-assisted recovery logic. The code runs locally with mocks or on AWS using real services through boto3 adapters.

The goal is working integration end to end: the UIs call REST APIs, the API reads and writes data, metrics flow into charts and into an Encoder-Decoder LSTM path, and the recovery orchestrator can drive failover-related actions (including manual failover for walkthroughs).

---

## 2. Core components

### 2.1 Frontend and client interfaces

We ship two React (TypeScript + Vite) applications:

- **End-user app** (`apps/frontend/`): browsing, search, video detail, JWT-based sign-in, and playback using sample streams. It talks to the backend over REST (`VITE_API_URL`, default `http://127.0.0.1:8000/api`).
- **Admin dashboard** (`apps/admin-dashboard/`): region overview, metric charts, scenario controls (for example CPU spike), “run prediction + policy,” forecast strip, manual failover / failback, and timelines for events and notifications. Dev server runs on port **5174** so it does not collide with the user app (**5173**).

Both apps use the same API prefix `/api` and rely on standard HTTP JSON requests.

### 2.2 Backend services

The API is **FastAPI** under `apps/backend/app/`. Routers include health, auth, users, videos, watch history, and admin (`main.py` mounts them under `/api`). On startup we create SQLite tables if needed (async SQLAlchemy) and start the metric simulator background loop so the admin charts always have something to plot during local demo.

Admin endpoints used for integration demos include:

- `GET /api/admin/overview`, `GET /api/admin/region-status`, `GET /api/admin/metrics/series`
- `POST /api/admin/scenario` to stress the simulator
- `POST /api/admin/prediction/run` to run ED-LSTM inference (or mock) and feed **RecoveryEngine**
- `POST /api/admin/failover/manual` for deterministic failover storytelling

OpenAPI is available at `/docs` when the server is running.

### 2.3 Cloud-oriented resources (compute, storage, adapters)

**Compute:** We primarily demonstrate **EC2** running `uvicorn` (documented in `docs/AWS_DEMO_SINGLE_EC2.md` for a single-instance demo, and `docs/AWS_DEPLOYMENT_CLI.md` for a fuller stack). The backend process is the main compute unit; optional SageMaker is documented for hosted ML.

**Storage:**

- **Database:** Local and demo deployments use **SQLite** via `DATABASE_URL` (`sqlite+aiosqlite:///./data/streamvault.db`). AWS guidance uses **RDS** (MySQL-compatible URL) when moving off the laptop.
- **Object storage:** Code paths use an **S3-compatible adapter** (`cloud_adapters/aws/` with mocks in `cloud_adapters/mocks/`) for patterns like presigned URLs when `APP_MODE=aws` and credentials are set.

**Other cloud hooks:** CloudWatch-style metrics, EventBridge-style events, SNS/SQS notifications and queues, Lambda-style recovery invocation, and Route 53-style DNS failover are implemented behind interfaces so mock mode works offline and AWS mode swaps in boto3. Details and env vars are in `docs/AWS_INTEGRATION_GUIDE.md`.

---

## 3. Functional integration

### 3.1 REST and data exchange

All integration between browsers and services is **REST/JSON**. After login, the JWT travels on protected routes as usual for FastAPI. Watch progress and catalog data go through the videos and watch routers; admin flows use `/api/admin/*`.

The metric simulator pushes samples into the metrics adapter; `GET /api/admin/metrics/series` aggregates series for the dashboard charts. When we run `POST /api/admin/prediction/run`, the backend builds a multivariate feature window (`build_feature_window`), calls the model adapter (in-process TensorFlow model file or optional HTTP ML microservice via settings), then passes anomaly / severity into **RecoveryEngine**, which coordinates adapters (events, notifications, optional Lambda path) consistent with the design.

### 3.2 End-to-end workflow (demo flow)

A typical walkthrough:

1. Start backend (`python -m uvicorn apps.backend.app.main:app`, `PYTHONPATH=.`) and seed data (`scripts/seed_data.py`).
2. Open the user app, log in with a seeded demo account, open a title and play sample media.
3. Open the admin app, confirm charts update every few seconds.
4. Fire a **scenario** (for example surge) and watch metrics move.
5. Click **Run ED-LSTM + policy** (or equivalent) so `prediction` and `decision` JSON appear; optionally trigger manual failover and verify overview / region state.

That sequence exercises UI → API → DB/simulator → ML path → orchestration → shared mock state (and real AWS adapters when enabled).

### 3.3 Architecture diagram (logical view)

We use a logical diagram like this to explain integration (DNS and AWS names are conceptual when adapters are mocked):

```
                    +------------------+
                    |  Route 53 / DNS  |
                    |     (adapter)    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
       +------v------+               +------v------+
       |  Primary    |               |  DR region  |
       |  (concept)  |               |  (standby)  |
       +------+------+               +------+------+
              |                             ^
              |         +-------------------+
              |         |
       +------v---------v---------+
       |      FastAPI backend      |
       |  auth | videos | admin   |
       +------+----+--------+-----+
              |    |        |
              |    |        +------------------+
              |    |                           |
       +------v----v------+            +-------v--------+
       | SQLite / RDS    |            | MetricsAdapter |
       | + seed catalog  |            | + simulator    |
       +-----------------+            +-------+--------+
                                              |
                                      +-------v--------+
                                      | ED-LSTM infer  |
                                      | RecoveryEngine |
                                      +-------+--------+
                                              |
                              +---------------+---------------+
                              |               |               |
                       +------v-----+ +-------v------+ +-----v-----+
                       | Event bus  | | Notifications| | Queue etc.|
                       | (adapter)  | | SNS pattern  | | (adapter) |
                       +------------+ +--------------+ +-----------+

User React app ----REST----> FastAPI
Admin React app ---REST----> FastAPI
```

---

## 4. Deployment

### 4.1 Local (primary proof for development)

We follow `docs/RUN_INSTRUCTIONS.md`: Python venv, `pip install -r requirements.txt`, copy `.env.example` to `.env` with `APP_MODE=mock`, seed script, then uvicorn on port **8000**, plus `npm install` / `npm run dev` in each frontend folder.

### 4.2 AWS

- **Quick single EC2 proof:** `docs/AWS_DEMO_SINGLE_EC2.md` (Amazon Linux, Python 3.11 venv, clone repo, seed, bind `0.0.0.0:8000`, optional static build upload).
- **Broader CLI-oriented deploy:** `docs/AWS_DEPLOYMENT_CLI.md` (IAM, bootstrap script for S3/SNS/SQS/stub Lambda, EC2/RDS patterns, optional Route 53 and SageMaker).

We also keep `scripts/verify_aws_connection.py` to sanity-check credentials before turning on `USE_REAL_AWS=true`.

### 4.3 Documentation artifacts (screenshots / logs)

Place captures under `docs/screenshots/` (see README list). Useful artifacts include:

- Swagger `/docs` or `GET /api/health` response
- User home and player page
- Admin DR console with charts and prediction/failover actions
- Optional: EC2 terminal showing uvicorn listening, or CloudWatch-related console if the full AWS path was used

---

## 5. Efficiency and configuration choices

The stack stays lean for iteration while still resembling a production-style cloud design:

- **API:** Async SQLAlchemy and FastAPI reduce blocking on I/O; local SQLite avoids RDS cost during iteration.
- **Metrics:** The simulator uses a fixed interval (about three seconds in code) so dashboards update smoothly without flooding the browser.
- **ML:** Training produces `services/ml_predictor/models/ed_lstm_demo.keras`; inference reuses that file in-process so we do not pay per-request SageMaker latency unless we flip settings for a cloud-hosted model.
- **Frontends:** Production builds are static assets (`npm run build`), suitable for nginx on EC2 or S3/CloudFront, which keeps runtime compute on the API tier only.

We document smoke checks in `docs/DEPLOYMENT_NOTES.md` (health, login, metrics nonempty, prediction POST, manual failover). Those steps double as simple regression checks before release.

---

## 6. Demonstration summary

**Video:** An optional screen recording can follow the same flow as section 3.2 (login, stream, admin charts, scenario, prediction run, failover).

**Sample inputs and outputs:**

- **Input:** `POST /api/admin/scenario` with body like `{"scenario": "cpu_spike"}` (exact schema in FastAPI models).  
  **Output:** `{"scenario": "cpu_spike"}` acknowledgment; metrics series then reflect the scenario.
- **Input:** `POST /api/admin/prediction/run` with empty body.  
  **Output:** JSON containing `prediction` (errors, thresholds, anomaly flag as implemented) and `decision` from **RecoveryEngine**.
- **Input:** Sign-in form with seeded email/password from `demo_accounts.py` after `seed_data.py`.  
  **Output:** JWT and access to protected routes from the UIs.

**Tests:** The checklist above plus manual UI verification covers observable behavior; automated pytest suites are not included here, but behavior is visible through Swagger and the admin dashboard.

---

## 7. Closing note

This write-up ties component implementation to the StreamVault design: two clients, one cohesive API, persisted catalog and auth state, simulated observability feeding ML and policy, and a clear path to AWS through adapters and the deployment docs. Screenshots and any demo recording can accompany this document as needed.
