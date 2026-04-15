# Deployment notes — validation, promotion, rollback

**Full AWS CLI deployment (account → EC2 → all services):** see **`docs/AWS_DEPLOYMENT_CLI.md`**.

## Pre-deployment validation

1. **Local mock run:** follow `docs/RUN_INSTRUCTIONS.md` — backend `8000`, frontend `5173`, admin `5174`.
2. **Seed data:** `python scripts/seed_data.py` — verify login on user UI.
3. **ML artifact:** run `python services/ml_predictor/train.py` OR configure SageMaker endpoint env vars.
4. **AWS:** `python scripts/verify_aws_connection.py` with the same profile/role used in production.

---

## Local → AWS promotion

1. Freeze Python deps: `requirements.txt` pinned versions.
2. Build static assets: `npm run build` in `apps/frontend` and `apps/admin-dashboard`; serve via S3+CloudFront or behind ALB on EC2/Nginx.
3. Set production `.env` on API hosts: `APP_MODE=aws`, `USE_REAL_AWS=true`, database URL to RDS, `JWT_SECRET` rotated.
4. Wire **security groups**: RDS ← app tier only; ALB → EC2; no public RDS.
5. Replace placeholder Route 53 logic in `cloud_adapters/aws/route53/dns_adapter.py` if you need real record swaps.

---

## Production environment checklist

- [ ] `JWT_SECRET` strong random value
- [ ] `DATABASE_URL` points to RDS (TLS if supported)
- [ ] `S3_BUCKET_NAME` and IAM for `s3:GetObject` / `PutObject` as needed
- [ ] `CORS_ORIGINS` = your real web origins only
- [ ] CloudWatch alarms on 5xx, latency, error rate
- [ ] SNS topic subscriptions (email/Slack) for `SNS_TOPIC_ARN`
- [ ] SageMaker endpoint in same region or cross-region invoke documented

---

## Service dependency order (startup)

1. RDS reachable
2. S3 bucket exists
3. API (FastAPI) healthy — `GET /api/health`
4. Frontends load and call API
5. Optional: SageMaker endpoint **InService**
6. Optional: Lambda `LAMBDA_RECOVERY_ARN` updated

---

## Smoke tests (post-deploy)

| Step | Action | Expected |
|------|--------|----------|
| 1 | `GET /api/health` | `200`, `app_mode` matches |
| 2 | Login via UI | JWT returned |
| 3 | Admin metrics chart | Non-empty after ~1 min |
| 4 | `POST /api/admin/prediction/run` | JSON with `prediction` |
| 5 | Manual failover button | `active_region` → `dr` in overview |

---

## Rollback

- **DNS:** revert Route 53 weights / failover to primary (or use manual failback API in demo: `POST /api/admin/failover/manual` with `"target":"primary"`).
- **Application:** redeploy previous artifact / CloudFormation stack version.
- **Database:** restore RDS snapshot if schema migration failed (not included in default demo).

---

## Presentation day checklist

- [ ] Seed script run; demo password known
- [ ] Browser tabs: user app + admin + API docs (`/docs`) optional
- [ ] Video playback tested (network allows Google sample URLs or swap to S3)
- [ ] Admin scenarios clicked once before judges arrive
- [ ] `docs/screenshots/*.png` placeholders replaced if slides need them
- [ ] AWS mode **off** unless internet + account verified
