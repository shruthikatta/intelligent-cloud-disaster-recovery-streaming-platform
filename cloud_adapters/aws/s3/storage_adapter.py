from __future__ import annotations

"""S3 storage adapter using boto3."""


from urllib.parse import quote

from botocore.exceptions import ClientError

from cloud_adapters.aws.config.aws_session import get_client
from cloud_adapters.aws.config.aws_settings import get_aws_settings


class S3StorageAdapter:
    def __init__(self, bucket: str | None = None, prefix: str = "") -> None:
        aws = get_aws_settings()
        self._bucket = bucket or aws.s3_bucket_name
        self._prefix = prefix
        self._client = get_client("s3")

    async def get_public_url(self, key: str) -> str:
        k = f"{self._prefix}{key}".lstrip("/")
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": k},
                ExpiresIn=3600,
            )
        except ClientError:
            return f"https://{self._bucket}.s3.amazonaws.com/{quote(k)}"

    async def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        k = f"{self._prefix}{key}".lstrip("/")
        self._client.put_object(Bucket=self._bucket, Key=k, Body=data, ContentType=content_type)
        return k

    async def exists(self, key: str) -> bool:
        k = f"{self._prefix}{key}".lstrip("/")
        try:
            self._client.head_object(Bucket=self._bucket, Key=k)
            return True
        except ClientError:
            return False
