import re
import uuid
from typing import List, Dict

# Delimitadores reais de frase:
# ponto, exclamação ou interrogação seguidos de espaço
SENTENCE_DELIMITERS = re.compile(r'(?<=[.!?])\s+')

# Placeholder temporário para proteger pontos que não são fim de frase
DOT_PLACEHOLDER = "§DOT§"


def protect_non_sentence_dots(texto: str) -> str:
    """
    Protege pontos que não devem ser interpretados como fim de frase.

    Casos tratados:
    - abreviaturas comuns: Dr., Sr., Sra., etc.
    - abreviaturas empresariais: Inc., Ltd., Corp., Co., Lda., etc.
    - iniciais isoladas de nomes próprios: P., M., J.
    - siglas com pontos: S.A., U.S., U.S.A.
    """

    # 1) Abreviaturas comuns e empresariais
    abreviaturas = [
        "St.", "Dr.", "Dra.", "Sr.", "Sra.", "Srta.",
        "Prof.", "Profa.", "Ex.", "Exmo.", "etc.",
        "Inc.", "Ltd.", "Corp.", "Co.", "Lda.", "Unip.", "Jr.", "Sr.",
        "Mt."
    ]

    for abrev in abreviaturas:
        texto = texto.replace(abrev, abrev.replace(".", DOT_PLACEHOLDER))

    # 2) Siglas com pontos tipo S.A., U.S., U.S.A., P.J.
    texto = re.sub(
        r'\b(?:[A-Z]\.){2,}',
        lambda m: m.group(0).replace(".", DOT_PLACEHOLDER),
        texto
    )

    # 3) Iniciais isoladas de nomes próprios: "J. Gaston", "M. King", "P. Carlin"
    texto = re.sub(
        r'\b([A-Z])\.(?=\s+[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛ])',
        rf'\1{DOT_PLACEHOLDER}',
        texto
    )

    return texto


def restore_protected_dots(texto: str) -> str:
    """
    Restaura os pontos protegidos anteriormente.
    """
    return texto.replace(DOT_PLACEHOLDER, ".")


def split_sentences(texto: str, noticia_id: str) -> List[Dict]:
    """
    Divide um texto em frases usando . ! ? como delimitadores,
    mas evitando partir abreviaturas, siglas e iniciais.

    Devolve lista de dicionários com:
      - id: identificador único da frase
      - texto: conteúdo da frase
      - ordem: posição da frase no texto
      - noticia_id: id da notícia
      - inicio: offset inicial no texto original
      - fim: offset final no texto original
    """
    texto_protegido = protect_non_sentence_dots(texto)
    partes_protegidas = SENTENCE_DELIMITERS.split(texto_protegido.strip())

    frases = []
    offset = 0

    for ordem, parte_protegida in enumerate(partes_protegidas):
        parte_protegida = parte_protegida.strip()
        if not parte_protegida:
            continue

        parte_original = restore_protected_dots(parte_protegida)

        inicio = texto.find(parte_original, offset)
        if inicio == -1:
            continue

        fim = inicio + len(parte_original)

        frases.append({
            "id": str(uuid.uuid4()),
            "texto": parte_original,
            "ordem": ordem,
            "noticia_id": noticia_id,
            "inicio": inicio,
            "fim": fim,
        })

        offset = fim

    return frases