#!/usr/bin/env bash
# Create core AWS resources for StreamVault (S3, SNS, SQS, stub Lambda).
# Prerequisites: AWS CLI v2, jq, zip; credentials with IAM permissions to create these resources.
#
# Usage (from repo root):
#   export AWS_REGION=us-west-2
#   export STREAMVAULT_PREFIX=streamvault   # optional; default streamvault
#   chmod +x scripts/aws/bootstrap-resources.sh
#   ./scripts/aws/bootstrap-resources.sh
#
# Outputs: scripts/aws/out/streamvault-aws-exports.sh — source it after editing secrets.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export AWS_PAGER=""
REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="$REGION"
PREFIX="${STREAMVAULT_PREFIX:-streamvault}"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
UNIQUE_SUFFIX="$(openssl rand -hex 4)"
BUCKET="${PREFIX}-assets-${ACCOUNT}-${UNIQUE_SUFFIX}"
TOPIC_NAME="${PREFIX}-alerts-${UNIQUE_SUFFIX}"
QUEUE_NAME="${PREFIX}-events-${UNIQUE_SUFFIX}"
ROLE_NAME="${PREFIX}-lambda-exec-${UNIQUE_SUFFIX}"
FUNC_NAME="${PREFIX}-recovery-${UNIQUE_SUFFIX}"
OUT_DIR="${ROOT}/scripts/aws/out"
ZIP_PATH="${OUT_DIR}/recovery-lambda.zip"

mkdir -p "$OUT_DIR"
rm -f "$ZIP_PATH"

echo "==> Region=$REGION Account=$ACCOUNT"
echo "==> Creating S3 bucket: $BUCKET"

if [[ "$REGION" == "us-east-1" ]]; then
  aws s3api create-bucket --bucket "$BUCKET" 2>/dev/null || true
else
  aws s3api create-bucket --bucket "$BUCKET" \
    --create-bucket-configuration LocationConstraint="$REGION" 2>/dev/null || true
fi

aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true 2>/dev/null || true

echo "==> Creating SNS topic: $TOPIC_NAME"
TOPIC_ARN="$(aws sns create-topic --name "$TOPIC_NAME" --query TopicArn --output text)"

echo "==> Creating SQS queue: $QUEUE_NAME"
QUEUE_URL="$(aws sqs create-queue --queue-name "$QUEUE_NAME" --query QueueUrl --output text)"
QUEUE_ARN="$(aws sqs get-queue-attributes --queue-url "$QUEUE_URL" --attribute-names QueueArn --query Attributes.QueueArn --output text)"

echo "==> Packaging Lambda"
(cd "$ROOT/infrastructure/lambda/recovery_stub" && zip -q "$ZIP_PATH" handler.py)

TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$TRUST" 2>/dev/null || \
  echo "(Role $ROLE_NAME may already exist — continuing)"

ROLE_ARN="$(aws iam get-role --role-name "$ROLE_NAME" --query Role.Arn --output text)"
aws iam attach-role-policy --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || true

echo "Waiting 10s for IAM role propagation..."
sleep 10

aws lambda delete-function --function-name "$FUNC_NAME" 2>/dev/null || true
aws lambda create-function \
  --function-name "$FUNC_NAME" \
  --runtime python3.12 \
  --role "$ROLE_ARN" \
  --handler handler.lambda_handler \
  --zip-file "fileb://${ZIP_PATH}" \
  --timeout 30 \
  --memory-size 128 \
  --description "StreamVault recovery stub (extend for real DR)"

LAMBDA_ARN="$(aws lambda get-function --function-name "$FUNC_NAME" --query Configuration.FunctionArn --output text)"

EXPORT_FILE="${OUT_DIR}/streamvault-aws-exports.sh"
cat > "$EXPORT_FILE" << EOF
# Review before use.
# Merge into .env and .env.aws (see docs/AWS_DEPLOYMENT_CLI.md).

export AWS_REGION=${REGION}
export AWS_ACCOUNT_ID=${ACCOUNT}
export USE_AWS_PROFILE=true
export AWS_PROFILE=\${AWS_PROFILE:-default}

export APP_MODE=aws
export USE_REAL_AWS=true
export ENABLE_SNS=true
export ENABLE_SQS=true

export S3_BUCKET_NAME=${BUCKET}
export SNS_TOPIC_ARN=${TOPIC_ARN}
export SQS_QUEUE_URL=${QUEUE_URL}
export EVENTBRIDGE_BUS_NAME=default
export LAMBDA_RECOVERY_ARN=${LAMBDA_ARN}

# SageMaker: leave empty to use local Keras on the API host (train and copy ed_lstm_demo.keras).
export SAGEMAKER_ENDPOINT_NAME=

# Route 53: optional — set if you extend dns_adapter for real failover.
export ROUTE53_HOSTED_ZONE_ID=
export ROUTE53_PRIMARY_RECORD=
export ROUTE53_DR_RECORD=

# RDS: fill after running RDS CLI steps in docs/AWS_DEPLOYMENT_CLI.md
export DATABASE_URL='mysql+aiomysql://USER:PASSWORD@RDS_ENDPOINT:3306/streamvault'

# CORS: your public UI origins (ALB, CloudFront, etc.)
export CORS_ORIGINS='https://YOUR-ALB-DNS,https://YOUR-CLOUDFRONT'

# JWT
export JWT_SECRET='CHANGE_ME_LONG_RANDOM'
EOF

chmod 600 "$EXPORT_FILE" 2>/dev/null || true

echo ""
echo "==> Done. Resource summary:"
echo "    S3_BUCKET_NAME=$BUCKET"
echo "    SNS_TOPIC_ARN=$TOPIC_ARN"
echo "    SQS_QUEUE_URL=$QUEUE_URL"
echo "    LAMBDA_RECOVERY_ARN=$LAMBDA_ARN"
echo ""
echo "Next: source or merge: $EXPORT_FILE"
echo "Then: create RDS + EC2 per docs/AWS_DEPLOYMENT_CLI.md"
