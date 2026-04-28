import os
import sys
from typing import List, Dict

from services.regex_entities import extract_regex_entities

REGEX_PRIORITY_TYPES = {"EMAIL", "TELEMOVEL", "MATRICULA", "CRIPTO"}


def run_ner(texto: str) -> List[Dict]:
    """
    Corre o modelo NER via NERManager e complementa com regex.
    """
    from ner_model.ner_manager import ner_manager

    raw = ner_manager.predict_entities(texto)
    entidades_modelo = _convert_offsets(texto, raw)
    entidades_regex = extract_regex_entities(texto)

    return _merge_entities(entidades_modelo, entidades_regex)


def _convert_offsets(texto: str, entidades_raw: List[Dict]) -> List[Dict]:
    palavras = texto.split()

    word_starts = []
    pos = 0
    for palavra in palavras:
        pos = texto.find(palavra, pos)
        word_starts.append(pos)
        pos += len(palavra)

    resultado = []
    for ent in entidades_raw:
        sw = ent["start_word"]
        ew = ent["end_word"]
        inicio = word_starts[sw]
        fim = word_starts[ew] + len(palavras[ew])
        resultado.append({
            "nome": ent["text"],
            "tipo": ent["label"],
            "inicio": inicio,
            "fim": fim,
        })

    return resultado


def _overlap(e1: Dict, e2: Dict) -> bool:
    return e1["inicio"] < e2["fim"] and e2["inicio"] < e1["fim"]


def _same_span(e1: Dict, e2: Dict) -> bool:
    return e1["inicio"] == e2["inicio"] and e1["fim"] == e2["fim"]


def _merge_entities(entidades_modelo: List[Dict], entidades_regex: List[Dict]) -> List[Dict]:
    resultado = []

    for ent_regex in entidades_regex:
        resultado.append(ent_regex)

    for ent_modelo in entidades_modelo:
        conflito = False
        for ent_final in resultado:
            if _same_span(ent_modelo, ent_final):
                conflito = True
                break
            if ent_final["tipo"] in REGEX_PRIORITY_TYPES and _overlap(ent_modelo, ent_final):
                conflito = True
                break
        if not conflito:
            resultado.append(ent_modelo)

    resultado.sort(key=lambda e: (e["inicio"], e["fim"]))
    return resultado