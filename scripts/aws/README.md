# AWS helper scripts

| File | Purpose |
|------|---------|
| `bootstrap-resources.sh` | Creates S3 bucket, SNS topic, SQS queue, IAM role + stub Lambda; writes `out/streamvault-aws-exports.sh`. |
| `iam-streamvault-app-policy.json` | **Template** — replace `REPLACE_*` placeholders with ARNs from bootstrap + your region/account, then create an IAM policy and attach to the **EC2 instance role**. |
| `out/` | Generated exports (gitignored) — **do not commit** secrets. |

Full step-by-step (account creation → EC2 → verify): **`docs/AWS_DEPLOYMENT_CLI.md`**.
