from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class CorsConfiguration:
    """Configures CORS once at the application composition root."""

    DEFAULT_ALLOWED_ORIGIN = "http://localhost:5173"
    DEFAULT_ALLOW_ALL = ["*"]

    def __init__(self, allow_origins: Optional[list[str]] = None, allow_methods: Optional[list[str]] = None,
                 allow_headers: Optional[list[str]] = None):
        self._allow_origins = list(allow_origins or [self.DEFAULT_ALLOWED_ORIGIN])
        self._allow_methods = list(allow_methods or self.DEFAULT_ALLOW_ALL)
        self._allow_headers = list(allow_headers or self.DEFAULT_ALLOW_ALL)

    def apply(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self._allow_origins,
            allow_methods=self._allow_methods,
            allow_headers=self._allow_headers,
        )


