import uuid
from typing import Any

from fastapi import HTTPException
from models.schemas import (
    Projeto, ProjetoResumo, CriarProjetoInput, AtualizarProjetoInput,
    Pasta, PastaResumo, CriarPastaInput, AtualizarPastaInput, MoverNoticiaInput
)

from .base_router import BaseApiRouter


class ProjetosRouter(BaseApiRouter):
    """Router component responsible for project and folder management endpoints."""

    ROUTER_PREFIX = "/projetos"
    ROUTER_TAGS = ["projetos"]
    IDENTIFIER_LENGTH = 8

    def __init__(self, neo4j_service: Any):
        self._neo4j_service = neo4j_service
        super().__init__(prefix=self.ROUTER_PREFIX, tags=self.ROUTER_TAGS)

    def _register_routes(self) -> None:
        self.router.add_api_route("/todas-as-pastas", self.listar_todas_as_pastas, methods=["GET"])
        self.router.add_api_route("/", self.listar_projetos, methods=["GET"], response_model=list[ProjetoResumo])
        self.router.add_api_route("/{projeto_id}", self.obter_projeto, methods=["GET"], response_model=Projeto)
        self.router.add_api_route(
            "/",
            self.criar_projeto,
            methods=["POST"],
            response_model=Projeto,
            status_code=201,
        )
        self.router.add_api_route(
            "/{projeto_id}",
            self.atualizar_projeto,
            methods=["PUT"],
            response_model=Projeto,
        )
        self.router.add_api_route("/{projeto_id}", self.eliminar_projeto, methods=["DELETE"], status_code=204)
        self.router.add_api_route(
            "/{projeto_id}/pastas/{pasta_id}",
            self.obter_pasta,
            methods=["GET"],
            response_model=Pasta,
        )
        self.router.add_api_route(
            "/{projeto_id}/pastas",
            self.criar_pasta,
            methods=["POST"],
            response_model=Pasta,
            status_code=201,
        )
        self.router.add_api_route(
            "/{projeto_id}/pastas/{pasta_id}",
            self.atualizar_pasta,
            methods=["PUT"],
            response_model=Pasta,
        )
        self.router.add_api_route(
            "/{projeto_id}/pastas/{pasta_id}",
            self.eliminar_pasta,
            methods=["DELETE"],
            status_code=204,
        )
        self.router.add_api_route(
            "/{projeto_id}/pastas/{pasta_id}/noticias/{noticia_id}/mover",
            self.mover_noticia,
            methods=["PUT"],
        )

    def listar_todas_as_pastas(self):
        """Lista todas as pastas de todos os projetos para o modal de mover notícia."""
        return self._neo4j_service.get_all_pastas()

    def listar_projetos(self):
        """Lista todos os projetos com contagem de pastas e notícias."""
        return self._neo4j_service.get_all_projetos()

    def obter_projeto(self, projeto_id: str):
        """Devolve um projeto com as suas pastas."""
        projeto = self._neo4j_service.get_projeto(projeto_id)
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return projeto

    def criar_projeto(self, body: CriarProjetoInput):
        """Cria um novo projeto."""
        projeto_id = self._generate_identifier()
        return self._neo4j_service.create_projeto(projeto_id, body.nome, body.descricao)

    def atualizar_projeto(self, projeto_id: str, body: AtualizarProjetoInput):
        """Atualiza nome e/ou descrição de um projeto."""
        projeto = self._neo4j_service.update_projeto(projeto_id, body.nome, body.descricao)
        if not projeto:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return projeto

    def eliminar_projeto(self, projeto_id: str):
        """Elimina um projeto e as suas pastas (notícias não são apagadas)."""
        if not self._neo4j_service.delete_projeto(projeto_id):
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

    def obter_pasta(self, projeto_id: str, pasta_id: str):
        """Devolve uma pasta com as suas notícias."""
        pasta = self._neo4j_service.get_pasta(pasta_id)
        if not pasta:
            raise HTTPException(status_code=404, detail="Pasta não encontrada")
        return pasta

    def criar_pasta(self, projeto_id: str, body: CriarPastaInput):
        """Cria uma nova pasta dentro de um projeto."""
        pasta_id = self._generate_identifier()
        return self._neo4j_service.create_pasta(pasta_id, body.nome, projeto_id)

    def atualizar_pasta(self, projeto_id: str, pasta_id: str, body: AtualizarPastaInput):
        """Atualiza o nome de uma pasta."""
        pasta = self._neo4j_service.update_pasta(pasta_id, body.nome)
        if not pasta:
            raise HTTPException(status_code=404, detail="Pasta não encontrada")
        return pasta

    def eliminar_pasta(self, projeto_id: str, pasta_id: str):
        """Elimina uma pasta (notícias não são apagadas)."""
        if not self._neo4j_service.delete_pasta(pasta_id):
            raise HTTPException(status_code=404, detail="Pasta não encontrada")

    def mover_noticia(self, projeto_id: str, pasta_id: str, noticia_id: str, body: MoverNoticiaInput):
        """Move uma notícia para outra pasta."""
        sucesso = self._neo4j_service.mover_noticia(noticia_id, body.pasta_id_destino)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Notícia ou pasta não encontrada")
        return {"ok": True}

    def _generate_identifier(self) -> str:
        return str(uuid.uuid4())[:self.IDENTIFIER_LENGTH]
