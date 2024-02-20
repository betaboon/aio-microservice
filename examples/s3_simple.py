import io
from uuid import UUID, uuid4

from aio_microservice import (
    Service,
    ServiceSettings,
    http,
    readiness_probe,
    startup_hook,
)
from aio_microservice.s3 import S3Extension, S3ExtensionSettings


class MySettings(ServiceSettings, S3ExtensionSettings):
    bucket_name: str = "example-bucket"


class MyService(Service[MySettings], S3Extension):
    def bucket_exists(self) -> bool:
        response = self.s3.client.list_buckets()
        existing_bucket_names = [b["Name"] for b in response["Buckets"]]
        return self.settings.bucket_name in existing_bucket_names

    @startup_hook
    async def create_s3_bucket(self) -> None:
        if self.bucket_exists():
            return
        self.s3.client.create_bucket(Bucket=self.settings.bucket_name)

    @readiness_probe
    async def bucket_exists_readiness_probe(self) -> bool:
        return self.bucket_exists()

    @http.post(path="/store-text")
    async def post_store_text(self, content: str) -> UUID:
        file_id = uuid4()
        file_obj = io.BytesIO(content.encode())
        self.s3.client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.settings.bucket_name,
            Key=f"{file_id}.txt",
        )
        return file_id


if __name__ == "__main__":
    MyService.cli()
