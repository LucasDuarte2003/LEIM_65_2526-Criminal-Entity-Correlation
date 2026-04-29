from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from api import CorsConfiguration, RouterFactory
from ner_model.ner_manager import ner_manager
from ner_model.trainer import Trainer
from services import graph_builder, neo4j_service, ner_service, sentence_splitter


class ApplicationRuntime:
    """Coordinates runtime services that must be started with the application."""

    APPLICATION_TITLE = "Criminal Entity Correlation API"
    READY_MESSAGE = "CEC API pronta."

    def __init__(self):
        self._ner_manager = ner_manager
        self._neo4j_service = neo4j_service
        self.trainer = Trainer(self._ner_manager, self._neo4j_service)

    def startup(self) -> None:
        self._ner_manager.carregar_modelo_inicial()
        self.trainer.iniciar()
        self._neo4j_service.init_labels()
        print(self.READY_MESSAGE)

    def shutdown(self) -> None:
        self.trainer.parar()


runtime = ApplicationRuntime()
app = FastAPI(title=ApplicationRuntime.APPLICATION_TITLE)

CorsConfiguration().apply(app)
app.include_router(
    RouterFactory(
        neo4j_service=neo4j_service,
        ner_service=ner_service,
        sentence_splitter=sentence_splitter,
        graph_builder=graph_builder,
        ner_manager=ner_manager,
        trainer=runtime.trainer,
    ).create_router()
)

@app.on_event("startup")
def startup() -> None:
    runtime.startup()


@app.on_event("shutdown")
def shutdown() -> None:
    runtime.shutdown()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "app": "Criminal Entity Correlation"}