import os
import sys
from typing import List, Dict

from services.regex_entities import extract_regex_entities
from ner_model.ner_manager import ner_manager
REGEX_PRIORITY_TYPES = {"EMAIL", "TELEMOVEL", "MATRICULA", "CRIPTO"}


def run_ner(texto: str) -> List[Dict]:
    """
    Corre o modelo NER via NERManager e complementa com regex.
    """
    raw = ner_manager.predict_entities(texto)

    # GLiNER devolve offsets de caracteres diretamente
    # XLM-RoBERTa devolve start_word/end_word
    if raw and "start_word" in raw[0]:
        entidades_modelo = _convert_offsets_words(texto, raw)
    else:
        entidades_modelo = raw  # GLiNER já tem o formato correto

    entidades_regex = extract_regex_entities(texto)
    return _merge_entities(entidades_modelo, entidades_regex)


def _convert_offsets_words(texto: str, entidades_raw: List[Dict]) -> List[Dict]:
    """Converte offsets de palavras para offsets de caracteres (xlm-roberta)."""
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
def _reagregar(entidades: List[Dict], desloc: int) -> List[Dict]:
    """Passa offsets locais da frase para offsets do texto completo."""
    for e in entidades:
        e["inicio"] += desloc
        e["fim"] += desloc
    return entidades


def run_ner_ambos_por_frases(frases: List[Dict]) -> dict:
    """
    Corre os dois modelos frase a frase e reagrega os offsets ao texto completo.
    Resolve a truncagem (B3): cada frase cabe folgadamente nos limites dos modelos.
    Nota: os modelos são carregados uma vez por pedido. Reutilizá-los entre
    pedidos (B1) fica para a consolidação do NERManager.
    """
    modelo_xlm = ner_manager.get_xlm()
    modelo_gliner = ner_manager.get_gliner()

    ents_xlm, ents_gliner, ents_regex = [], [], []
    for frase in frases:
        texto = frase["texto"]
        desloc = frase["inicio"]

        raw_xlm = modelo_xlm.predict_entities(texto)
        f_xlm = _convert_offsets_words(texto, raw_xlm) if (raw_xlm and "start_word" in raw_xlm[0]) else raw_xlm
        ents_xlm.extend(_reagregar(f_xlm, desloc))
        ents_gliner.extend(_reagregar(modelo_gliner.predict_entities(texto), desloc))
        ents_regex.extend(_reagregar(extract_regex_entities(texto), desloc))

    return {
        "xlm": _merge_entities(ents_xlm, ents_regex),
        "gliner": _merge_entities(ents_gliner, ents_regex),
    }

def run_ner_por_frases(frases: List[Dict]) -> List[Dict]:
    """Corre o modelo ativo frase a frase e reagrega offsets ao texto completo."""
    entidades = []
    for frase in frases:
        ents = run_ner(frase["texto"])
        entidades.extend(_reagregar(ents, frase["inicio"]))
    return entidades

def run_ner_ambos(texto: str) -> dict:
    """
    Corre os dois modelos em paralelo e devolve entidades de cada um.
    """
    import concurrent.futures
    from ner_model.xlm_roberta_model import NERModel
    from ner_model.gliner_model import GLiNERModel

    def run_xlm():
        modelo = NERModel()
        raw = modelo.predict_entities(texto)
        if raw and "start_word" in raw[0]:
            return _convert_offsets_words(texto, raw)
        return raw

    def run_gliner():
        modelo = GLiNERModel()
        return modelo.predict_entities(texto)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_xlm = executor.submit(run_xlm)
        future_gliner = executor.submit(run_gliner)
        entidades_xlm = future_xlm.result()
        entidades_gliner = future_gliner.result()

    entidades_regex = extract_regex_entities(texto)
    return {
        "xlm": _merge_entities(entidades_xlm, entidades_regex),
        "gliner": _merge_entities(entidades_gliner, entidades_regex),
    }