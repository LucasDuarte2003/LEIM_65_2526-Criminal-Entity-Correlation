import os
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from services.graph_builder import build_cooccurrences
from ner_model.data.labels import LABEL2ID

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
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (n:Noticia)
            RETURN n.id AS id,
                   COALESCE(n.titulo, left(n.texto, 60)) AS titulo
        """)
        return [{"id": r["id"], "titulo": r["titulo"] or r["id"]} for r in result]


def get_noticias_por_pasta(pasta_id: str) -> List[Dict]:
    """Devolve lista de notícias de uma pasta específica."""
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (p:Pasta {id: $pasta_id})-[:CONTEM_NOTICIA]->(n:Noticia)
            RETURN n.id AS id, n.titulo AS titulo
        """, pasta_id=pasta_id)
        return [{"id": r["id"], "titulo": r["titulo"]} for r in result]


def get_noticia(noticia_id: str) -> Optional[Dict]:
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
    with get_driver().session(database="cec") as session:
        session.execute_write(_write_noticia, noticia)


def _write_noticia(tx, noticia: Dict) -> None:
    noticia_id = noticia["id"]

    tx.run("""
        MATCH (n:Noticia {id: $id})-[:TEM_FRASE]->(f:Frase)
        MATCH ()-[r:CO_OCORRE_COM {frase_id: f.id}]-()
        DELETE r
    """, id=noticia_id)

    tx.run("""
        MATCH (n:Noticia {id: $id})
        OPTIONAL MATCH (n)-[:TEM_FRASE]->(f:Frase)
        DETACH DELETE f
    """, id=noticia_id)

    tx.run("""
        MERGE (n:Noticia {id: $id})
        SET n.titulo = $titulo
    """, id=noticia_id, titulo=noticia["titulo"])

    for frase in noticia["frases"]:
        tx.run("""
            CREATE (f:Frase {id: $id, texto: $texto, ordem: $ordem, noticia_id: $noticia_id})
            WITH f
            MATCH (n:Noticia {id: $noticia_id})
            CREATE (n)-[:TEM_FRASE]->(f)
        """, id=frase["id"], texto=frase["texto"],
             ordem=frase["ordem"], noticia_id=noticia["id"])

        for ent in frase["entidades"]:
            tx.run("""
                MERGE (e:Entidade {nome: $nome, tipo: $tipo})
                WITH e
                MATCH (f:Frase {id: $frase_id})
                CREATE (e)-[:MENCIONADA_EM {inicio: $inicio, fim: $fim}]->(f)
            """, nome=ent["nome"], tipo=ent["tipo"],
                 frase_id=frase["id"], inicio=ent["inicio"], fim=ent["fim"])

        pares = build_cooccurrences(frase["entidades"])
        for e1, e2 in pares:
            tx.run("""
                MATCH (a:Entidade {nome: $nome1, tipo: $tipo1})
                MATCH (b:Entidade {nome: $nome2, tipo: $tipo2})
                MERGE (a)-[:CO_OCORRE_COM {frase_id: $frase_id}]->(b)
            """, nome1=e1["nome"], tipo1=e1["tipo"],
                 nome2=e2["nome"], tipo2=e2["tipo"],
                 frase_id=frase["id"])


def delete_noticia(noticia_id: str) -> bool:
    with get_driver().session(database="cec") as session:
        session.execute_write(_delete_noticia_tx, noticia_id)
    return True


def _delete_noticia_tx(tx, noticia_id: str) -> None:
    tx.run("""
        MATCH (n:Noticia {id: $id})-[:TEM_FRASE]->(f:Frase)
        MATCH ()-[r:CO_OCORRE_COM {frase_id: f.id}]-()
        DELETE r
    """, id=noticia_id)
    tx.run("""
        MATCH (n:Noticia {id: $id})
        OPTIONAL MATCH (n)-[:TEM_FRASE]->(f:Frase)
        DETACH DELETE f
    """, id=noticia_id)
    tx.run("""
        MATCH (n:Noticia {id: $id})
        DETACH DELETE n
    """, id=noticia_id)


def ligar_noticia_a_pasta(noticia_id: str, pasta_id: str) -> None:
    with get_driver().session(database="cec") as session:
        session.run("""
            MATCH (p:Pasta {id: $pasta_id}), (n:Noticia {id: $noticia_id})
            MERGE (p)-[:CONTEM_NOTICIA]->(n)
        """, pasta_id=pasta_id, noticia_id=noticia_id)


def mover_noticia(noticia_id: str, pasta_id_destino: str) -> bool:
    with get_driver().session(database="cec") as session:
        session.run("""
            MATCH (p:Pasta)-[r:CONTEM_NOTICIA]->(n:Noticia {id: $noticia_id})
            DELETE r
        """, noticia_id=noticia_id)
        result = session.run("""
            MATCH (p:Pasta {id: $pasta_id}), (n:Noticia {id: $noticia_id})
            CREATE (p)-[:CONTEM_NOTICIA]->(n)
            RETURN n.id AS id
        """, pasta_id=pasta_id_destino, noticia_id=noticia_id)
        return result.single() is not None


# --- Projetos ---

def get_all_projetos() -> List[Dict]:
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (proj:Projeto)
            OPTIONAL MATCH (proj)-[:TEM_PASTA]->(p:Pasta)
            OPTIONAL MATCH (p)-[:CONTEM_NOTICIA]->(n:Noticia)
            RETURN proj.id AS id,
                   proj.nome AS nome,
                   proj.descricao AS descricao,
                   count(DISTINCT p) AS total_pastas,
                   count(DISTINCT n) AS total_noticias
        """)
        return [
            {
                "id": r["id"],
                "nome": r["nome"],
                "descricao": r["descricao"],
                "total_pastas": r["total_pastas"],
                "total_noticias": r["total_noticias"],
            }
            for r in result
        ]


def get_projeto(projeto_id: str) -> Optional[Dict]:
    with get_driver().session(database="cec") as session:
        proj_result = session.run("""
            MATCH (proj:Projeto {id: $id})
            RETURN proj.id AS id, proj.nome AS nome, proj.descricao AS descricao
        """, id=projeto_id)
        row = proj_result.single()
        if not row:
            return None

        pastas_result = session.run("""
            MATCH (proj:Projeto {id: $id})-[:TEM_PASTA]->(p:Pasta)
            OPTIONAL MATCH (p)-[:CONTEM_NOTICIA]->(n:Noticia)
            RETURN p.id AS id, p.nome AS nome, p.projeto_id AS projeto_id,
                   count(n) AS total_noticias
        """, id=projeto_id)

        return {
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "pastas": [
                {
                    "id": p["id"],
                    "nome": p["nome"],
                    "projeto_id": p["projeto_id"],
                    "total_noticias": p["total_noticias"],
                }
                for p in pastas_result
            ],
        }


def create_projeto(projeto_id: str, nome: str, descricao: Optional[str]) -> Dict:
    with get_driver().session(database="cec") as session:
        session.run("""
            CREATE (proj:Projeto {id: $id, nome: $nome, descricao: $descricao})
        """, id=projeto_id, nome=nome, descricao=descricao)
    return {"id": projeto_id, "nome": nome, "descricao": descricao, "pastas": []}


def update_projeto(projeto_id: str, nome: Optional[str], descricao: Optional[str]) -> Optional[Dict]:
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (proj:Projeto {id: $id})
            SET proj.nome      = COALESCE($nome, proj.nome),
                proj.descricao = COALESCE($descricao, proj.descricao)
            RETURN proj.id AS id
        """, id=projeto_id, nome=nome, descricao=descricao)
        if not result.single():
            return None
    return get_projeto(projeto_id)


def delete_projeto(projeto_id: str) -> bool:
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (proj:Projeto {id: $id})
            OPTIONAL MATCH (proj)-[:TEM_PASTA]->(p:Pasta)
            DETACH DELETE p, proj
            RETURN count(proj) AS apagados
        """, id=projeto_id)
        row = result.single()
        return row and row["apagados"] > 0


# --- Pastas ---

def get_pasta(pasta_id: str) -> Optional[Dict]:
    with get_driver().session(database="cec") as session:
        pasta_result = session.run("""
            MATCH (p:Pasta {id: $id})
            RETURN p.id AS id, p.nome AS nome, p.projeto_id AS projeto_id
        """, id=pasta_id)
        row = pasta_result.single()
        if not row:
            return None

        noticias_result = session.run("""
            MATCH (p:Pasta {id: $id})-[:CONTEM_NOTICIA]->(n:Noticia)
            RETURN n.id AS id, n.titulo AS titulo
        """, id=pasta_id)

        return {
            "id": row["id"],
            "nome": row["nome"],
            "projeto_id": row["projeto_id"],
            "noticias": [{"id": n["id"], "titulo": n["titulo"]} for n in noticias_result],
        }


def create_pasta(pasta_id: str, nome: str, projeto_id: str) -> Dict:
    with get_driver().session(database="cec") as session:
        session.run("""
            MATCH (proj:Projeto {id: $projeto_id})
            CREATE (p:Pasta {id: $id, nome: $nome, projeto_id: $projeto_id})
            CREATE (proj)-[:TEM_PASTA]->(p)
        """, id=pasta_id, nome=nome, projeto_id=projeto_id)
    return {"id": pasta_id, "nome": nome, "projeto_id": projeto_id, "noticias": []}


def update_pasta(pasta_id: str, nome: str) -> Optional[Dict]:
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (p:Pasta {id: $id})
            SET p.nome = $nome
            RETURN p.id AS id
        """, id=pasta_id, nome=nome)
        if not result.single():
            return None
    return get_pasta(pasta_id)


def delete_pasta(pasta_id: str) -> bool:
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (p:Pasta {id: $id})
            DETACH DELETE p
            RETURN count(p) AS apagados
        """, id=pasta_id)
        row = result.single()
        return row and row["apagados"] > 0


# --- Labels ---

def get_all_labels() -> List[Dict]:
    with get_driver().session(database="cec") as session:
        result = session.run("MATCH (l:Label) RETURN l.nome AS nome, l.cor AS cor")
        return [{"nome": r["nome"], "cor": r["cor"]} for r in result]


def init_labels() -> None:
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


def get_grafo_relacionadas(frase_id: str, nomes_visiveis: list, ambito: str = "global") -> Dict:
    with get_driver().session(database="cec") as session:

        # Determina o filtro de âmbito
        if ambito == "documento":
            filtro = """
                MATCH (f_origem:Frase {id: $frase_id})<-[:TEM_FRASE]-(n_origem:Noticia)
                WITH n_origem
                MATCH (n_origem)-[:TEM_FRASE]->(f_alvo:Frase)
            """
            where_extra = "AND r.frase_id <> $frase_id AND f_alvo.id = r.frase_id"
        elif ambito == "pasta":
            filtro = """
                MATCH (f_origem:Frase {id: $frase_id})<-[:TEM_FRASE]-(:Noticia)
                      <-[:CONTEM_NOTICIA]-(pasta:Pasta)
                WITH pasta
                MATCH (pasta)-[:CONTEM_NOTICIA]->(:Noticia)-[:TEM_FRASE]->(f_alvo:Frase)
            """
            where_extra = "AND r.frase_id <> $frase_id AND f_alvo.id = r.frase_id"
        elif ambito == "projeto":
            filtro = """
                MATCH (f_origem:Frase {id: $frase_id})<-[:TEM_FRASE]-(:Noticia)
                      <-[:CONTEM_NOTICIA]-(:Pasta)<-[:TEM_PASTA]-(proj:Projeto)
                WITH proj
                MATCH (proj)-[:TEM_PASTA]->(:Pasta)-[:CONTEM_NOTICIA]->(:Noticia)-[:TEM_FRASE]->(f_alvo:Frase)
            """
            where_extra = "AND r.frase_id <> $frase_id AND f_alvo.id = r.frase_id"
        else:  # global
            filtro = ""
            where_extra = "AND r.frase_id <> $frase_id"

        if ambito in ("documento", "pasta", "projeto"):
            query = f"""
                {filtro}
                WITH collect(f_alvo.id) AS frases_ambito
                UNWIND $nomes AS nome
                MATCH (origem:Entidade {{nome: nome}})-[r:CO_OCORRE_COM]->(nova:Entidade)
                MATCH (nova)-[:MENCIONADA_EM]->(f:Frase)-[:TEM_FRASE]-(n:Noticia)
                WHERE r.frase_id IN frases_ambito
                AND r.frase_id <> $frase_id
                AND NOT nova.nome IN $nomes
                RETURN nova.nome AS nome,
                       nova.tipo AS tipo,
                       collect(DISTINCT origem.nome) AS ligada_a,
                       n.id AS noticia_id,
                       n.titulo AS noticia_titulo,
                       r.frase_id AS frase_origem
            """
        else:
            query = """
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
            """

        result = session.run(query, nomes=nomes_visiveis, frase_id=frase_id)

        nos_origem = {
            nome: {"id": nome, "nome": nome, "tipo": None, "origem": True}
            for nome in nomes_visiveis
        }
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
            eh_total = all(n in ligada_a for n in nomes_visiveis)
            tipo_ligacao = "total" if eh_total else "parcial"
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
            for origem_nome in ligada_a:
                if origem_nome in nomes_visiveis:
                    arestas.append({
                        "origem": origem_nome,
                        "destino": chave,
                        "relacao": tipo_ligacao,
                    })

        arestas_unicas = list({
            f"{a['origem']}_{a['destino']}": a for a in arestas
        }.values())
        todos_nos = list(nos_origem.values()) + list(nos_novos.values())
        return {
            "nos": todos_nos,
            "arestas": arestas_unicas,
            "tem_resultados": len(nos_novos) > 0,
        }

def get_all_pastas() -> List[Dict]:
    """Devolve todas as pastas de todos os projetos."""
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (proj:Projeto)-[:TEM_PASTA]->(p:Pasta)
            RETURN p.id AS id, p.nome AS nome,
                   proj.id AS projeto_id, proj.nome AS projeto_nome
            ORDER BY proj.nome, p.nome
        """)
        return [
            {
                "id": r["id"],
                "nome": r["nome"],
                "projeto_id": r["projeto_id"],
                "projeto_nome": r["projeto_nome"],
            }
            for r in result
        ]

def get_grafo_frases_fundidas(frase_ids: list) -> Dict:
    """Devolve o grafo combinado de duas frases."""
    with get_driver().session(database="cec") as session:
        result = session.run("""
            UNWIND $frase_ids AS frase_id
            MATCH (a:Entidade)-[r:CO_OCORRE_COM {frase_id: frase_id}]->(b:Entidade)
            RETURN a.nome AS nome1, a.tipo AS tipo1,
                   b.nome AS nome2, b.tipo AS tipo2,
                   frase_id
        """, frase_ids=frase_ids)

        nos_vistos = {}
        arestas = []
        for row in result:
            for nome, tipo in [(row["nome1"], row["tipo1"]), (row["nome2"], row["tipo2"])]:
                if nome not in nos_vistos:
                    nos_vistos[nome] = {"id": nome, "nome": nome, "tipo": tipo}
            arestas.append({
                "origem": row["nome1"],
                "destino": row["nome2"],
                "relacao": "CO_OCORRE_COM",
                "frase_id": row["frase_id"],
            })

        arestas_unicas = list({
            f"{a['origem']}_{a['destino']}": a for a in arestas
        }.values())

        return {"nos": list(nos_vistos.values()), "arestas": arestas_unicas}
def exportar_dados_treino() -> list:
    """
    Exporta todas as notícias anotadas do Neo4j em formato de treino.
    Devolve lista de {"tokens": [...], "labels": [...]} por frase.
    """
    with get_driver().session(database="cec") as session:
        result = session.run("""
            MATCH (n:Noticia)-[:TEM_FRASE]->(f:Frase)
            OPTIONAL MATCH (e:Entidade)-[r:MENCIONADA_EM]->(f)
            WITH f.id AS frase_id,
                 f.texto AS texto,
                 f.noticia_id AS noticia_id,
                 f.ordem AS ordem,
                 collect({
                     nome: e.nome,
                     tipo: e.tipo,
                     inicio: r.inicio,
                     fim: r.fim
                 }) AS entidades
            ORDER BY noticia_id, ordem
            RETURN frase_id, texto, entidades
        """)

        dados = []
        for row in result:
            texto = row["texto"]
            entidades = [e for e in row["entidades"] if e["nome"] is not None]
            tokens = texto.split()

            word_starts = []
            pos = 0
            for palavra in tokens:
                pos = texto.find(palavra, pos)
                word_starts.append(pos)
                pos += len(palavra)

            labels = ["O"] * len(tokens)
            for ent in entidades:
                tipo = ent["tipo"]
                inicio = ent["inicio"]
                fim = ent["fim"]
                primeiro = True
                for i, (word, start) in enumerate(zip(tokens, word_starts)):
                    end = start + len(word)
                    if start >= inicio and end <= fim:
                        labels[i] = f"{'B' if primeiro else 'I'}-{tipo}"
                        primeiro = False

            if any(l != "O" for l in labels):
                dados.append({"tokens": tokens, "labels": labels})

        return dados