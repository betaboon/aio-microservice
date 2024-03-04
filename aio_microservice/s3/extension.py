from __future__ import annotations

from typing import TYPE_CHECKING

import boto3
import botocore
from loguru import logger
from pydantic import BaseModel, Field, SecretStr

from aio_microservice.core.abc import ExtensionABC, readiness_probe, startup_hook

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


class S3Settings(BaseModel):
    endpoint_url: str = Field(
        description="The URL to connet to.",
    )
    access_key_id: str = Field(
        description="The AWS access key ID used for authentication.",
    )
    secret_access_key: SecretStr = Field(
        description="The AWS secret access key used for authentication.",
    )


class S3ExtensionImpl:
    def __init__(self, settings: S3Settings) -> None:
        self._settings = settings
        self._boto3_session = boto3.Session(
            aws_access_key_id=self._settings.access_key_id,
            aws_secret_access_key=self._settings.secret_access_key.get_secret_value(),
        )
        self._boto3_s3_client = self.session.client(
            service_name="s3",
            endpoint_url=self._settings.endpoint_url,
        )

    @property
    def session(self) -> boto3.session.Session:
        return self._boto3_session

    @property
    def client(self) -> S3Client:
        return self._boto3_s3_client

    def verify_connection(self) -> bool:
        try:
            self._boto3_s3_client.list_buckets()
        except botocore.exceptions.EndpointConnectionError:
            pass
        else:
            return True
        return False


class S3ExtensionSettings(BaseModel):
    s3: S3Settings


class S3Extension(ExtensionABC):
    def __init__(self, settings: S3ExtensionSettings) -> None:
        self.s3 = S3ExtensionImpl(settings=settings.s3)

    @startup_hook
    async def _s3_startup_hook(self) -> None:
        if not self.s3.verify_connection():
            logger.error("Failed to verify connection")

    @readiness_probe
    async def _s3_readiness_probe(self) -> bool:
        return self.s3.verify_connection()
