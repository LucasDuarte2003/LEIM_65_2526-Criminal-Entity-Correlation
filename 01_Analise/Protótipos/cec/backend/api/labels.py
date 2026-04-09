from fastapi import APIRouter
from models.schemas import Label
from services import neo4j_service

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("/", response_model=list[Label])
def listar_labels():
    """Devolve todas as labels com as suas cores."""
    return neo4j_service.get_all_labels()