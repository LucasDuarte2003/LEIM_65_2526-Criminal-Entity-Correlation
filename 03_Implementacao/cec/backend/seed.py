"""
Popula o Neo4j de raiz a partir do dataset_anotado.json.
Cria um projeto e pasta default e liga todas as notícias.
Corre uma vez: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from dotenv import load_dotenv
load_dotenv()

from services.neo4j_service import (
    get_driver, init_labels, save_noticia,
    create_projeto, create_pasta, ligar_noticia_a_pasta
)
from services.sentence_splitter import split_sentences
from services.graph_builder import assign_entities_to_sentences

DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "ner_model", "data", "dataset_anotado.json"
)

# IDs fixos para o projeto e pasta default
PROJETO_DEFAULT_ID = "default"
PASTA_DEFAULT_ID   = "default"


def converter_entidade(ent_json: dict) -> dict:
    return {
        "nome": ent_json["text"],
        "tipo": ent_json["label"],
        "inicio": ent_json["start"],
        "fim": ent_json["end"],
    }


def limpar_grafo(session):
    session.run("MATCH (n) DETACH DELETE n")
    print("Grafo limpo.")


def criar_estrutura_default():
    """Cria o projeto e pasta default se não existirem."""
    create_projeto(PROJETO_DEFAULT_ID, "Projeto Default", "Notícias importadas automaticamente")
    create_pasta(PASTA_DEFAULT_ID, "Geral", PROJETO_DEFAULT_ID)
    print("Projeto e pasta default criados.")


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if isinstance(dataset, dict):
        dataset = [dataset]

    driver = get_driver()

    with driver.session(database="cec") as session:
        limpar_grafo(session)

    init_labels()
    print("Labels inicializadas.")

    criar_estrutura_default()

    for item in dataset:
        noticia_id = item["id"].strip()
        texto = item["text"]

        entidades_doc = [converter_entidade(e) for e in item["entities"]]
        frases = split_sentences(texto, noticia_id)
        frases = assign_entities_to_sentences(frases, entidades_doc)

        noticia = {
            "id": noticia_id,
            "titulo": texto[:60] + ("..." if len(texto) > 60 else ""),
            "frases": frases,
        }

        save_noticia(noticia)
        ligar_noticia_a_pasta(noticia_id, PASTA_DEFAULT_ID)

        total_ents = sum(len(f["entidades"]) for f in frases)
        print(f"  ✓ {noticia_id} — {len(frases)} frases, {total_ents} entidades")

    print("\nBase de dados populada com sucesso!")


if __name__ == "__main__":
    main()