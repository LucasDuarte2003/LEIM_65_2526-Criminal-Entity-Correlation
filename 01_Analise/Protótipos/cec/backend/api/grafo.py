from fastapi import APIRouter, HTTPException
from models.schemas import GrafoFrase
from services import neo4j_service

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