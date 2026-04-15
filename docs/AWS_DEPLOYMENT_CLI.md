# Deploy StreamVault on AWS (CLI-first guide)

> **Only need a quick demo on one machine?** Use **`docs/AWS_DEMO_SINGLE_EC2.md`** — EC2 + mock mode + SQLite, **no** S3/RDS/Lambda setup.

This document walks a new operator from **creating an AWS account** through **running the API on EC2** with **S3, CloudWatch, EventBridge, Lambda, SNS, SQS**, and optional **RDS**, **Route 53**, and **SageMaker**. Commands are copy-pasteable on **macOS, Linux, or WSL** with **AWS CLI v2** and **jq** installed.

> **Scope:** The application code uses boto3 adapters under `cloud_adapters/aws/`. Nothing auto-deploys from GitHub Actions—you run the steps below (or extend `infrastructure/cloudformation/`). A helper script creates **S3 + SNS + SQS + stub Lambda**; **RDS, EC2, ALB, and optional SageMaker** use documented CLI patterns.

---

## 0. What you will have at the end

| Layer | AWS service | Role in this repo |
|--------|-------------|-------------------|
| Object storage | **S3** | `S3StorageAdapter` — presigned URLs, uploads |
| Metrics | **CloudWatch** | `CloudWatchMetricsAdapter` — PutMetricData + GetMetricStatistics (simulator pushes when API runs) |
| Events | **EventBridge** | `EventBridgeAdapter` — default bus `PutEvents` |
| Automation | **Lambda** | `LambdaRecoveryAdapter` — invoked on proactive failover path |
| DNS (optional) | **Route 53** | `Route53FailoverAdapter` — extend for real record changes |
| Alerts | **SNS** | `SNSNotificationAdapter` — `ENABLE_SNS=true` |
| Queues | **SQS** | `SQSQueueAdapter` — `ENABLE_SQS=true` |
| ML (optional) | **SageMaker Runtime** | Used only if **no** local `ed_lstm_demo.keras` and endpoint name is set |
| Database | **RDS MySQL** (recommended) or SQLite on EC2 (demo only) | `DATABASE_URL` |
| Compute | **EC2** (+ optional **ALB**) | Run `uvicorn` + static frontends or separate S3/CloudFront |

---

## Part A — Create an AWS account and IAM identity

### A.1 Create the AWS account

1. Open [https://aws.amazon.com/](https://aws.amazon.com/) → **Create an AWS Account**.
2. Enter email, password, account name, contact/billing information.
3. Choose **Support plan** (Free Basic is enough to start).
4. Complete **phone verification** and wait until the account is **Active**.

### A.2 Create an IAM user for CLI (do not use the root user daily)

1. Sign in to the **AWS Console** as root (once), go to **IAM** → **Users** → **Create user**.
2. User name: e.g. `streamvault-deploy`.
3. **Attach policies directly** (for learning; tighten later):
   - Start with **AdministratorAccess** *only in a sandbox account*, **or**
   - Use the minimal policy in **Part H** after resources exist (recommended for teams).
4. After user creation: **Security credentials** → **Create access key** → **Command Line Interface (CLI)**.
5. Save **Access key ID** and **Secret access key** (shown once).

### A.3 Install and configure AWS CLI v2

```bash
# macOS (Homebrew)
brew install awscli jq

# Verify
aws --version
```

Configure a named profile (replace placeholders):

```bash
aws configure set region us-west-2 --profile streamvault
aws configure set aws_access_key_id AKIAxxxxxxxxxxxxxxxx --profile streamvault
aws configure set aws_secret_access_key YOUR_SECRET_KEY --profile streamvault
```

Test:

```bash
export AWS_PROFILE=streamvault
export AWS_REGION=us-west-2
aws sts get-caller-identity
```

You should see `Account`, `Arn`, `UserId`.

---

## Part B — Clone the repository and Python environment

```bash
git clone <YOUR_FORK_OR_REPO_URL> intelligent-cloud-disaster-recovery-streaming-platform
cd intelligent-cloud-disaster-recovery-streaming-platform

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Verify AWS from the repo (loads `.env` / `.env.aws` if present):

```bash
export PYTHONPATH=.
python scripts/verify_aws_connection.py
```

---

## Part C — Bootstrap S3, SNS, SQS, and stub Lambda (automated script)

From the **repository root**, with `AWS_PROFILE` and `AWS_REGION` set:

```bash
chmod +x scripts/aws/bootstrap-resources.sh
./scripts/aws/bootstrap-resources.sh
```

The script:

- Creates a **globally unique S3 bucket** (`streamvault-assets-<account>-<random>` pattern).
- Creates **SNS topic** and **SQS queue** (names include a random suffix).
- Zips `infrastructure/lambda/recovery_stub/handler.py`, creates an **IAM role** and **Lambda** (`python3.12`).
- Writes **`scripts/aws/out/streamvault-aws-exports.sh`** — **contains ARNs; do not commit to git** (the `out/` folder is gitignored except `.gitignore`).

Review and merge variables into your runtime environment:

```bash
cat scripts/aws/out/streamvault-aws-exports.sh
# Then either:
source scripts/aws/out/streamvault-aws-exports.sh
# Or append keys into a single .env file you pass to systemd / Docker.
```

---

## Part D — RDS MySQL (recommended for “real” deploy)

### D.1 Default VPC and subnets

```bash
export AWS_REGION=us-west-2
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[0:3].SubnetId' --output text | tr '\t' ',')
SUBNET_A=$(echo "$SUBNET_IDS" | cut -d, -f1)
SUBNET_B=$(echo "$SUBNET_IDS" | cut -d, -f2)
echo "VPC=$VPC_ID subnets=$SUBNET_IDS"
```

### D.2 DB subnet group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name streamvault-db-subnets \
  --db-subnet-group-description "StreamVault" \
  --subnet-ids "$SUBNET_A" "$SUBNET_B"
```

### D.3 Security group for RDS (MySQL from your EC2 SG later)

Create an EC2 security group first (Part E) if you want least privilege; **for a first pass** you can create RDS SG allowing 3306 from the VPC CIDR (tighten before production):

```bash
RDS_SG=$(aws ec2 create-security-group \
  --group-name streamvault-rds-sg \
  --description "MySQL for StreamVault" \
  --vpc-id "$VPC_ID" \
  --query GroupId --output text)

aws ec2 authorize-security-group-ingress \
  --group-id "$RDS_SG" \
  --protocol tcp \
  --port 3306 \
  --cidr 10.0.0.0/8
```

Adjust `--cidr` to your VPC CIDR (check `aws ec2 describe-vpcs`).

### D.4 Create the database instance

Pick a strong master password (store in Secrets Manager in real life):

```bash
export DB_PASSWORD='REPLACE_WITH_LONG_RANDOM_PASSWORD'

aws rds create-db-instance \
  --db-instance-identifier streamvault-mysql \
  --db-instance-class db.t4g.micro \
  --engine mysql \
  --engine-version 8.0.40 \
  --master-username admin \
  --master-user-password "$DB_PASSWORD" \
  --allocated-storage 20 \
  --vpc-security-group-ids "$RDS_SG" \
  --db-subnet-group-name streamvault-db-subnets \
  --backup-retention-period 1 \
  --publicly-accessible \
  --no-deletion-protection
```

> **Note:** `--publicly-accessible` simplifies coursework; for production use private subnets + bastion or VPN.

Wait until **available**:

```bash
aws rds wait db-instance-available --db-instance-identifier streamvault-mysql
RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier streamvault-mysql \
  --query 'DBInstances[0].Endpoint.Address' --output text)
echo "$RDS_ENDPOINT"
```

### D.5 Allow EC2 → RDS

After you create the EC2 security group (`EC2_SG` in Part E), add:

```bash
aws ec2 authorize-security-group-ingress \
  --group-id "$RDS_SG" \
  --protocol tcp \
  --port 3306 \
  --source-group "$EC2_SG"
```

(Remove the overly broad `10.0.0.0/8` rule when this is in place.)

### D.6 `DATABASE_URL` for the app

The backend uses **async** SQLAlchemy; use **`mysql+aiomysql`** (dependency: `aiomysql` in `requirements.txt`):

```bash
export DATABASE_URL="mysql+aiomysql://admin:${DB_PASSWORD}@${RDS_ENDPOINT}:3306/streamvault"
```

Tables are created on API startup (`Base.metadata.create_all` in lifespan) if the user has DDL rights.

---

## Part E — EC2 for the FastAPI API

### E.1 Key pair (SSH)

```bash
aws ec2 create-key-pair --key-name streamvault-key --query 'KeyMaterial' --output text > ~/.ssh/streamvault-key.pem
chmod 600 ~/.ssh/streamvault-key.pem
```

### E.2 Security group for EC2

```bash
EC2_SG=$(aws ec2 create-security-group \
  --group-name streamvault-api-sg \
  --description "StreamVault API" \
  --vpc-id "$VPC_ID" \
  --query GroupId --output text)

MY_IP=$(curl -sSf https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id "$EC2_SG" --protocol tcp --port 22 --cidr "${MY_IP}/32"
aws ec2 authorize-security-group-ingress --group-id "$EC2_SG" --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

> Add **80/443** if you put **ALB + Nginx** in front; restrict **8000** to ALB only in production.

### E.3 Latest Amazon Linux 2023 AMI

```bash
AMI=$(aws ssm get-parameters --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameters[0].Value' --output text)
```

### E.4 Launch instance

```bash
aws ec2 run-instances \
  --image-id "$AMI" \
  --instance-type t3.medium \
  --key-name streamvault-key \
  --security-group-ids "$EC2_SG" \
  --subnet-id "$SUBNET_A" \
  --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=streamvault-api}]' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]'

INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=streamvault-api" "Name=instance-state-name,Values=running,pending" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "SSH: ssh -i ~/.ssh/streamvault-key.pem ec2-user@$PUBLIC_IP"
```

### E.5 Install the app on EC2 (SSH session)

```bash
ssh -i ~/.ssh/streamvault-key.pem ec2-user@$PUBLIC_IP
```

On the instance:

```bash
sudo dnf update -y
sudo dnf install -y git python3.11 python3.11-pip gcc python3.11-devel
git clone https://github.com/YOUR_ORG/intelligent-cloud-disaster-recovery-streaming-platform.git
cd intelligent-cloud-disaster-recovery-streaming-platform
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Train and ship the Keras model (recommended so you do not depend on SageMaker stub)
export PYTHONPATH=.
python services/ml_predictor/train.py

# Seed RDS (same DATABASE_URL as on laptop test first, or run from EC2 after .env exists)
python scripts/seed_data.py
```

Create **`/home/ec2-user/intelligent-cloud-disaster-recovery-streaming-platform/.env`** on the server merging:

- All variables from `scripts/aws/out/streamvault-aws-exports.sh`
- `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` (include `http://$PUBLIC_IP:8000` only if you serve UIs from same host; prefer HTTPS + real domain)

Example minimal `.env` fragment:

```env
APP_MODE=aws
USE_REAL_AWS=true
AWS_REGION=us-west-2
ENABLE_SNS=true
ENABLE_SQS=true
S3_BUCKET_NAME=...
SNS_TOPIC_ARN=...
SQS_QUEUE_URL=...
LAMBDA_RECOVERY_ARN=...
EVENTBRIDGE_BUS_NAME=default
DATABASE_URL=mysql+aiomysql://admin:PASSWORD@rds-endpoint:3306/streamvault
JWT_SECRET=long-random-string
CORS_ORIGINS=https://your-admin-host,https://your-user-host
```

**Attach an IAM instance profile** to EC2 with permissions for S3, CloudWatch, EventBridge, Lambda invoke, SNS, SQS (same actions as your deploy user, or use the policy file in Part H). Creating an instance profile is easiest in the **IAM Console** (role → EC2 trust → attach policies → attach role to instance).

Run the API:

```bash
cd /home/ec2-user/intelligent-cloud-disaster-recovery-streaming-platform
source .venv/bin/activate
export PYTHONPATH=.
python -m uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000
```

For production, use **systemd** or **gunicorn+uvicorn workers** behind **Nginx**.

---

## Part F — Frontends (admin + user)

Build locally (or on a build server):

```bash
cd apps/frontend
echo "VITE_API_URL=https://api.yourdomain.com/api" > .env.production
npm ci && npm run build

cd ../admin-dashboard
echo "VITE_API_URL=https://api.yourdomain.com/api" > .env.production
npm ci && npm run build
```

**Option 1 — S3 + CloudFront (static hosting)**  
Create a second bucket (or prefix) for static sites, upload `dist/`, enable static website hosting or CloudFront origin, set **CORS** on the API `CORS_ORIGINS` to the CloudFront domain.

**Option 2 — Same EC2 + Nginx**  
Copy `dist/` to `/var/www/html/` with two `server_name` paths or subpaths; configure TLS with **Certbot**.

---

## Part G — EventBridge and CloudWatch

- **EventBridge:** the code uses the **`default`** event bus (`EVENTBRIDGE_BUS_NAME=default`). No extra resource is required; IAM user/role needs `events:PutEvents` on `arn:aws:events:REGION:ACCOUNT:event-bus/default`.
- **CloudWatch:** the running API’s **metric simulator** calls `PutMetricData` when `USE_REAL_AWS=true`. IAM needs `cloudwatch:PutMetricData` and `cloudwatch:GetMetricStatistics` for namespace `StreamVault/App`.

---

## Part H — IAM policy (application role on EC2)

Save as `scripts/aws/iam-streamvault-app-policy.json` (replace ARNs after bootstrap + RDS):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Bucket",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:HeadObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET",
        "arn:aws:s3:::YOUR_BUCKET/*"
      ]
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData", "cloudwatch:GetMetricStatistics"],
      "Resource": "*"
    },
    {
      "Sid": "EventBridgeDefaultBus",
      "Effect": "Allow",
      "Action": ["events:PutEvents"],
      "Resource": "arn:aws:events:REGION:ACCOUNT_ID:event-bus/default"
    },
    {
      "Sid": "LambdaInvokeRecovery",
      "Effect": "Allow",
      "Action": ["lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:YOUR_RECOVERY_FUNCTION"
    },
    {
      "Sid": "SNSPublish",
      "Effect": "Allow",
      "Action": ["sns:Publish"],
      "Resource": "SNS_TOPIC_ARN"
    },
    {
      "Sid": "SQS",
      "Effect": "Allow",
      "Action": ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:GetQueueUrl", "sqs:GetQueueAttributes"],
      "Resource": "SQS_QUEUE_ARN"
    },
    {
      "Sid": "SageMakerOptional",
      "Effect": "Allow",
      "Action": ["sagemaker:InvokeEndpoint"],
      "Resource": "*"
    }
  ]
}
```

Create policy and attach to the **EC2 instance role**:

```bash
aws iam create-policy --policy-name StreamVaultAppPolicy --policy-document file://scripts/aws/iam-streamvault-app-policy.json
# Then attach to your EC2 role via console or CLI (attach-role-policy).
```

---

## Part I — Route 53 (optional)

1. Register or move a domain to **Route 53** hosted zone.
2. Set `ROUTE53_HOSTED_ZONE_ID`, `ROUTE53_PRIMARY_RECORD`, `ROUTE53_DR_RECORD` in env.
3. Extend `cloud_adapters/aws/route53/dns_adapter.py` to call `ChangeResourceRecordSets` (see comment in file). Until then, the adapter still updates **in-app** failover state when hosted zone id is missing.

---

## Part J — SageMaker (optional)

The code path **`SageMakerInferenceAdapter`** expects a deployed endpoint and a JSON body `{"instances": [window]}`. Training/deploying a custom container is **not** scripted here.

**Practical course path:** keep **`ed_lstm_demo.keras`** on the EC2 host and **`ML_MODEL_PATH`** pointing to it so **`LocalTensorFlowInferenceAdapter`** is used (no SageMaker required).

To force SageMaker: remove or relocate the `.keras` file, set `SAGEMAKER_ENDPOINT_NAME`, and align the endpoint’s input/output schema with `cloud_adapters/aws/sagemaker/model_inference_adapter.py`.

---

## Part K — Verify end-to-end

```bash
curl -sS "http://$PUBLIC_IP:8000/api/health"
curl -sS -X POST "http://$PUBLIC_IP:8000/api/admin/prediction/run"
```

From the admin UI (after CORS + static deploy): scenarios, failover, charts.

---

## Part L — CloudFormation (optional IaC)

The repo includes **`infrastructure/cloudformation/streamvault-core-placeholder.yaml`** (S3 only). You can grow it to match all resources, then:

```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/streamvault-core-placeholder.yaml \
  --stack-name streamvault-core \
  --capabilities CAPABILITY_NAMED_IAM
```

That stack **does not** replace the full guide today—it is a starting point.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `AccessDenied` on PutMetricData | IAM policy CloudWatch section |
| `NoCredentialsError` | `AWS_PROFILE`, instance role attachment |
| DB connection refused | RDS SG ingress from `EC2_SG`, `DATABASE_URL` host/port |
| CORS errors | `CORS_ORIGINS` includes exact browser origin (scheme+host+port) |
| ML mock only | `.keras` path exists; or SageMaker env + no local file |

---

## Single-command recap (after account + CLI profile)

```bash
git clone <repo> && cd intelligent-cloud-disaster-recovery-streaming-platform
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export AWS_PROFILE=streamvault AWS_REGION=us-west-2 PYTHONPATH=.
./scripts/aws/bootstrap-resources.sh
python scripts/verify_aws_connection.py
# Then RDS + EC2 steps above, merge env, run uvicorn.
```

For questions about adapter contracts, see **`docs/AWS_INTEGRATION_GUIDE.md`**.
