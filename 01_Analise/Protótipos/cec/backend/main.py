from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import noticias, labels, grafo
from services import neo4j_service

app = FastAPI(title="Criminal Entity Correlation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Regista os routers
app.include_router(noticias.router, prefix="/api")
app.include_router(labels.router, prefix="/api")
app.include_router(grafo.router, prefix="/api")


@app.on_event("startup")
def startup():
    """Inicializa labels no Neo4j se ainda não existirem."""
    neo4j_service.init_labels()
    print("CEC API pronta.")


@app.get("/")
def root():
    return {"status": "ok", "app": "Criminal Entity Correlation"}