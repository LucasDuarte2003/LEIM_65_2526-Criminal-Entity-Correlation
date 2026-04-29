import re
from typing import List, Dict

# Email
EMAIL_REGEX = re.compile(
    r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
)

# Telemóvel português
# formatos aceites:
# 912345678
# 912 345 678
# +351 912 345 678
# +351912345678
TELEMOVEL_REGEX = re.compile(
    r'(?<!\d)(?:\+351\s?)?(?:9[1236]\d(?:\s?\d{3}){2})(?!\d)'
)

# Matrícula portuguesa
# formatos comuns:
# 12-AB-34
# AB-12-CD
# 12-34-AB
MATRICULA_REGEX = re.compile(
    r'\b(?:\d{2}-[A-Z]{2}-\d{2}|[A-Z]{2}-\d{2}-[A-Z]{2}|\d{2}-\d{2}-[A-Z]{2})\b'
)

# Nomes e símbolos de criptomoedas
CRIPTO_NOME_REGEX = re.compile(
    r'\b(?:BTC|Bitcoin|ETH|Ethereum|USDT|Tether|XMR|Monero|BNB|Binance Coin|SOL|Solana|ADA|Cardano|DOGE|Dogecoin|XRP|LTC|Litecoin)\b',
    re.IGNORECASE
)

# Endereços Bitcoin modernos (bech32) — começam por bc1
CRIPTO_BTC_ADDRESS_REGEX = re.compile(
    r'\bbc1[a-z0-9]{20,90}\b',
    re.IGNORECASE
)

# Endereços Ethereum — começam por 0x e têm 40 hex chars
CRIPTO_ETH_ADDRESS_REGEX = re.compile(
    r'\b0x[a-fA-F0-9]{40}\b'
)


def _build_entity(match: re.Match, label: str) -> Dict:
    return {
        "nome": match.group(0),
        "tipo": label,
        "inicio": match.start(),
        "fim": match.end(),
    }


def extract_regex_entities(texto: str) -> List[Dict]:
    entidades = []

    for match in EMAIL_REGEX.finditer(texto):
        entidades.append(_build_entity(match, "EMAIL"))

    for match in TELEMOVEL_REGEX.finditer(texto):
        entidades.append(_build_entity(match, "TELEMOVEL"))

    for match in MATRICULA_REGEX.finditer(texto):
        entidades.append(_build_entity(match, "MATRICULA"))

    for match in CRIPTO_NOME_REGEX.finditer(texto):
        entidades.append(_build_entity(match, "CRIPTO"))

    for match in CRIPTO_BTC_ADDRESS_REGEX.finditer(texto):
        entidades.append(_build_entity(match, "CRIPTO"))

    for match in CRIPTO_ETH_ADDRESS_REGEX.finditer(texto):
        entidades.append(_build_entity(match, "CRIPTO"))

    return entidades