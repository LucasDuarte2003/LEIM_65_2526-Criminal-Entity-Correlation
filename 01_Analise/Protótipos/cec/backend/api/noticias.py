import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import NoticiaResumo, Noticia, PredictInput, GuardarInput, MoverNoticiaInput
from services import neo4j_service, ner_service, sentence_splitter, graph_builder

router = APIRouter(prefix="/noticias", tags=["noticias"])


@router.get("/", response_model=list[NoticiaResumo])
def listar_noticias():
    """Devolve todas as notícias (usado no seed/debug)."""
    return neo4j_service.get_all_noticias()


@router.get("/{noticia_id}", response_model=Noticia)
def obter_noticia(noticia_id: str):
    """Devolve uma notícia completa com frases e entidades."""
    noticia = neo4j_service.get_noticia(noticia_id)
    if not noticia:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return noticia


@router.post("/predict", response_model=Noticia)
def predict(body: PredictInput):
    """
    Recebe texto e pasta_id, corre o NER, divide em frases,
    guarda no Neo4j e liga à pasta indicada.
    """
    noticia_id = str(uuid.uuid4())[:8]
    texto = body.texto.strip()

    entidades_doc = ner_service.run_ner(texto)
    frases = sentence_splitter.split_sentences(texto, noticia_id)
    frases = graph_builder.assign_entities_to_sentences(frases, entidades_doc)

    noticia = {
        "id": noticia_id,
        "titulo": texto[:60] + ("..." if len(texto) > 60 else ""),
        "frases": frases,
    }

    neo4j_service.save_noticia(noticia)
    neo4j_service.ligar_noticia_a_pasta(noticia_id, body.pasta_id)

    return noticia


@router.put("/{noticia_id}", response_model=Noticia)
def guardar_noticia(noticia_id: str, body: GuardarInput):
    """Guarda edições manuais de uma notícia no Neo4j."""
    if noticia_id != body.id:
        raise HTTPException(status_code=400, detail="ID inconsistente")
    noticia = body.model_dump()
    neo4j_service.save_noticia(noticia)
    return noticia


@router.delete("/{noticia_id}", status_code=204)
def apagar_noticia(noticia_id: str):
    """Apaga uma notícia e tudo o que lhe está associado."""
    neo4j_service.delete_noticia(noticia_id)


@router.put("/{noticia_id}/mover")
def mover_noticia(noticia_id: str, body: MoverNoticiaInput):
    """Move uma notícia para outra pasta."""
    sucesso = neo4j_service.mover_noticia(noticia_id, body.pasta_id_destino)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Notícia ou pasta não encontrada")
    return {"ok": True}