from typing import Any

from litestar import MediaType, Request, get
from litestar.openapi import OpenAPIController as _OpenAPIController
from litestar.response.base import ASGIResponse


class OpenAPIController(_OpenAPIController):
    path = "/schema"

    @get(path="/openapi", include_in_schema=False, sync_to_thread=False)
    def swagger_ui(self, request: Request[Any, Any, Any]) -> ASGIResponse:
        return ASGIResponse(
            body=self.render_swagger_ui(request),
            media_type=MediaType.HTML,
        )
