LABEL_LIST = [
    "O",
    "B-PESSOA", "I-PESSOA",
    "B-ORGANIZACAO", "I-ORGANIZACAO",
    "B-LOCAL", "I-LOCAL",
    "B-CRIME", "I-CRIME",
    "B-DATA", "I-DATA",
]

LABEL2ID = {label: idx for idx, label in enumerate(LABEL_LIST)}
ID2LABEL = {idx: label for label, idx in LABEL2ID.items()}


RAW_TRAIN_DATA = [
    # --- PESSOA + ORGANIZACAO + LOCAL ---
    [
        ("João", "B-PESSOA"), ("Silva", "I-PESSOA"), ("foi", "O"),
        ("detido", "O"), ("em", "O"), ("Lisboa", "B-LOCAL"),
        ("pela", "O"), ("PSP", "B-ORGANIZACAO"), (".", "O")
    ],
    [
        ("A", "O"), ("GNR", "B-ORGANIZACAO"), ("identificou", "O"),
        ("Maria", "B-PESSOA"), ("Santos", "I-PESSOA"), ("como", "O"),
        ("suspeita", "O"), ("de", "O"), ("tráfico", "B-CRIME"),
        ("de", "I-CRIME"), ("droga", "I-CRIME"), (".", "O")
    ],
    [
        ("Carlos", "B-PESSOA"), ("Mendes", "I-PESSOA"), ("e", "O"),
        ("António", "B-PESSOA"), ("Ferreira", "I-PESSOA"), ("foram", "O"),
        ("acusados", "O"), ("de", "O"), ("furto", "B-CRIME"),
        ("no", "O"), ("Porto", "B-LOCAL"), (".", "O")
    ],
    [
        ("O", "O"), ("Ministério", "B-ORGANIZACAO"), ("Público", "I-ORGANIZACAO"),
        ("abriu", "O"), ("inquérito", "O"), ("por", "O"),
        ("homicídio", "B-CRIME"), ("em", "O"), ("Braga", "B-LOCAL"), (".", "O")
    ],
    [
        ("Pedro", "B-PESSOA"), ("Alves", "I-PESSOA"), ("foi", "O"),
        ("condenado", "O"), ("por", "O"), ("burla", "B-CRIME"),
        ("em", "O"), ("Faro", "B-LOCAL"), ("em", "O"),
        ("janeiro", "B-DATA"), ("de", "I-DATA"), ("2023", "I-DATA"), (".", "O")
    ],
    [
        ("A", "O"), ("Polícia", "B-ORGANIZACAO"), ("Judiciária", "I-ORGANIZACAO"),
        ("deteve", "O"), ("Rui", "B-PESSOA"), ("Costa", "I-PESSOA"),
        ("em", "O"), ("Coimbra", "B-LOCAL"), (".", "O")
    ],
    [
        ("Suspeito", "O"), ("de", "O"), ("assalto", "B-CRIME"),
        ("à", "I-CRIME"), ("mão", "I-CRIME"), ("armada", "I-CRIME"),
        ("na", "O"), ("Amadora", "B-LOCAL"), ("foi", "O"),
        ("identificado", "O"), (".", "O")
    ],
    [
        ("O", "O"), ("crime", "O"), ("ocorreu", "O"), ("em", "O"),
        ("Setúbal", "B-LOCAL"), ("no", "O"), ("dia", "O"),
        ("15", "B-DATA"), ("de", "I-DATA"), ("março", "I-DATA"), (".", "O")
    ],

    # --- NOVOS EXEMPLOS ---

    # Roubo + LOCAL + DATA
    [
        ("O", "O"), ("roubo", "B-CRIME"), ("aconteceu", "O"), ("em", "O"),
        ("Sintra", "B-LOCAL"), ("a", "O"), ("3", "B-DATA"),
        ("de", "I-DATA"), ("fevereiro", "I-DATA"), (".", "O")
    ],
    # PESSOA + CRIME + LOCAL
    [
        ("Luís", "B-PESSOA"), ("Marques", "I-PESSOA"), ("foi", "O"),
        ("apanhado", "O"), ("a", "O"), ("conduzir", "O"), ("bêbedo", "O"),
        ("em", "O"), ("Aveiro", "B-LOCAL"), (".", "O")
    ],
    # ORGANIZACAO + CRIME + LOCAL
    [
        ("A", "O"), ("Interpol", "B-ORGANIZACAO"), ("desmantelou", "O"),
        ("uma", "O"), ("rede", "O"), ("de", "O"), ("tráfico", "B-CRIME"),
        ("humano", "I-CRIME"), ("com", "O"), ("base", "O"), ("em", "O"),
        ("Lisboa", "B-LOCAL"), (".", "O")
    ],
    # PESSOA + ORGANIZACAO
    [
        ("Fernando", "B-PESSOA"), ("Gomes", "I-PESSOA"), ("foi", "O"),
        ("interrogado", "O"), ("pela", "O"), ("Polícia", "B-ORGANIZACAO"),
        ("Judiciária", "I-ORGANIZACAO"), (".", "O")
    ],
    # CRIME + LOCAL + DATA
    [
        ("Um", "O"), ("homicídio", "B-CRIME"), ("foi", "O"), ("registado", "O"),
        ("em", "O"), ("Almada", "B-LOCAL"), ("em", "O"), ("outubro", "B-DATA"),
        ("de", "I-DATA"), ("2022", "I-DATA"), (".", "O")
    ],
    # PESSOA + CRIME
    [
        ("Sónia", "B-PESSOA"), ("Figueiredo", "I-PESSOA"), ("foi", "O"),
        ("acusada", "O"), ("de", "O"), ("corrupção", "B-CRIME"),
        ("ativa", "I-CRIME"), (".", "O")
    ],
    # ORGANIZACAO + PESSOA + LOCAL
    [
        ("O", "O"), ("SEF", "B-ORGANIZACAO"), ("deteve", "O"),
        ("Andrei", "B-PESSOA"), ("Popescu", "I-PESSOA"), ("no", "O"),
        ("Aeroporto", "B-LOCAL"), ("de", "I-LOCAL"), ("Lisboa", "I-LOCAL"), (".", "O")
    ],
    # CRIME + PESSOA + DATA
    [
        ("O", "O"), ("sequestro", "B-CRIME"), ("de", "O"),
        ("Ricardo", "B-PESSOA"), ("Nunes", "I-PESSOA"), ("ocorreu", "O"),
        ("em", "O"), ("abril", "B-DATA"), (".", "O")
    ],
    # LOCAL + ORGANIZACAO + CRIME
    [
        ("Em", "O"), ("Cascais", "B-LOCAL"), ("a", "O"), ("PSP", "B-ORGANIZACAO"),
        ("registou", "O"), ("vários", "O"), ("casos", "O"), ("de", "O"),
        ("vandalismo", "B-CRIME"), (".", "O")
    ],
    # PESSOA + LOCAL + CRIME
    [
        ("Bruno", "B-PESSOA"), ("Tavares", "I-PESSOA"), ("foi", "O"),
        ("preso", "O"), ("em", "O"), ("Matosinhos", "B-LOCAL"),
        ("por", "O"), ("tráfico", "B-CRIME"), ("de", "I-CRIME"),
        ("estupefacientes", "I-CRIME"), (".", "O")
    ],
    # ORGANIZACAO + LOCAL
    [
        ("A", "O"), ("ASAE", "B-ORGANIZACAO"), ("encerrou", "O"),
        ("vários", "O"), ("estabelecimentos", "O"), ("em", "O"),
        ("Guimarães", "B-LOCAL"), (".", "O")
    ],
    # PESSOA + CRIME + DATA
    [
        ("Miguel", "B-PESSOA"), ("Carvalho", "I-PESSOA"), ("foi", "O"),
        ("condenado", "O"), ("por", "O"), ("abuso", "B-CRIME"),
        ("de", "I-CRIME"), ("poder", "I-CRIME"), ("em", "O"),
        ("setembro", "B-DATA"), ("de", "I-DATA"), ("2021", "I-DATA"), (".", "O")
    ],
    # ORGANIZACAO + CRIME + DATA
    [
        ("O", "O"), ("Tribunal", "B-ORGANIZACAO"), ("de", "I-ORGANIZACAO"),
        ("Coimbra", "I-ORGANIZACAO"), ("julgou", "O"), ("um", "O"),
        ("caso", "O"), ("de", "O"), ("falsificação", "B-CRIME"),
        ("em", "O"), ("março", "B-DATA"), (".", "O")
    ],
    # PESSOA + PESSOA + CRIME + LOCAL
    [
        ("Jorge", "B-PESSOA"), ("Lima", "I-PESSOA"), ("e", "O"),
        ("Paulo", "B-PESSOA"), ("Serra", "I-PESSOA"), ("foram", "O"),
        ("detidos", "O"), ("por", "O"), ("furto", "B-CRIME"),
        ("qualificado", "I-CRIME"), ("em", "O"), ("Loures", "B-LOCAL"), (".", "O")
    ],
    # LOCAL + CRIME + DATA
    [
        ("Em", "O"), ("Viseu", "B-LOCAL"), ("ocorreu", "O"), ("um", "O"),
        ("incêndio", "B-CRIME"), ("criminoso", "I-CRIME"), ("em", "O"),
        ("julho", "B-DATA"), ("de", "I-DATA"), ("2023", "I-DATA"), (".", "O")
    ],
    # PESSOA + ORGANIZACAO + CRIME
    [
        ("Diana", "B-PESSOA"), ("Moura", "I-PESSOA"), ("foi", "O"),
        ("acusada", "O"), ("pelo", "O"), ("Ministério", "B-ORGANIZACAO"),
        ("Público", "I-ORGANIZACAO"), ("de", "O"), ("fraude", "B-CRIME"),
        ("fiscal", "I-CRIME"), (".", "O")
    ],
    # ORGANIZACAO + PESSOA + DATA
    [
        ("A", "O"), ("GNR", "B-ORGANIZACAO"), ("deteve", "O"),
        ("Vítor", "B-PESSOA"), ("Pinto", "I-PESSOA"), ("em", "O"),
        ("dezembro", "B-DATA"), ("de", "I-DATA"), ("2022", "I-DATA"), (".", "O")
    ],
    # CRIME + LOCAL
    [
        ("Foi", "O"), ("detetado", "O"), ("um", "O"), ("esquema", "O"),
        ("de", "O"), ("lavagem", "B-CRIME"), ("de", "I-CRIME"),
        ("dinheiro", "I-CRIME"), ("em", "O"), ("Évora", "B-LOCAL"), (".", "O")
    ],
    # PESSOA + LOCAL + DATA
    [
        ("Nuno", "B-PESSOA"), ("Bastos", "I-PESSOA"), ("foi", "O"),
        ("visto", "O"), ("pela", "O"), ("última", "O"), ("vez", "O"),
        ("em", "O"), ("Leiria", "B-LOCAL"), ("em", "O"),
        ("novembro", "B-DATA"), (".", "O")
    ],
    # ORGANIZACAO + CRIME + LOCAL
    [
        ("A", "O"), ("Europol", "B-ORGANIZACAO"), ("coordenou", "O"),
        ("uma", "O"), ("operação", "O"), ("contra", "O"),
        ("cibercrime", "B-CRIME"), ("com", "O"), ("base", "O"),
        ("em", "O"), ("Portugal", "B-LOCAL"), (".", "O")
    ],
    # PESSOA + CRIME + LOCAL + DATA
    [
        ("Rafael", "B-PESSOA"), ("Cunha", "I-PESSOA"), ("praticou", "O"),
        ("violência", "B-CRIME"), ("doméstica", "I-CRIME"),
        ("em", "O"), ("Braga", "B-LOCAL"), ("em", "O"),
        ("agosto", "B-DATA"), ("de", "I-DATA"), ("2023", "I-DATA"), (".", "O")
    ],
    # LOCAL + ORGANIZACAO + PESSOA
    [
        ("Em", "O"), ("Setúbal", "B-LOCAL"), ("a", "O"),
        ("Polícia", "B-ORGANIZACAO"), ("Judiciária", "I-ORGANIZACAO"),
        ("prendeu", "O"), ("Henrique", "B-PESSOA"), ("Lopes", "I-PESSOA"), (".", "O")
    ],
    # CRIME + PESSOA
    [
        ("A", "O"), ("tentativa", "O"), ("de", "O"), ("homicídio", "B-CRIME"),
        ("foi", "O"), ("atribuída", "O"), ("a", "O"),
        ("Filipe", "B-PESSOA"), ("Rocha", "I-PESSOA"), (".", "O")
    ],
    # ORGANIZACAO + LOCAL + DATA
    [
        ("O", "O"), ("Tribunal", "B-ORGANIZACAO"), ("de", "I-ORGANIZACAO"),
        ("Évora", "I-ORGANIZACAO"), ("emitiu", "O"), ("mandado", "O"),
        ("em", "O"), ("junho", "B-DATA"), ("de", "I-DATA"), ("2023", "I-DATA"), (".", "O")
    ],
    # PESSOA + ORGANIZACAO + LOCAL + CRIME
    [
        ("Tiago", "B-PESSOA"), ("Matos", "I-PESSOA"), ("foi", "O"),
        ("presente", "O"), ("ao", "O"), ("Tribunal", "B-ORGANIZACAO"),
        ("de", "I-ORGANIZACAO"), ("Lisboa", "I-ORGANIZACAO"),
        ("por", "O"), ("extorsão", "B-CRIME"), (".", "O")
    ],
    # DATA + CRIME + LOCAL
    [
        ("Em", "O"), ("janeiro", "B-DATA"), ("de", "I-DATA"), ("2024", "I-DATA"),
        ("foi", "O"), ("registado", "O"), ("um", "O"), ("roubo", "B-CRIME"),
        ("em", "O"), ("Santarém", "B-LOCAL"), (".", "O")
    ],
    # PESSOA + CRIME
    [
        ("Carla", "B-PESSOA"), ("Vieira", "I-PESSOA"), ("foi", "O"),
        ("indiciada", "O"), ("por", "O"), ("peculato", "B-CRIME"), (".", "O")
    ],
    # ORGANIZACAO + CRIME + PESSOA
    [
        ("O", "O"), ("DIAP", "B-ORGANIZACAO"), ("acusou", "O"),
        ("Armando", "B-PESSOA"), ("Reis", "I-PESSOA"), ("de", "O"),
        ("tráfico", "B-CRIME"), ("de", "I-CRIME"), ("influências", "I-CRIME"), (".", "O")
    ],
    # CRIME + LOCAL + ORGANIZACAO
    [
        ("O", "O"), ("assalto", "B-CRIME"), ("a", "O"), ("banco", "O"),
        ("em", "O"), ("Vila", "B-LOCAL"), ("Nova", "I-LOCAL"), ("de", "I-LOCAL"),
        ("Gaia", "I-LOCAL"), ("foi", "O"), ("investigado", "O"),
        ("pela", "O"), ("PJ", "B-ORGANIZACAO"), (".", "O")
    ],
    # PESSOA + DATA + LOCAL
    [
        ("Susana", "B-PESSOA"), ("Monteiro", "I-PESSOA"), ("desapareceu", "O"),
        ("em", "O"), ("fevereiro", "B-DATA"), ("em", "O"),
        ("Viana", "B-LOCAL"), ("do", "I-LOCAL"), ("Castelo", "I-LOCAL"), (".", "O")
    ],
    # ORGANIZACAO + LOCAL + CRIME
    [
        ("A", "O"), ("PSP", "B-ORGANIZACAO"), ("de", "O"),
        ("Almada", "B-LOCAL"), ("deteve", "O"), ("um", "O"),
        ("suspeito", "O"), ("de", "O"), ("violação", "B-CRIME"), (".", "O")
    ],
    # PESSOA + CRIME + DATA
    [
        ("Eduardo", "B-PESSOA"), ("Ferreira", "I-PESSOA"), ("foi", "O"),
        ("julgado", "O"), ("por", "O"), ("evasão", "B-CRIME"),
        ("fiscal", "I-CRIME"), ("em", "O"), ("maio", "B-DATA"),
        ("de", "I-DATA"), ("2022", "I-DATA"), (".", "O")
    ],
    # LOCAL + CRIME + DATA
    [
        ("Em", "O"), ("Portimão", "B-LOCAL"), ("ocorreu", "O"),
        ("um", "O"), ("homicídio", "B-CRIME"), ("na", "O"),
        ("madrugada", "O"), ("de", "O"), ("sábado", "B-DATA"), (".", "O")
    ],
    # PESSOA + ORGANIZACAO + DATA
    [
        ("Marco", "B-PESSOA"), ("Antunes", "I-PESSOA"), ("entregou-se", "O"),
        ("à", "O"), ("GNR", "B-ORGANIZACAO"), ("em", "O"),
        ("outubro", "B-DATA"), (".", "O")
    ],
    # CRIME + ORGANIZACAO
    [
        ("O", "O"), ("branqueamento", "B-CRIME"), ("de", "I-CRIME"),
        ("capitais", "I-CRIME"), ("foi", "O"), ("investigado", "O"),
        ("pelo", "O"), ("Ministério", "B-ORGANIZACAO"), ("Público", "I-ORGANIZACAO"), (".", "O")
    ],
    # PESSOA + LOCAL + ORGANIZACAO + CRIME
    [
        ("Hugo", "B-PESSOA"), ("Fonseca", "I-PESSOA"), ("foi", "O"),
        ("preso", "O"), ("em", "O"), ("Barcelos", "B-LOCAL"),
        ("pela", "O"), ("GNR", "B-ORGANIZACAO"), ("por", "O"),
        ("posse", "B-CRIME"), ("de", "I-CRIME"), ("armas", "I-CRIME"), (".", "O")
    ],
    # DATA + PESSOA + CRIME
    [
        ("Em", "O"), ("março", "B-DATA"), ("de", "I-DATA"), ("2024", "I-DATA"),
        ("Inês", "B-PESSOA"), ("Correia", "I-PESSOA"), ("foi", "O"),
        ("detida", "O"), ("por", "O"), ("condução", "B-CRIME"),
        ("sob", "I-CRIME"), ("efeito", "I-CRIME"), ("de", "I-CRIME"),
        ("álcool", "I-CRIME"), (".", "O")
    ],
    # ORGANIZACAO + LOCAL + PESSOA
    [
        ("A", "O"), ("Polícia", "B-ORGANIZACAO"), ("Municipal", "I-ORGANIZACAO"),
        ("de", "I-ORGANIZACAO"), ("Lisboa", "I-ORGANIZACAO"), ("identificou", "O"),
        ("Ricardo", "B-PESSOA"), ("Pires", "I-PESSOA"), (".", "O")
    ],
    # CRIME + LOCAL + PESSOA
    [
        ("O", "O"), ("furto", "B-CRIME"), ("em", "O"),
        ("Odivelas", "B-LOCAL"), ("foi", "O"), ("cometido", "O"),
        ("por", "O"), ("Gonçalo", "B-PESSOA"), ("Dias", "I-PESSOA"), (".", "O")
    ],
    # ORGANIZACAO + CRIME + DATA
    [
        ("O", "O"), ("INEM", "B-ORGANIZACAO"), ("reportou", "O"),
        ("um", "O"), ("caso", "O"), ("de", "O"), ("agressão", "B-CRIME"),
        ("em", "O"), ("dezembro", "B-DATA"), (".", "O")
    ],
    # PESSOA + PESSOA + ORGANIZACAO
    [
        ("Rosa", "B-PESSOA"), ("Sousa", "I-PESSOA"), ("e", "O"),
        ("Vera", "B-PESSOA"), ("Leal", "I-PESSOA"), ("foram", "O"),
        ("ouvidas", "O"), ("pelo", "O"), ("Ministério", "B-ORGANIZACAO"),
        ("Público", "I-ORGANIZACAO"), (".", "O")
    ],
    # LOCAL + LOCAL + CRIME
    [
        ("Entre", "O"), ("Lisboa", "B-LOCAL"), ("e", "O"),
        ("Setúbal", "B-LOCAL"), ("foi", "O"), ("intercetado", "O"),
        ("um", "O"), ("veículo", "O"), ("com", "O"),
        ("droga", "B-CRIME"), (".", "O")
    ],
]


RAW_VAL_DATA = [
    [
        ("Ana", "B-PESSOA"), ("Rodrigues", "I-PESSOA"), ("foi", "O"),
        ("presa", "O"), ("em", "O"), ("Évora", "B-LOCAL"),
        ("pela", "O"), ("GNR", "B-ORGANIZACAO"), (".", "O")
    ],
    [
        ("O", "O"), ("Tribunal", "B-ORGANIZACAO"), ("de", "I-ORGANIZACAO"),
        ("Lisboa", "I-ORGANIZACAO"), ("julgou", "O"), ("Manuel", "B-PESSOA"),
        ("Lopes", "I-PESSOA"), ("por", "O"), ("corrupção", "B-CRIME"), (".", "O")
    ],
    [
        ("Álvaro", "B-PESSOA"), ("Baptista", "I-PESSOA"), ("foi", "O"),
        ("condenado", "O"), ("por", "O"), ("tráfico", "B-CRIME"),
        ("de", "I-CRIME"), ("armas", "I-CRIME"), ("em", "O"),
        ("agosto", "B-DATA"), ("de", "I-DATA"), ("2023", "I-DATA"), (".", "O")
    ],
    [
        ("A", "O"), ("PSP", "B-ORGANIZACAO"), ("deteve", "O"),
        ("três", "O"), ("suspeitos", "O"), ("em", "O"),
        ("Cascais", "B-LOCAL"), (".", "O")
    ],
    [
        ("Em", "O"), ("Guimarães", "B-LOCAL"), ("a", "O"),
        ("Polícia", "B-ORGANIZACAO"), ("Judiciária", "I-ORGANIZACAO"),
        ("investigou", "O"), ("um", "O"), ("caso", "O"),
        ("de", "O"), ("burla", "B-CRIME"), ("informática", "I-CRIME"), (".", "O")
    ],
    [
        ("Cristina", "B-PESSOA"), ("Neves", "I-PESSOA"), ("foi", "O"),
        ("indiciada", "O"), ("por", "O"), ("falsificação", "B-CRIME"),
        ("de", "I-CRIME"), ("documentos", "I-CRIME"), (".", "O")
    ],
    [
        ("O", "O"), ("incidente", "O"), ("ocorreu", "O"), ("em", "O"),
        ("fevereiro", "B-DATA"), ("de", "I-DATA"), ("2024", "I-DATA"),
        ("em", "O"), ("Braga", "B-LOCAL"), (".", "O")
    ],
    [
        ("Rui", "B-PESSOA"), ("Monteiro", "I-PESSOA"), ("e", "O"),
        ("Filipa", "B-PESSOA"), ("Castro", "I-PESSOA"), ("foram", "O"),
        ("detidos", "O"), ("pela", "O"), ("GNR", "B-ORGANIZACAO"),
        ("por", "O"), ("roubo", "B-CRIME"), (".", "O")
    ],
    [
        ("A", "O"), ("Europol", "B-ORGANIZACAO"), ("interveio", "O"),
        ("num", "O"), ("caso", "O"), ("de", "O"),
        ("cibercrime", "B-CRIME"), ("com", "O"), ("origem", "O"),
        ("em", "O"), ("Portugal", "B-LOCAL"), (".", "O")
    ],
    [
        ("Em", "O"), ("julho", "B-DATA"), ("de", "I-DATA"), ("2022", "I-DATA"),
        ("o", "O"), ("Ministério", "B-ORGANIZACAO"), ("Público", "I-ORGANIZACAO"),
        ("abriu", "O"), ("inquérito", "O"), ("por", "O"),
        ("homicídio", "B-CRIME"), ("em", "O"), ("Faro", "B-LOCAL"), (".", "O")
    ],
]