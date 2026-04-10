import os
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from services.graph_builder import build_cooccurrences

# --- Ligação ---

URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    return _driver


# --- Notícias ---
def get_all_noticias() -> List[Dict]:
    """Devolve lista resumida de notícias (id + titulo)."""
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (n:Noticia)
            RETURN n.id AS id,
                   COALESCE(n.titulo, left(n.texto, 60)) AS titulo
        """)
        return [{"id": r["id"], "titulo": r["titulo"] or r["id"]} for r in result]


def get_noticia(noticia_id: str) -> Optional[Dict]:
    """Devolve notícia completa com frases e entidades."""
    with get_driver().session(database="cec") as session:

        frases_result = session.run("""
            MATCH (n:Noticia {id: $id})-[:TEM_FRASE]->(f:Frase)
            RETURN f.id AS id, f.texto AS texto, f.ordem AS ordem,
                   f.noticia_id AS noticia_id
            ORDER BY f.ordem
        """, id=noticia_id)

        frases = []
        for row in frases_result:
            frase = {
                "id": row["id"],
                "texto": row["texto"],
                "ordem": row["ordem"],
                "noticia_id": row["noticia_id"] or noticia_id,
                "entidades": []
            }

            # Busca entidades — inicio/fim estão na relação, não no nó
            ents_result = session.run("""
                MATCH (e:Entidade)-[r:MENCIONADA_EM]->(f:Frase {id: $frase_id})
                RETURN e.nome AS nome, e.tipo AS tipo,
                       r.inicio AS inicio, r.fim AS fim
            """, frase_id=frase["id"])

            frase["entidades"] = [
                {
                    "nome": r["nome"],
                    "tipo": r["tipo"],
                    "inicio": r["inicio"] if r["inicio"] is not None else 0,
                    "fim": r["fim"] if r["fim"] is not None else 0,
                }
                for r in ents_result
            ]
            frases.append(frase)

        if not frases:
            return None

        noticia_result = session.run(
            "MATCH (n:Noticia {id: $id}) RETURN n.titulo AS titulo",
            id=noticia_id
        )
        row = noticia_result.single()
        titulo = row["titulo"] if row and row["titulo"] else noticia_id

        return {"id": noticia_id, "titulo": titulo, "frases": frases}


def save_noticia(noticia: Dict) -> None:
    """
    Guarda uma notícia completa no Neo4j.
    Se já existir com o mesmo id, substitui.
    """
    with get_driver().session(database="cec") as session:
        session.execute_write(_write_noticia, noticia)


def _write_noticia(tx, noticia: Dict) -> None:
    noticia_id = noticia["id"]

    # 1. Apaga CO_OCORRE_COM das frases desta notícia ANTES de apagar as frases
    tx.run("""
        MATCH (n:Noticia {id: $id})-[:TEM_FRASE]->(f:Frase)
        MATCH ()-[r:CO_OCORRE_COM {frase_id: f.id}]-()
        DELETE r
    """, id=noticia_id)

    # 2. Apaga frases e relações MENCIONADA_EM
    tx.run("""
        MATCH (n:Noticia {id: $id})
        OPTIONAL MATCH (n)-[:TEM_FRASE]->(f:Frase)
        DETACH DELETE f
    """, id=noticia_id)

    # 3. Cria/atualiza nó Noticia
    tx.run("""
        MERGE (n:Noticia {id: $id})
        SET n.titulo = $titulo
    """, id=noticia_id, titulo=noticia["titulo"])

    for frase in noticia["frases"]:
        # Cria nó Frase
        tx.run("""
            CREATE (f:Frase {id: $id, texto: $texto, ordem: $ordem, noticia_id: $noticia_id})
            WITH f
            MATCH (n:Noticia {id: $noticia_id})
            CREATE (n)-[:TEM_FRASE]->(f)
        """, id=frase["id"], texto=frase["texto"],
             ordem=frase["ordem"], noticia_id=noticia["id"])

        # Cria entidades e liga à frase
        for ent in frase["entidades"]:
            tx.run("""
                MERGE (e:Entidade {nome: $nome, tipo: $tipo})
                WITH e
                MATCH (f:Frase {id: $frase_id})
                CREATE (e)-[:MENCIONADA_EM {inicio: $inicio, fim: $fim}]->(f)
            """, nome=ent["nome"], tipo=ent["tipo"],
                 frase_id=frase["id"], inicio=ent["inicio"], fim=ent["fim"])

        # Cria co-ocorrências dentro da frase
        pares = build_cooccurrences(frase["entidades"])
        for e1, e2 in pares:
            tx.run("""
                MATCH (a:Entidade {nome: $nome1, tipo: $tipo1})
                MATCH (b:Entidade {nome: $nome2, tipo: $tipo2})
                MERGE (a)-[:CO_OCORRE_COM {frase_id: $frase_id}]->(b)
            """, nome1=e1["nome"], tipo1=e1["tipo"],
                 nome2=e2["nome"], tipo2=e2["tipo"],
                 frase_id=frase["id"])


# --- Labels ---

def get_all_labels() -> List[Dict]:
    """Devolve todas as labels com as suas cores."""
    with get_driver().session(database="cec") as session:
        result = session.run("MATCH (l:Label) RETURN l.nome AS nome, l.cor AS cor")
        return [{"nome": r["nome"], "cor": r["cor"]} for r in result]


def init_labels() -> None:
    """
    Inicializa as labels com cores padrão se ainda não existirem.
    Chamado no arranque da aplicação.
    """
    defaults = [
        ("PESSOA",      "#4A90D9"),
        ("LOCAL",       "#27AE60"),
        ("ORGANIZACAO", "#E67E22"),
        ("CRIME",       "#E74C3C"),
        ("DATA",        "#9B59B6"),
        ("VIATURA",     "#1ABC9C"),
        ("MATRICULA",   "#F39C12"),
        ("TELEMOVEL",   "#2ECC71"),
        ("EMAIL",       "#3498DB"),
        ("CRIPTO",      "#E91E63"),
        ("MONTANTE",    "#FF9800"),
    ]
    with get_driver().session(database="cec") as session:
        for nome, cor in defaults:
            session.run("""
                MERGE (l:Label {nome: $nome})
                ON CREATE SET l.cor = $cor
            """, nome=nome, cor=cor)


# --- Grafo de frase ---

def get_grafo_frase(frase_id: str) -> Dict:
    """
    Devolve nós e arestas de uma frase para renderizar no frontend.
    """
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (a:Entidade)-[r:CO_OCORRE_COM {frase_id: $frase_id}]->(b:Entidade)
            RETURN a.nome AS nome1, a.tipo AS tipo1,
                   b.nome AS nome2, b.tipo AS tipo2
        """, frase_id=frase_id)

        nos_vistos = {}
        arestas = []

        for row in result:
            for nome, tipo in [(row["nome1"], row["tipo1"]), (row["nome2"], row["tipo2"])]:
                if nome not in nos_vistos:
                    nos_vistos[nome] = {"id": nome, "nome": nome, "tipo": tipo}

            arestas.append({
                "origem": row["nome1"],
                "destino": row["nome2"],
                "relacao": "CO_OCORRE_COM"
            })

        return {"nos": list(nos_vistos.values()), "arestas": arestas}

def get_grafo_relacionadas(frase_id: str, nomes_visiveis: list) -> Dict:
    """
    Dado o id de uma frase e os nomes dos nós visíveis,
    procura entidades noutras frases/notícias que co-ocorram
    com essas entidades. Separa em totais e parciais.
    """
    with get_driver().session(database="cec") as session:

        # Busca co-ocorrências noutras frases que não esta
        result = session.run("""
            UNWIND $nomes AS nome
            MATCH (origem:Entidade {nome: nome})-[r:CO_OCORRE_COM]->(nova:Entidade)
            MATCH (nova)-[:MENCIONADA_EM]->(f:Frase)-[:TEM_FRASE]-(n:Noticia)
            WHERE r.frase_id <> $frase_id
            AND NOT nova.nome IN $nomes
            RETURN nova.nome AS nome,
                   nova.tipo AS tipo,
                   collect(DISTINCT origem.nome) AS ligada_a,
                   n.id AS noticia_id,
                   n.titulo AS noticia_titulo,
                   r.frase_id AS frase_origem
        """, nomes=nomes_visiveis, frase_id=frase_id)

        nos_origem = {
            nome: {"id": nome, "nome": nome, "tipo": None, "origem": True}
            for nome in nomes_visiveis
        }

        # Busca tipos das entidades origem
        tipos_result = session.run("""
            UNWIND $nomes AS nome
            MATCH (e:Entidade {nome: nome})
            RETURN e.nome AS nome, e.tipo AS tipo
        """, nomes=nomes_visiveis)
        for row in tipos_result:
            if row["nome"] in nos_origem:
                nos_origem[row["nome"]]["tipo"] = row["tipo"]

        nos_novos = {}
        arestas = []

        for row in result:
            nome_novo = row["nome"]
            ligada_a = row["ligada_a"]

            # Classifica como total ou parcial
            eh_total = all(n in ligada_a for n in nomes_visiveis)
            tipo_ligacao = "total" if eh_total else "parcial"

            # Adiciona nó novo se ainda não existe
            chave = f"{nome_novo}_{row['noticia_id']}"
            if chave not in nos_novos:
                nos_novos[chave] = {
                    "id": chave,
                    "nome": nome_novo,
                    "tipo": row["tipo"],
                    "noticia_id": row["noticia_id"],
                    "noticia_titulo": row["noticia_titulo"],
                    "origem": False,
                }

            # Cria arestas para cada entidade origem a que está ligada
            for origem_nome in ligada_a:
                if origem_nome in nomes_visiveis:
                    arestas.append({
                        "origem": origem_nome,
                        "destino": chave,
                        "relacao": tipo_ligacao,
                    })

        # Remove arestas duplicadas
        arestas_unicas = list({
            f"{a['origem']}_{a['destino']}": a for a in arestas
        }.values())

        todos_nos = list(nos_origem.values()) + list(nos_novos.values())

        return {
            "nos": todos_nos,
            "arestas": arestas_unicas,
            "tem_resultados": len(nos_novos) > 0,
        }