import uuid
from typing import Any

from fastapi import HTTPException
from models.schemas import NoticiaResumo, Noticia, PredictInput, GuardarInput, MoverNoticiaInput

from .base_router import BaseApiRouter


class NoticiasRouter(BaseApiRouter):
    """Router component responsible for news processing and persistence endpoints."""

    ROUTER_PREFIX = "/noticias"
    ROUTER_TAGS = ["noticias"]
    TITULO_PREVIEW_LENGTH = 60
    IDENTIFIER_LENGTH = 8

    def __init__(self, neo4j_service: Any, ner_service: Any, sentence_splitter: Any, graph_builder: Any,
                 trainer: Any):
        self._neo4j_service = neo4j_service
        self._ner_service = ner_service
        self._sentence_splitter = sentence_splitter
        self._graph_builder = graph_builder
        self._trainer = trainer
        super().__init__(prefix=self.ROUTER_PREFIX, tags=self.ROUTER_TAGS)

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.listar_noticias, methods=["GET"], response_model=list[NoticiaResumo])
        self.router.add_api_route(
            "/{noticia_id}",
            self.obter_noticia,
            methods=["GET"],
            response_model=Noticia,
        )
        self.router.add_api_route("/predict", self.predict, methods=["POST"], response_model=Noticia)
        self.router.add_api_route(
            "/{noticia_id}",
            self.guardar_noticia,
            methods=["PUT"],
            response_model=Noticia,
        )
        self.router.add_api_route("/{noticia_id}", self.apagar_noticia, methods=["DELETE"], status_code=204)
        self.router.add_api_route("/{noticia_id}/mover", self.mover_noticia, methods=["PUT"])

    def listar_noticias(self):
        """Devolve todas as notícias (usado no seed/debug)."""
        return self._neo4j_service.get_all_noticias()

    def obter_noticia(self, noticia_id: str):
        """Devolve uma notícia completa com frases e entidades."""
        noticia = self._neo4j_service.get_noticia(noticia_id)
        if not noticia:
            raise HTTPException(status_code=404, detail="Notícia não encontrada")
        return noticia

    def predict(self, body: PredictInput):
        """
        Recebe texto, corre o NER e devolve a notícia processada.
        NÃO guarda no Neo4j — o utilizador revê e clica em Guardar.
        """
        noticia_id = self._generate_identifier()
        texto = body.texto.strip()
        entidades_documento = self._ner_service.run_ner(texto)
        frases = self._sentence_splitter.split_sentences(texto, noticia_id)
        frases = self._graph_builder.assign_entities_to_sentences(frases, entidades_documento)
        return {"id": noticia_id, "titulo": self._build_titulo(texto), "frases": frases}

    def guardar_noticia(self, noticia_id: str, body: GuardarInput):
        if noticia_id != body.id:
            raise HTTPException(status_code=400, detail="ID inconsistente")
        noticia = body.model_dump()
        self._neo4j_service.save_noticia(noticia)
        if body.pasta_id:
            self._neo4j_service.ligar_noticia_a_pasta(noticia_id, body.pasta_id)
        self._trainer.notificar_nova_noticia()
        return noticia

    def apagar_noticia(self, noticia_id: str):
        """Apaga uma notícia e tudo o que lhe está associado."""
        self._neo4j_service.delete_noticia(noticia_id)

    def mover_noticia(self, noticia_id: str, body: MoverNoticiaInput):
        """Move uma notícia para outra pasta."""
        sucesso = self._neo4j_service.mover_noticia(noticia_id, body.pasta_id_destino)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Notícia ou pasta não encontrada")
        return {"ok": True}

    def _generate_identifier(self) -> str:
        return str(uuid.uuid4())[:self.IDENTIFIER_LENGTH]

    def _build_titulo(self, texto: str) -> str:
        if len(texto) <= self.TITULO_PREVIEW_LENGTH:
            return texto
        return f"{texto[:self.TITULO_PREVIEW_LENGTH]}..."
