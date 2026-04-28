from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/modelo", tags=["modelo"])

# Importado aqui para evitar circular imports
def get_manager():
    from ner_model.ner_manager import ner_manager
    return ner_manager

def get_trainer():
    from main import trainer
    return trainer


@router.get("/status")
def obter_status():
    """Devolve o estado atual do modelo."""
    return get_manager().get_status()


@router.post("/retreinar")
def retreinar(background_tasks: BackgroundTasks):
    """Lança um retreino manual em background."""
    manager = get_manager()
    if manager._a_treinar:
        raise HTTPException(status_code=409, detail="Retreino já em curso.")
    trainer = get_trainer()
    background_tasks.add_task(trainer.treinar_agora)
    return {"ok": True, "mensagem": "Retreino iniciado em background."}


class AlterarTipoInput(BaseModel):
    tipo: str  # "xlm-roberta" | "gliner"


@router.post("/tipo")
def alterar_tipo(body: AlterarTipoInput):
    """Alterna entre xlm-roberta e gliner."""
    try:
        get_manager().set_tipo(body.tipo)
        return {"ok": True, "tipo": body.tipo}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))