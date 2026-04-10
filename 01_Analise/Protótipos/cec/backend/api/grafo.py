from fastapi import APIRouter, HTTPException
from models.schemas import GrafoFrase
from services import neo4j_service
from pydantic import BaseModel
router = APIRouter(prefix="/grafo", tags=["grafo"])


@router.get("/frase/{frase_id}", response_model=GrafoFrase)
def grafo_frase(frase_id: str):
    """
    Devolve os nós e arestas de uma frase específica
    para renderizar o grafo interativo no frontend.
    """
    grafo = neo4j_service.get_grafo_frase(frase_id)
    if not grafo["nos"]:
        raise HTTPException(status_code=404, detail="Frase sem relações")
    return grafo


class RelacionadasInput(BaseModel):
    nos: list[str]

@router.post("/frase/{frase_id}/relacionadas")
def grafo_relacionadas(frase_id: str, body: RelacionadasInput):
    """
    Procura entidades noutras notícias que co-ocorram
    com os nós visíveis atualmente no grafo.
    """
    if not body.nos:
        raise HTTPException(status_code=400, detail="Lista de nós vazia")

    resultado = neo4j_service.get_grafo_relacionadas(frase_id, body.nos)
    return resultado