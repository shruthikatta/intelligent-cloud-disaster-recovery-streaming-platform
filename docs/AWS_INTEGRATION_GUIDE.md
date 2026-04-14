# AWS integration guide (A–Z)

This project keeps **all** AWS SDK usage under `cloud_adapters/aws/`. Application logic and FastAPI routes depend on **contracts** in `shared/contracts/` and factories in `cloud_adapters/dependency_factory.py`.

The proposal’s `/platform/aws/...` layout maps to **`cloud_adapters/aws/...`** in this repo (see README — `platform` would shadow Python’s stdlib).

---

## 1. What AWS resources you need (typical)

| Capability | AWS service | Adapter folder |
|------------|-------------|----------------|
| Object storage / video assets | S3 | `cloud_adapters/aws/s3/storage_adapter.py` |
| Metrics | CloudWatch | `cloud_adapters/aws/cloudwatch/metrics_adapter.py` |
| Events | EventBridge | `cloud_adapters/aws/eventbridge/eventbus_adapter.py` |
| Automation | Lambda | `cloud_adapters/aws/lambda_fn/recovery_adapter.py` |
| DNS failover | Route 53 | `cloud_adapters/aws/route53/dns_adapter.py` |
| Alerts | SNS | `cloud_adapters/aws/sns/notification_adapter.py` |
| Queues | SQS | `cloud_adapters/aws/sqs/queue_adapter.py` |
| Hosted ML | SageMaker runtime | `cloud_adapters/aws/sagemaker/model_inference_adapter.py` |
| Relational data | RDS (MySQL) | App uses `DATABASE_URL`; helpers placeholder `cloud_adapters/aws/rds/__init__.py` |
| EC2 / ALB | — | Placeholders `cloud_adapters/aws/ec2/`, `cloud_adapters/aws/alb/` |

**Centralized boto3 session**

- `cloud_adapters/aws/config/aws_session.py` — `get_boto3_session()`, `get_client()`, `require_aws_configured()`
- `cloud_adapters/aws/config/aws_settings.py` — resource ARNs, bucket names, etc.

---

## 2. Authentication modes supported

| Mode | How |
|------|-----|
| **Explicit keys** | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN` |
| **Named profile** | `USE_AWS_PROFILE=true`, `AWS_PROFILE=myprofile`, optional `AWS_REGION` |
| **IAM role** | On EC2/ECS/Lambda: instance/task/execution role — leave keys unset; set `USE_IAM_ROLE=true` for clarity in docs |
| **Default chain** | Shared credentials file, env vars, SSO (if profile configured) — boto3 default |
| **SSO** | `aws configure sso` then `AWS_PROFILE=your-sso-profile` |

Never commit secrets. Use `.env.aws` locally (gitignored pattern) or Secrets Manager in production.

---

## 3. Environment variables (core)

| Variable | Purpose |
|----------|---------|
| `APP_MODE` | `mock` or `aws` — toggles real adapters when combined with `USE_REAL_AWS` |
| `USE_REAL_AWS` | `true` to use AWS implementations from `dependency_factory` |
| `PRIMARY_REGION` | Default `us-west-2` |
| `DR_REGION` | Default `us-east-1` |
| `AWS_REGION` | Boto3 region |
| `AWS_PROFILE` | Profile name |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Long-lived or temp keys |
| `AWS_ACCOUNT_ID` | Metadata / ARNs (optional) |
| `USE_AWS_PROFILE` | `true` to prefer profile |
| `USE_IAM_ROLE` | Document that role is used on compute |
| `ENABLE_SNS` | `true` to use `SNSNotificationAdapter` |
| `ENABLE_SQS` | `true` to use `SQSQueueAdapter` |
| `S3_BUCKET_NAME` | Real bucket |
| `SNS_TOPIC_ARN` | Topic for alerts |
| `SQS_QUEUE_URL` | Queue URL |
| `EVENTBRIDGE_BUS_NAME` | Event bus name (default `default`) |
| `LAMBDA_RECOVERY_ARN` | Function for recovery workflow |
| `SAGEMAKER_ENDPOINT_NAME` | For `SageMakerInferenceAdapter` |
| `ROUTE53_HOSTED_ZONE_ID` | For Route 53 adapter |
| `DATABASE_URL` | e.g. `mysql+aiomysql://user:pass@rds-host:3306/db` (install async MySQL driver if used) |

**Example merge:** copy `.env.aws.example` to `.env.aws` and source it alongside `.env`.

**Files:**

- `.env.aws.example` — template at repo root
- `shared/config/settings.py` — app-level flags
- `cloud_adapters/aws/config/aws_settings.py` — AWS resource names

---

## 4. Switching mock → AWS

1. Run `python scripts/verify_aws_connection.py`.
2. Set `APP_MODE=aws` and `USE_REAL_AWS=true` in `.env`.
3. Fill `cloud_adapters/aws/config/aws_settings.py` fields via environment (see `.env.aws.example`).
4. Restart the API so `get_settings()` picks up changes.

**Factory wiring:** `cloud_adapters/dependency_factory.py` — this is the **only** place that chooses mock vs AWS per adapter.

---

## 5. Per-service hookup notes

### S3 (`StorageAdapter`)

- **File:** `cloud_adapters/aws/s3/storage_adapter.py`
- Set `S3_BUCKET_NAME`. Ensure bucket policy / CORS allow your ALB origin if browsers fetch presigned URLs.

### RDS

- Use `DATABASE_URL` with your MySQL endpoint. Local dev stays on SQLite; production points to RDS.
- Placeholder: `cloud_adapters/aws/rds/__init__.py`

### CloudWatch metrics

- **File:** `cloud_adapters/aws/cloudwatch/metrics_adapter.py`
- IAM: `cloudwatch:PutMetricData`, `cloudwatch:GetMetricStatistics` on your namespaces.

### EventBridge

- **File:** `cloud_adapters/aws/eventbridge/eventbus_adapter.py`
- IAM: `events:PutEvents` on the bus.

### Lambda recovery

- **File:** `cloud_adapters/aws/lambda_fn/recovery_adapter.py`
- Set `LAMBDA_RECOVERY_ARN`. Lambda should accept JSON payloads from `RecoveryEngine`.

### Route 53

- **File:** `cloud_adapters/aws/route53/dns_adapter.py`
- Today: validates hosted zone when set; extend `ChangeResourceRecordSets` for real failover. App state is still updated for the admin UI.

### SageMaker

- **File:** `cloud_adapters/aws/sagemaker/model_inference_adapter.py`
- Payload format must match what your endpoint expects; adjust `model_inference_adapter.py` if your model wrapper differs.

### SNS / SQS

- **Files:** `cloud_adapters/aws/sns/notification_adapter.py`, `cloud_adapters/aws/sqs/queue_adapter.py`
- Set `ENABLE_SNS=true`, `ENABLE_SQS=true` in `shared/config/settings.py` via env.

---

## 6. Verification script

- **Path:** `scripts/verify_aws_connection.py`
- Prints auth mode, region, STS identity, light S3 check.

---

## 7. Common mistakes

| Mistake | Fix |
|---------|-----|
| Wrong region for S3 bucket | Align `AWS_REGION` with bucket region |
| EventBridge `AccessDenied` | Bus name / IAM `events:PutEvents` |
| SageMaker 400 on payload | Match JSON body to endpoint’s expected schema |
| App still mock | `USE_REAL_AWS` must be `true` **and** `APP_MODE=aws` per `dependency_factory` |

---

## 8. Pre-deployment checklist

- [ ] `python scripts/verify_aws_connection.py` succeeds
- [ ] `.env` on servers has **no** plaintext long-term keys if roles are available
- [ ] S3 bucket CORS / ALB origin configured
- [ ] RDS security groups allow EC2/Lambda only
- [ ] SageMaker endpoint tested with sample window from `apps/backend/app/services/metrics_window.py`
- [ ] Route 53 health checks and failover records documented for your hosted zone
