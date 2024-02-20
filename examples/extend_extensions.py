from pydantic import Field

from aio_microservice import Service, ServiceSettings, startup_hook
from aio_microservice.s3 import S3Extension, S3ExtensionSettings


class MyS3ExtensionSettings(S3ExtensionSettings):
    s3_bucket_name: str = Field(default="example-bucket", description="bucket to create")


class MyS3Extension(S3Extension):
    def __init__(self, settings: MyS3ExtensionSettings) -> None:
        super().__init__(settings=settings)
        self._my_bucket_name = settings.s3_bucket_name

    @startup_hook
    async def _my_s3_extension_startup_hook(self) -> None:
        self.s3.client.create_bucket(Bucket=self._my_bucket_name)


class MyServiceSettings(ServiceSettings, MyS3ExtensionSettings): ...


class MyService(Service[MyServiceSettings], MyS3Extension): ...


if __name__ == "__main__":
    MyService.cli()
