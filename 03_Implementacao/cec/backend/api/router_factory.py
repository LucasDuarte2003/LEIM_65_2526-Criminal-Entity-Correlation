from typing import Any

from fastapi import APIRouter

from .routes.grafo import GrafoRouter
from .routes.labels import LabelsRouter
from .routes.modelo import ModeloRouter
from .routes.noticias import NoticiasRouter
from .routes.projetos import ProjetosRouter


class RouterFactory:
    """Builds the aggregated API router for the FastAPI application."""

    API_PREFIX = "/api"

    def __init__(self, neo4j_service: Any, ner_service: Any, sentence_splitter: Any, graph_builder: Any,
                 ner_manager: Any, trainer: Any):
        self._neo4j_service = neo4j_service
        self._ner_service = ner_service
        self._sentence_splitter = sentence_splitter
        self._graph_builder = graph_builder
        self._ner_manager = ner_manager
        self._trainer = trainer

    def create_router(self) -> APIRouter:
        api_router = APIRouter(prefix=self.API_PREFIX)
        for feature_router in self._build_feature_routers():
            api_router.include_router(feature_router)
        return api_router

    def _build_feature_routers(self) -> list[APIRouter]:
        return [
            NoticiasRouter(
                neo4j_service=self._neo4j_service,
                ner_service=self._ner_service,
                sentence_splitter=self._sentence_splitter,
                graph_builder=self._graph_builder,
                trainer=self._trainer,
            ).router,
            LabelsRouter(neo4j_service=self._neo4j_service).router,
            GrafoRouter(neo4j_service=self._neo4j_service).router,
            ProjetosRouter(neo4j_service=self._neo4j_service).router,
            ModeloRouter(ner_manager=self._ner_manager, trainer=self._trainer).router,
        ]