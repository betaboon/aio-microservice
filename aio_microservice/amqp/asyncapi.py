from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.site import get_asyncapi_html
from litestar import Controller, MediaType, get


def make_asyncapi_controller(
    app: FastStream,
    path: str = "/schema",
) -> type[Controller]:
    routes_path = path

    class _AsyncAPIController(Controller):
        path: str = routes_path

        @get(
            path="/asyncapi",
            media_type=MediaType.HTML,
            include_in_schema=False,
            sync_to_thread=False,
        )
        def root(
            self,
            sidebar: bool = True,
            info: bool = True,
            servers: bool = True,
            operations: bool = True,
            messages: bool = True,
            schemas: bool = True,
            errors: bool = True,
            expand_message_examples: bool = True,
        ) -> str:
            schema = get_app_schema(app)
            return get_asyncapi_html(
                schema=schema,
                sidebar=sidebar,
                info=info,
                servers=servers,
                operations=operations,
                messages=messages,
                schemas=schemas,
                errors=errors,
                expand_message_examples=expand_message_examples,
                title=schema.info.title,
            )

        @get(
            path="/asyncapi.json",
            media_type=MediaType.JSON,
            include_in_schema=False,
            sync_to_thread=False,
        )
        def retrieve_schema_json(self) -> str:
            schema = get_app_schema(app)
            return schema.to_json()

        @get(
            path=["/asyncapi.yaml", "asyncapi.yml"],
            media_type="application/yaml",
            include_in_schema=False,
            sync_to_thread=False,
        )
        def retrieve_schema_yaml(self) -> str:
            schema = get_app_schema(app)
            return schema.to_yaml()

    return _AsyncAPIController
