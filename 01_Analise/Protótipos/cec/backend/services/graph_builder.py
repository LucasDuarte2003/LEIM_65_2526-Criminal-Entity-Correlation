from typing import List, Dict, Tuple


def build_cooccurrences(entidades: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """
    Recebe a lista de entidades de uma frase.
    Devolve pares únicos de entidades de tipos diferentes
    que co-ocorrem nessa frase.

    Exemplo de par:
      ({"nome": "João", "tipo": "PESSOA"}, {"nome": "Lisboa", "tipo": "LOCAL"})
    """
    pares = []
    vistos = set()

    for i, e1 in enumerate(entidades):
        for e2 in entidades[i + 1:]:

            # Só pares de tipos diferentes
            if e1["tipo"] == e2["tipo"]:
                continue

            chave = tuple(sorted([
                (e1["nome"], e1["tipo"]),
                (e2["nome"], e2["tipo"])
            ]))

            if chave in vistos:
                continue

            vistos.add(chave)
            pares.append((e1, e2))

    return pares


def assign_entities_to_sentences(frases: List[Dict], entidades_doc: List[Dict]) -> List[Dict]:
    """
    Dado o texto dividido em frases e as entidades do documento inteiro
    (com offsets relativos ao documento), distribui cada entidade
    pela frase onde está contida.

    Devolve as frases com o campo 'entidades' preenchido.
    """
    for frase in frases:
        frase["entidades"] = []

    for entidade in entidades_doc:
        for frase in frases:
            if entidade["inicio"] >= frase["inicio"] and entidade["fim"] <= frase["fim"]:
                # Converte offsets para serem relativos à frase
                entidade_local = {
                    "nome": entidade["nome"],
                    "tipo": entidade["tipo"],
                    "inicio": entidade["inicio"] - frase["inicio"],
                    "fim": entidade["fim"] - frase["inicio"],
                }
                frase["entidades"].append(entidade_local)
                break

    return frases