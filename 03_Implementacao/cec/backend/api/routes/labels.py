from typing import Any

from models.schemas import Label

from ..base_router import BaseApiRouter


class LabelsRouter(BaseApiRouter):
    """Router component responsible for label endpoints."""

    ROUTER_PREFIX = "/labels"
    ROUTER_TAGS = ["labels"]

    def __init__(self, neo4j_service: Any):
        self._neo4j_service = neo4j_service
        super().__init__(prefix=self.ROUTER_PREFIX, tags=self.ROUTER_TAGS)

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.listar_labels, methods=["GET"], response_model=list[Label])

    def listar_labels(self):
        """Devolve todas as labels com as suas cores."""
        return self._neo4j_service.get_all_labels()
