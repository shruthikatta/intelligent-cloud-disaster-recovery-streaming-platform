# File map — what to open for which task

## Top-level

| Path | Purpose |
|------|---------|
| `README.md` | Overview, architecture, quick start |
| `requirements.txt` | Python dependencies |
| `.env.example` | Local mock defaults |
| `.env.aws.example` | AWS-oriented env template |
| `docker-compose.yml` | Optional containerized dev |

---

## Applications

| Path | Role |
|------|------|
| `apps/backend/app/main.py` | FastAPI startup, CORS, router include, **lifespan** (DB create + metric simulator) |
| `apps/backend/app/database.py` | Async SQLAlchemy engine + `get_db()` |
| `apps/backend/app/deps.py` | JWT dependency (`get_current_user`) |
| `apps/backend/app/security.py` | Password hash + JWT |
| `apps/backend/app/routers/*.py` | HTTP routes (`/api/...`) |
| `apps/backend/app/services/metrics_window.py` | Builds multivariate windows for ED-LSTM |
| `apps/frontend/` | End-user Vite app — `src/App.tsx`, `src/pages/*` |
| `apps/admin-dashboard/src/App.tsx` | Admin single-page console |

---

## Cloud adapters (AWS + mocks)

**Design doc name `platform/` → code folder `cloud_adapters/`** (avoids Python stdlib `platform` shadowing).

| Path | Role |
|------|------|
| `cloud_adapters/dependency_factory.py` | **Single switchboard** for mock vs AWS adapters |
| `cloud_adapters/mocks/state.py` | In-memory region, metrics, timeline, alerts (demo) |
| `cloud_adapters/mocks/mock_*.py` | Local implementations of each contract |
| `cloud_adapters/aws/config/aws_session.py` | Central boto3 session + `get_client()` |
| `cloud_adapters/aws/config/aws_settings.py` | Env-driven ARNs, bucket names, etc. |
| `cloud_adapters/aws/s3/storage_adapter.py` | S3 |
| `cloud_adapters/aws/cloudwatch/metrics_adapter.py` | CloudWatch |
| `cloud_adapters/aws/eventbridge/eventbus_adapter.py` | EventBridge |
| `cloud_adapters/aws/lambda_fn/recovery_adapter.py` | Lambda invoke |
| `cloud_adapters/aws/route53/dns_adapter.py` | Route 53 stub + app state sync |
| `cloud_adapters/aws/sns/notification_adapter.py` | SNS |
| `cloud_adapters/aws/sqs/queue_adapter.py` | SQS |
| `cloud_adapters/aws/sagemaker/model_inference_adapter.py` | SageMaker runtime |

---

## Services (Python packages)

| Path | Role |
|------|------|
| `services/ml_predictor/ed_lstm/model.py` | `build_ed_lstm()` |
| `services/ml_predictor/train.py` | Training → `models/ed_lstm_demo.keras` |
| `services/ml_predictor/inference/local_tensorflow.py` | Loads `.keras` for API inference |
| `services/ml_predictor/api.py` | Optional standalone FastAPI on port 8001 |
| `services/monitoring/metric_simulator.py` | Simulated CloudWatch metrics |
| `services/recovery_orchestrator/engine.py` | Anomaly → warn / failover decision path |
| `services/notification_service/fanout.py` | Thin wrapper over `NotificationAdapter` |

---

## Shared contracts

| Path | Role |
|------|------|
| `shared/contracts/*.py` | `Protocol` interfaces: storage, metrics, events, recovery, DNS, notifications, queue, model inference |
| `shared/config/settings.py` | `AppSettings` (`APP_MODE`, regions, JWT, DB URL, ML paths) |

---

## Scripts & infrastructure

| Path | Role |
|------|------|
| `scripts/seed_data.py` | Seed SQLite + demo user |
| `scripts/verify_aws_connection.py` | STS + sanity checks |
| `scripts/demo_simulations.sh` | Curl demo scenarios |
| `infrastructure/cloudformation/streamvault-core-placeholder.yaml` | Starter CFN |

---

## What to edit

| Goal | Files |
|------|--------|
| Local-only demo | `.env`, `shared/config/settings.py`, `cloud_adapters/mocks/*` |
| Real AWS | `.env.aws`, `cloud_adapters/aws/config/aws_settings.py`, IAM policies, **no code changes** if env complete |
| Prediction thresholds | `services/ml_predictor/inference/local_tensorflow.py`, `services/recovery_orchestrator/engine.py` |
| Failover policy | `services/recovery_orchestrator/engine.py`, `cloud_adapters/aws/route53/dns_adapter.py` |
| Backend startup | `apps/backend/app/main.py` |
| Frontend startup | `apps/frontend/vite.config.ts` (port 5173), `apps/admin-dashboard/vite.config.ts` (port 5174) |
