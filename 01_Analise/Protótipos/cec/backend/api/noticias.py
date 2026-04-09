import uuid
from fastapi import APIRouter, HTTPException
from models.schemas import NoticiaResumo, Noticia, PredictInput, GuardarInput
from services import neo4j_service, ner_service, sentence_splitter, graph_builder

router = APIRouter(prefix="/noticias", tags=["noticias"])


@router.get("/", response_model=list[NoticiaResumo])
def listar_noticias():
    """Devolve a lista resumida de todas as notícias."""
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
    Recebe texto, corre o NER, divide em frases,
    distribui entidades pelas frases e guarda no Neo4j.
    """
    noticia_id = str(uuid.uuid4())[:8]
    texto = body.texto.strip()

    # 1. Correr NER — entidades com offsets relativos ao documento
    entidades_doc = ner_service.run_ner(texto)

    # 2. Dividir texto em frases
    frases = sentence_splitter.split_sentences(texto, noticia_id)

    # 3. Distribuir entidades pelas frases
    frases = graph_builder.assign_entities_to_sentences(frases, entidades_doc)

    # 4. Construir objeto notícia
    noticia = {
        "id": noticia_id,
        "titulo": texto[:60] + ("..." if len(texto) > 60 else ""),
        "frases": frases,
    }

    # 5. Guardar no Neo4j
    neo4j_service.save_noticia(noticia)

    return noticia


@router.put("/{noticia_id}", response_model=Noticia)
def guardar_noticia(noticia_id: str, body: GuardarInput):
    """Guarda edições manuais de uma notícia no Neo4j."""
    if noticia_id != body.id:
        raise HTTPException(status_code=400, detail="ID inconsistente")

    noticia = body.model_dump()
    neo4j_service.save_noticia(noticia)
    return noticia