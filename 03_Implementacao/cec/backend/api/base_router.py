from fastapi import APIRouter


class BaseApiRouter:
    """Base stereotype for API components that expose a FastAPI router."""

    def __init__(self, prefix: str, tags: list[str]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self._register_routes()

    def _register_routes(self) -> None:
        raise NotImplementedError("API routers must register their routes.")

