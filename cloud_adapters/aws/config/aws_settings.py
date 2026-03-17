from __future__ import annotations

"""AWS-specific settings: regions, profiles, account id, feature flags."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AwsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.aws", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    aws_region: str | None = Field(default=None, alias="AWS_REGION")
    aws_profile: str | None = Field(default=None, alias="AWS_PROFILE")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_session_token: str | None = Field(default=None, alias="AWS_SESSION_TOKEN")
    aws_account_id: str | None = Field(default=None, alias="AWS_ACCOUNT_ID")

    use_aws_profile: bool = Field(default=False, alias="USE_AWS_PROFILE")
    use_iam_role: bool = Field(default=False, alias="USE_IAM_ROLE")

    # Resource names (fill for real deployment)
    s3_bucket_name: str = Field(default="", alias="S3_BUCKET_NAME")
    rds_host: str = Field(default="", alias="RDS_HOST")
    rds_port: int = Field(default=3306, alias="RDS_PORT")
    rds_database: str = Field(default="", alias="RDS_DATABASE")
    rds_user: str = Field(default="", alias="RDS_USER")
    rds_password: str = Field(default="", alias="RDS_PASSWORD")

    route53_hosted_zone_id: str = Field(default="", alias="ROUTE53_HOSTED_ZONE_ID")
    route53_primary_record: str = Field(default="", alias="ROUTE53_PRIMARY_RECORD")
    route53_dr_record: str = Field(default="", alias="ROUTE53_DR_RECORD")

    sagemaker_endpoint_name: str = Field(default="", alias="SAGEMAKER_ENDPOINT_NAME")
    sns_topic_arn: str = Field(default="", alias="SNS_TOPIC_ARN")
    sqs_queue_url: str = Field(default="", alias="SQS_QUEUE_URL")
    eventbridge_bus_name: str = Field(default="default", alias="EVENTBRIDGE_BUS_NAME")
    lambda_recovery_arn: str = Field(default="", alias="LAMBDA_RECOVERY_ARN")


@lru_cache
def get_aws_settings() -> AwsSettings:
    return AwsSettings()
