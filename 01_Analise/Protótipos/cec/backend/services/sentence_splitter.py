import re
import uuid
from typing import List, Dict


# Delimitadores de frase
SENTENCE_DELIMITERS = re.compile(r'(?<=[.!?])\s+')


def split_sentences(texto: str, noticia_id: str) -> List[Dict]:
    """
    Divide um texto em frases usando . ! ? como delimitadores.

    Devolve lista de dicionários com:
      - id:         identificador único da frase
      - texto:      conteúdo da frase
      - ordem:      posição da frase no texto (0-indexed)
      - noticia_id: id da notícia a que pertence
      - inicio:     offset de início no texto original
      - fim:        offset de fim no texto original
    """
    partes = SENTENCE_DELIMITERS.split(texto.strip())
    frases = []
    offset = 0

    for ordem, parte in enumerate(partes):
        parte = parte.strip()
        if not parte:
            continue

        inicio = texto.find(parte, offset)
        fim = inicio + len(parte)

        frases.append({
            "id": str(uuid.uuid4()),
            "texto": parte,
            "ordem": ordem,
            "noticia_id": noticia_id,
            "inicio": inicio,
            "fim": fim,
        })

        offset = fim

    return frases