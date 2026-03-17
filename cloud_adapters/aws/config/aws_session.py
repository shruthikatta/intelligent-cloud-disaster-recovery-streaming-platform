from __future__ import annotations

"""
Centralized boto3 session factory with safe credential resolution.

Resolution order:
1. Explicit env vars (when USE_REAL_AWS and keys present)
2. Named profile (USE_AWS_PROFILE=true and AWS_PROFILE)
3. Default boto3 chain (shared credentials, IAM role on EC2/Lambda, SSO, etc.)
"""


import os
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from cloud_adapters.aws.config.aws_settings import AwsSettings, get_aws_settings


class AwsConfigurationError(RuntimeError):
    """Raised when AWS is required but credentials or region are unusable."""


def _build_session(aws: AwsSettings) -> boto3.session.Session:
    region = aws.aws_region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    profile = aws.aws_profile

    if aws.use_aws_profile and profile:
        return boto3.session.Session(profile_name=profile, region_name=region)

    if aws.aws_access_key_id and aws.aws_secret_access_key:
        return boto3.session.Session(
            aws_access_key_id=aws.aws_access_key_id,
            aws_secret_access_key=aws.aws_secret_access_key,
            aws_session_token=aws.aws_session_token,
            region_name=region,
        )

    # Default chain: env vars, shared file, IAM role, SSO via profile if set
    return boto3.session.Session(profile_name=profile, region_name=region)


@lru_cache
def get_boto3_session() -> boto3.session.Session:
    aws = get_aws_settings()
    return _build_session(aws)


def get_client(service_name: str, **kwargs: Any) -> Any:
    session = get_boto3_session()
    return session.client(service_name, **kwargs)


def require_aws_configured() -> None:
    """Verify STS identity; raise AwsConfigurationError on failure."""
    try:
        sts = get_client("sts")
        sts.get_caller_identity()
    except NoCredentialsError as e:
        raise AwsConfigurationError(
            "No AWS credentials found. Configure AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, "
            "or AWS_PROFILE / shared credentials, or IAM role on the host."
        ) from e
    except ClientError as e:
        raise AwsConfigurationError(f"AWS STS get-caller-identity failed: {e}") from e


def clear_session_cache() -> None:
    """For tests: reset cached session."""
    get_boto3_session.cache_clear()
