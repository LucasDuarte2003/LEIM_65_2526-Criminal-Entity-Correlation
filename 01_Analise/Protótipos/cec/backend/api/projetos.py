import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import (
    Projeto, ProjetoResumo, CriarProjetoInput, AtualizarProjetoInput,
    Pasta, PastaResumo, CriarPastaInput, AtualizarPastaInput, MoverNoticiaInput
)
from services import neo4j_service

router = APIRouter(prefix="/projetos", tags=["projetos"])


# ── Rota estática — tem de vir ANTES de /{projeto_id} ───────────

@router.get("/todas-as-pastas")
def listar_todas_as_pastas():
    """Lista todas as pastas de todos os projetos para o modal de mover notícia."""
    return neo4j_service.get_all_pastas()


# ── Projetos ────────────────────────────────────────────────────

@router.get("/", response_model=list[ProjetoResumo])
def listar_projetos():
    """Lista todos os projetos com contagem de pastas e notícias."""
    return neo4j_service.get_all_projetos()


@router.get("/{projeto_id}", response_model=Projeto)
def obter_projeto(projeto_id: str):
    """Devolve um projeto com as suas pastas."""
    projeto = neo4j_service.get_projeto(projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto


@router.post("/", response_model=Projeto, status_code=201)
def criar_projeto(body: CriarProjetoInput):
    """Cria um novo projeto."""
    projeto_id = str(uuid.uuid4())[:8]
    return neo4j_service.create_projeto(projeto_id, body.nome, body.descricao)


@router.put("/{projeto_id}", response_model=Projeto)
def atualizar_projeto(projeto_id: str, body: AtualizarProjetoInput):
    """Atualiza nome e/ou descrição de um projeto."""
    projeto = neo4j_service.update_projeto(projeto_id, body.nome, body.descricao)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto


@router.delete("/{projeto_id}", status_code=204)
def eliminar_projeto(projeto_id: str):
    """Elimina um projeto e as suas pastas (notícias não são apagadas)."""
    if not neo4j_service.delete_projeto(projeto_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")


# ── Pastas ──────────────────────────────────────────────────────

@router.get("/{projeto_id}/pastas/{pasta_id}", response_model=Pasta)
def obter_pasta(projeto_id: str, pasta_id: str):
    """Devolve uma pasta com as suas notícias."""
    pasta = neo4j_service.get_pasta(pasta_id)
    if not pasta:
        raise HTTPException(status_code=404, detail="Pasta não encontrada")
    return pasta


@router.post("/{projeto_id}/pastas", response_model=Pasta, status_code=201)
def criar_pasta(projeto_id: str, body: CriarPastaInput):
    """Cria uma nova pasta dentro de um projeto."""
    pasta_id = str(uuid.uuid4())[:8]
    return neo4j_service.create_pasta(pasta_id, body.nome, projeto_id)


@router.put("/{projeto_id}/pastas/{pasta_id}", response_model=Pasta)
def atualizar_pasta(projeto_id: str, pasta_id: str, body: AtualizarPastaInput):
    """Atualiza o nome de uma pasta."""
    pasta = neo4j_service.update_pasta(pasta_id, body.nome)
    if not pasta:
        raise HTTPException(status_code=404, detail="Pasta não encontrada")
    return pasta


@router.delete("/{projeto_id}/pastas/{pasta_id}", status_code=204)
def eliminar_pasta(projeto_id: str, pasta_id: str):
    """Elimina uma pasta (notícias não são apagadas)."""
    if not neo4j_service.delete_pasta(pasta_id):
        raise HTTPException(status_code=404, detail="Pasta não encontrada")


# ── Notícias dentro de pastas ───────────────────────────────────

@router.put("/{projeto_id}/pastas/{pasta_id}/noticias/{noticia_id}/mover")
def mover_noticia(projeto_id: str, pasta_id: str, noticia_id: str, body: MoverNoticiaInput):
    """Move uma notícia para outra pasta."""
    sucesso = neo4j_service.mover_noticia(noticia_id, body.pasta_id_destino)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Notícia ou pasta não encontrada")
    return {"ok": True}