import json
from neo4j import GraphDatabase

# --- Configuração ---
URI      = "bolt://localhost:7687"
USER     = "neo4j"
PASSWORD = "cec12345"
JSON_PATH = "sample_data/dataset_anotado.json"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def load_data(tx, noticia, pares):
    # 1. Cria o nó Noticia
    tx.run("""
        MERGE (n:Noticia {id: $id})
        SET n.texto = $texto
    """, id=noticia["id"], texto=noticia["text"][:500])

    # 2. Cria cada entidade e liga à notícia
    for ent in noticia["entities"]:
        tx.run("""
            MERGE (e:Entidade {nome: $nome, tipo: $tipo})
            MERGE (n:Noticia {id: $id})
            MERGE (e)-[:MENCIONADA_EM]->(n)
        """, nome=ent["text"], tipo=ent["label"], id=noticia["id"])

    # 3. Liga entidades que co-ocorrem na mesma notícia
    for (nome1, tipo1), (nome2, tipo2) in pares:
        tx.run("""
            MERGE (a:Entidade {nome: $nome1, tipo: $tipo1})
            MERGE (b:Entidade {nome: $nome2, tipo: $tipo2})
            MERGE (a)-[:CO_OCORRE_COM {noticia_id: $nid}]->(b)
        """, nome1=nome1, tipo1=tipo1, nome2=nome2, tipo2=tipo2, nid=noticia["id"])


def gerar_pares(entidades):
    """Gera pares únicos de entidades de tipos diferentes."""
    pares = []
    vistos = set()
    for i, e1 in enumerate(entidades):
        for e2 in entidades[i+1:]:
            if e1["label"] == e2["label"]:
                continue
            chave = tuple(sorted([(e1["text"], e1["label"]), (e2["text"], e2["label"])]))
            if chave not in vistos:
                vistos.add(chave)
                pares.append(chave)
    return pares


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    with driver.session(database="cec") as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Grafo limpo.")

        for noticia in data:
            pares = gerar_pares(noticia["entities"])
            session.execute_write(load_data, noticia, pares)
            print(f"Notícia {noticia['id']} — {len(noticia['entities'])} entidades, {len(pares)} pares")

    print("\nGrafo populado com sucesso!")
    driver.close()


if __name__ == "__main__":
    main()