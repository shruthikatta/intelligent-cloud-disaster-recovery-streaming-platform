from __future__ import annotations

#!/usr/bin/env python3
"""
Verify AWS credentials and list resolved configuration.

Usage (from repo root):
  PYTHONPATH=. python scripts/verify_aws_connection.py
"""


import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cloud_adapters.aws.config.aws_settings import AwsSettings, get_aws_settings
from cloud_adapters.aws.config.aws_session import AwsConfigurationError, get_boto3_session, require_aws_configured


def main() -> None:
    aws: AwsSettings = get_aws_settings()
    print("=== StreamVault AWS connection check ===\n")

    mode_parts = []
    if aws.use_iam_role:
        mode_parts.append("IAM role / instance metadata (USE_IAM_ROLE=true)")
    if aws.use_aws_profile and aws.aws_profile:
        mode_parts.append(f"named profile: {aws.aws_profile}")
    if aws.aws_access_key_id:
        mode_parts.append("explicit access key env vars")
    if not mode_parts:
        mode_parts.append("default credential chain (env, shared file, SSO, role)")

    print("Auth mode:", " + ".join(mode_parts))
    region = aws.aws_region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    print("Resolved region:", region or "(not set — boto may use defaults)")
    print("AWS account id (env):", aws.aws_account_id or "(unset)")

    try:
        require_aws_configured()
    except AwsConfigurationError as e:
        print("\nFAILED:", e)
        sys.exit(1)

    session = get_boto3_session()
    sts = session.client("sts")
    ident = sts.get_caller_identity()
    print("\nSTS get-caller-identity OK:")
    print("  Account:", ident.get("Account"))
    print("  Arn:", ident.get("Arn"))
    print("  UserId:", ident.get("UserId"))

    # Light-touch service checks (read-only where possible)
    s3 = session.client("s3")
    try:
        s3.list_buckets(MaxKeys=1)
        print("\nS3 ListBuckets: OK (limited)")
    except Exception as e:
        print("\nS3 ListBuckets: skipped or failed:", e)

    print("\nDone. If APP_MODE=aws, adapters will use this session.")
    print("See docs/AWS_INTEGRATION_GUIDE.md for resource wiring.")


if __name__ == "__main__":
    main()
