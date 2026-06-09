import uuid
from typing import Any

from fastapi import HTTPException, UploadFile, Form
from models.schemas import NoticiaResumo, Noticia, PredictInput, GuardarInput, MoverNoticiaInput

from ..base_router import BaseApiRouter


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
        self.router.add_api_route("/predict", self.predict, methods=["POST"])
        self.router.add_api_route("/predict-ficheiro", self.predict_ficheiro, methods=["POST"])
        self.router.add_api_route("/{noticia_id}/mover", self.mover_noticia, methods=["PUT"])
        self.router.add_api_route("/{noticia_id}/semelhantes", self.noticias_semelhantes, methods=["GET"])
        self.router.add_api_route("/{noticia_id}", self.obter_noticia, methods=["GET"], response_model=Noticia)
        self.router.add_api_route("/{noticia_id}", self.guardar_noticia, methods=["PUT"], response_model=Noticia)
        self.router.add_api_route("/{noticia_id}", self.apagar_noticia, methods=["DELETE"], status_code=204)

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
        from models.schemas import NoticiaAmbos
        noticia_id = self._generate_identifier()
        texto = body.texto.strip()
        titulo = self._build_titulo(texto)

        if body.modo == "ambos":
            import copy
            frases_base = self._sentence_splitter.split_sentences(texto, noticia_id)
            resultado = self._ner_service.run_ner_ambos_por_frases(frases_base)
            frases_xlm = self._graph_builder.assign_entities_to_sentences(
                copy.deepcopy(frases_base), resultado["xlm"]
            )
            frases_gliner = self._graph_builder.assign_entities_to_sentences(
                copy.deepcopy(frases_base), resultado["gliner"]
            )
            return NoticiaAmbos(
                id=noticia_id,
                titulo=titulo,
                frases=frases_xlm,
                frases_gliner=frases_gliner,
                modo="ambos",
            )
        else:
            frases = self._sentence_splitter.split_sentences(texto, noticia_id)
            entidades = self._ner_service.run_ner_por_frases(frases)
            frases = self._graph_builder.assign_entities_to_sentences(frases, entidades)
            return {"id": noticia_id, "titulo": titulo, "frases": frases}

    async def predict_ficheiro(
            self,
            ficheiro: UploadFile,
            pasta_id: str = Form(...),
            modo: str = Form("xlm-roberta"),
    ):
        """
        Recebe um ficheiro .txt ou .pdf, extrai o texto e corre o pipeline NER
        (por frases, igual ao /predict). NÃO guarda no Neo4j.
        """
        from models.schemas import NoticiaAmbos
        import copy

        nome = ficheiro.filename or ""
        conteudo = await ficheiro.read()

        if nome.lower().endswith(".pdf"):
            texto = self._extrair_texto_pdf(conteudo)
        else:
            texto = conteudo.decode("utf-8", errors="ignore")

        texto = texto.strip()
        if not texto:
            raise HTTPException(status_code=400, detail="Ficheiro sem texto extraível.")

        noticia_id = self._generate_identifier()
        titulo = self._build_titulo(texto)

        if modo == "ambos":
            frases_base = self._sentence_splitter.split_sentences(texto, noticia_id)
            resultado = self._ner_service.run_ner_ambos_por_frases(frases_base)
            frases_xlm = self._graph_builder.assign_entities_to_sentences(
                copy.deepcopy(frases_base), resultado["xlm"]
            )
            frases_gliner = self._graph_builder.assign_entities_to_sentences(
                copy.deepcopy(frases_base), resultado["gliner"]
            )
            return NoticiaAmbos(
                id=noticia_id,
                titulo=titulo,
                frases=frases_xlm,
                frases_gliner=frases_gliner,
                modo="ambos",
            )
        else:
            frases = self._sentence_splitter.split_sentences(texto, noticia_id)
            entidades = self._ner_service.run_ner_por_frases(frases)
            frases = self._graph_builder.assign_entities_to_sentences(frases, entidades)
            return {"id": noticia_id, "titulo": titulo, "frases": frases}

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

    def noticias_semelhantes(self, noticia_id: str):
        """Devolve as 3 notícias mais semelhantes à notícia indicada."""
        noticia = self._neo4j_service.get_noticia(noticia_id)
        if not noticia:
            raise HTTPException(status_code=404, detail="Notícia não encontrada")
        return self._neo4j_service.get_noticias_semelhantes(noticia_id)

    def _generate_identifier(self) -> str:
        return str(uuid.uuid4())[:self.IDENTIFIER_LENGTH]

    def _build_titulo(self, texto: str) -> str:
        if len(texto) <= self.TITULO_PREVIEW_LENGTH:
            return texto
        return f"{texto[:self.TITULO_PREVIEW_LENGTH]}..."

    def _extrair_texto_pdf(self, conteudo: bytes) -> str:
        """Extrai texto de um PDF em bytes usando pdfplumber."""
        import io
        import pdfplumber
        texto_paginas = []
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_paginas.append(texto_pagina)
        return "\n".join(texto_paginas)