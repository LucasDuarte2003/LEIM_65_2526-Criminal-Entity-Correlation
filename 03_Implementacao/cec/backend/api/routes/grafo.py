from typing import Any

from fastapi import HTTPException
from models.schemas import GrafoFrase
from pydantic import BaseModel

from ..base_router import BaseApiRouter


class RelacionadasInput(BaseModel):
    nos: list[str]
    ambito: str = "global"  # "documento" | "pasta" | "projeto" | "global"


class FundirInput(BaseModel):
    frase_ids: list[str]


class GrafoRouter(BaseApiRouter):
    """Router component responsible for graph exploration endpoints."""

    ROUTER_PREFIX = "/grafo"
    ROUTER_TAGS = ["grafo"]
    FRASES_PARA_FUSAO = 2

    def __init__(self, neo4j_service: Any):
        self._neo4j_service = neo4j_service
        super().__init__(prefix=self.ROUTER_PREFIX, tags=self.ROUTER_TAGS)

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "/frase/{frase_id}",
            self.grafo_frase,
            methods=["GET"],
            response_model=GrafoFrase,
        )
        self.router.add_api_route("/frase/{frase_id}/relacionadas", self.grafo_relacionadas, methods=["POST"])
        self.router.add_api_route("/frases/fundir", self.grafo_fundir, methods=["POST"])

    def grafo_frase(self, frase_id: str):
        """
        Devolve os nós e arestas de uma frase específica
        para renderizar o grafo interativo no frontend.
        """
        grafo = self._neo4j_service.get_grafo_frase(frase_id)
        if not grafo["nos"]:
            raise HTTPException(status_code=404, detail="Frase sem relações")
        return grafo

    def grafo_relacionadas(self, frase_id: str, body: RelacionadasInput):
        """
        Procura entidades noutras frases que co-ocorram
        com os nós visíveis, filtrado pelo âmbito escolhido.
        """
        if not body.nos:
            raise HTTPException(status_code=400, detail="Lista de nós vazia")
        return self._neo4j_service.get_grafo_relacionadas(frase_id, body.nos, body.ambito)

    def grafo_fundir(self, body: FundirInput):
        """
        Devolve o grafo combinado de duas frases.
        Não altera a base de dados.
        """
        if len(body.frase_ids) != self.FRASES_PARA_FUSAO:
            raise HTTPException(status_code=400, detail="Exactamente 2 frases necessárias")
        return self._neo4j_service.get_grafo_frases_fundidas(body.frase_ids)
