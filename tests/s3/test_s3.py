import io
import uuid

import pytest
from pydantic import SecretStr
from testcontainers_on_whales.minio import MinioContainer

from aio_microservice import Service, ServiceSettings, http, startup_hook
from aio_microservice.http import TestHttpClient
from aio_microservice.s3 import S3Extension, S3ExtensionSettings, S3Settings


async def test_s3_client() -> None:
    class TestSettings(ServiceSettings, S3ExtensionSettings):
        bucket_name: str = "test-bucket"

    class TestService(Service[TestSettings], S3Extension):
        @startup_hook
        async def create_s3_bucket(self) -> None:
            self.s3.client.create_bucket(Bucket=self.settings.bucket_name)

        @http.post(path="/test-upload")
        async def post_upload(self, content: str) -> str:
            file_id = uuid.uuid4()
            file_obj = io.BytesIO(content.encode())
            self.s3.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.settings.bucket_name,
                Key=f"{file_id}.txt",
            )
            return str(file_id)

    with MinioContainer() as container:
        container.wait_ready(timeout=120)

        settings = TestSettings(
            s3=S3Settings(
                endpoint_url=container.get_connection_url(),
                access_key_id=container.username,
                secret_access_key=SecretStr(container.password),
            ),
        )

        service = TestService(settings=settings)

        async with TestHttpClient(service=service) as http_client:
            response_post = await http_client.post("/test-upload?content=TEST-CONTENT")
            assert response_post.status_code == http.status_codes.HTTP_201_CREATED

            response_list_objects = service.s3.client.list_objects(
                Bucket=service.settings.bucket_name,
            )
            object_keys = [c["Key"] for c in response_list_objects["Contents"]]
            assert f"{response_post.text}.txt" in object_keys


async def test_s3_connection_verification_on_startup(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class TestSettings(ServiceSettings, S3ExtensionSettings): ...

    class TestService(Service[TestSettings], S3Extension): ...

    settings = TestSettings(
        s3=S3Settings(
            endpoint_url="http://localhost:12345",
            access_key_id="somerandomid",
            secret_access_key=SecretStr("somerandomsecret"),
        ),
    )

    service = TestService(settings=settings)

    async with TestHttpClient(service=service):
        pass

    assert "Failed to verify connection" in caplog.text


async def test_s3_readiness_probe() -> None:
    class TestSettings(ServiceSettings, S3ExtensionSettings): ...

    class TestService(Service[TestSettings], S3Extension): ...

    container = MinioContainer()
    container.start()
    container.wait_ready(timeout=120)

    settings = TestSettings(
        s3=S3Settings(
            endpoint_url=container.get_connection_url(),
            access_key_id=container.username,
            secret_access_key=SecretStr(container.password),
        ),
    )

    service = TestService(settings=settings)

    async with TestHttpClient(service=service) as http_client:
        response_running = await http_client.get("/readiness")

        container.stop()
        container.wait_exited(timeout=10)

        response_stopped = await http_client.get("/readiness")

        assert response_running.status_code == http.status_codes.HTTP_200_OK
        assert response_stopped.status_code == http.status_codes.HTTP_503_SERVICE_UNAVAILABLE
