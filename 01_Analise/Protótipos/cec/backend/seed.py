"""
Popula o Neo4j de raiz a partir do dataset_anotado.json.
Corre uma vez: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from dotenv import load_dotenv
load_dotenv()

from services.neo4j_service import get_driver, init_labels, save_noticia
from services.sentence_splitter import split_sentences
from services.graph_builder import assign_entities_to_sentences

# Aponta para o dataset_anotado.json do ner_model
DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "ner_model", "data", "dataset_anotado.json"
)


def converter_entidade(ent_json: dict) -> dict:
    """Converte formato do dataset_anotado para formato interno."""
    return {
        "nome": ent_json["text"],
        "tipo": ent_json["label"],
        "inicio": ent_json["start"],
        "fim": ent_json["end"],
    }


def limpar_grafo(session):
    session.run("MATCH (n) DETACH DELETE n")
    print("Grafo limpo.")


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if isinstance(dataset, dict):
        dataset = [dataset]

    driver = get_driver()

    with driver.session(database="cec") as session:
        limpar_grafo(session)

    # Inicializa labels com cores
    init_labels()
    print("Labels inicializadas.")

    for item in dataset:
        noticia_id = item["id"]
        texto = item["text"]

        # Converte entidades do formato dataset para formato interno
        entidades_doc = [converter_entidade(e) for e in item["entities"]]

        # Divide em frases
        frases = split_sentences(texto, noticia_id)

        # Distribui entidades pelas frases usando offsets
        frases = assign_entities_to_sentences(frases, entidades_doc)

        noticia = {
            "id": noticia_id,
            "titulo": texto[:60] + ("..." if len(texto) > 60 else ""),
            "frases": frases,
        }

        save_noticia(noticia)
        total_ents = sum(len(f["entidades"]) for f in frases)
        print(f"  ✓ {noticia_id} — {len(frases)} frases, {total_ents} entidades")

    print("\nBase de dados populada com sucesso!")


if __name__ == "__main__":
    main()