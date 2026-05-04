from typing import Any

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel

from ..base_router import BaseApiRouter

class AlterarTipoInput(BaseModel):
    tipo: str  # "xlm-roberta" | "gliner"


class ModeloRouter(BaseApiRouter):
    """Router component responsible for NER model management endpoints."""

    ROUTER_PREFIX = "/modelo"
    ROUTER_TAGS = ["modelo"]

    def __init__(self, ner_manager: Any, trainer: Any):
        self._ner_manager = ner_manager
        self._trainer = trainer
        super().__init__(prefix=self.ROUTER_PREFIX, tags=self.ROUTER_TAGS)

    def _register_routes(self) -> None:
        self.router.add_api_route("/status", self.obter_status, methods=["GET"])
        self.router.add_api_route("/retreinar", self.retreinar, methods=["POST"])
        self.router.add_api_route("/tipo", self.alterar_tipo, methods=["POST"])

    def obter_status(self):
        """Devolve o estado atual do modelo."""
        return self._ner_manager.get_status()

    def retreinar(self, background_tasks: BackgroundTasks):
        """Lança um retreino manual em background."""
        if self._ner_manager._a_treinar:
            raise HTTPException(status_code=409, detail="Retreino já em curso.")
        if self._trainer is None:
            raise HTTPException(status_code=503, detail="Trainer não configurado.")
        background_tasks.add_task(self._trainer.treinar_agora)
        return {"ok": True, "mensagem": "Retreino iniciado em background."}

    def alterar_tipo(self, body: AlterarTipoInput):
        """Alterna entre xlm-roberta e gliner."""
        try:
            self._ner_manager.set_tipo(body.tipo)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"ok": True, "tipo": body.tipo}
