from typing import Any, Optional

from fastapi import HTTPException

from ..base_router import BaseApiRouter


class InvestigarRouter(BaseApiRouter):
    """Router component responsible for entity investigation endpoints."""

    ROUTER_PREFIX = "/investigar"
    ROUTER_TAGS = ["investigar"]

    def __init__(self, neo4j_service: Any):
        self._neo4j_service = neo4j_service
        super().__init__(prefix=self.ROUTER_PREFIX, tags=self.ROUTER_TAGS)

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.investigar, methods=["GET"])

    def investigar(self, nome: str, tipo: Optional[str] = None, ambito: str = "global"):
        """
        Pesquisa uma entidade pelo nome e devolve:
        - as notícias onde aparece
        - o grafo de co-ocorrências
        - entidades que co-ocorrem com ela (para cruzamento)
        """
        if not nome or not nome.strip():
            raise HTTPException(status_code=400, detail="Nome da entidade obrigatório")
        return self._neo4j_service.get_investigar(nome.strip(), tipo, ambito)