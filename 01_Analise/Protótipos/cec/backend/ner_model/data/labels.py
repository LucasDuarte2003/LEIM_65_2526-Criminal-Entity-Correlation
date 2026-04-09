# Definição central de todas as labels do sistema NER.

LABEL_LIST = [
    "O",
    "B-PESSOA",       "I-PESSOA",
    "B-VIATURA",      "I-VIATURA",
    "B-MATRICULA",    "I-MATRICULA",
    "B-TELEMOVEL",    "I-TELEMOVEL",
    "B-EMAIL",        "I-EMAIL",
    "B-CRIPTO",       "I-CRIPTO",
    "B-CRIME",        "I-CRIME",
    "B-LOCAL",        "I-LOCAL",
    "B-DATA",         "I-DATA",
    "B-ORGANIZACAO",  "I-ORGANIZACAO",
    "B-MONTANTE",     "I-MONTANTE",
]

LABEL2ID = {label: idx for idx, label in enumerate(LABEL_LIST)}
ID2LABEL = {idx: label for label, idx in LABEL2ID.items()}