import os
import sys
from typing import List, Dict

# Garante que o modelo é encontrado independentemente de onde o servidor é lançado
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ner_model")
sys.path.insert(0, MODEL_DIR)

from predict import predict_entities  # noqa: E402


def run_ner(texto: str) -> List[Dict]:
    """
    Corre o modelo NER num texto e devolve entidades
    com offsets de caracteres relativos ao documento.

    Devolve:
        [{"nome": str, "tipo": str, "inicio": int, "fim": int}, ...]
    """
    raw = predict_entities(texto)
    return _convert_offsets(texto, raw)


def _convert_offsets(texto: str, entidades_raw: List[Dict]) -> List[Dict]:
    """
    Converte start_word/end_word (índices de palavras)
    para inicio/fim (índices de caracteres no texto original).
    """
    palavras = texto.split()

    # Calcula o offset de início de cada palavra
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