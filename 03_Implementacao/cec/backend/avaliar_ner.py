"""
avaliar_ner.py — treino e avaliação do modelo NER (XLM-RoBERTa) com métricas por tipo.

    # 1) Avaliar o modelo que já tens em ner_model/saved_model
    python avaliar_ner.py --modo avaliar-atual

    # 2) Treinar de raiz (desde xlm-roberta-base) e avaliar
    python avaliar_ner.py --modo treinar-avaliar --epocas 5

    # 2b) ... e guardar o modelo treinado por cima do saved_model
    python avaliar_ner.py --modo treinar-avaliar --epocas 5 --guardar

Dependências extra: pip install seqeval
(O resto — torch, transformers — já tens.)

Notas:
- Os dados vêm da BD via services.neo4j_service.exportar_dados_treino().
  Alternativa sem BD ligada: --dados-json caminho.json (lista de {"tokens","labels"}).
- O split é determinístico (seed) para os resultados serem reproduzíveis.
- A avaliação é a nível de entidade (seqeval), não a nível de token.
"""

import argparse
import json
import os
import random
import sys

# Garante que os imports do projeto funcionam quando corrido a partir de backend/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carrega o .env (NEO4J_URI/USER/PASSWORD) como a app faz no arranque.
# Tem de acontecer ANTES de importar o neo4j_service, que lê estas variáveis ao ser importado.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

SEED = 42
MODEL_BASE = "xlm-roberta-base"
MODEL_PATH = os.path.join("ner_model", "saved_model")
MAX_LENGTH = 128


def fixar_seeds(seed: int = SEED) -> None:
    """Torna o treino e o split reproduzíveis."""
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def carregar_dados(dados_json: str = None) -> list:
    """Carrega [{'tokens': [...], 'labels': [...]}] da BD ou de um ficheiro JSON."""
    if dados_json:
        with open(dados_json, "r", encoding="utf-8") as f:
            return json.load(f)
    from services.neo4j_service import exportar_dados_treino
    return exportar_dados_treino()


def contar_entidades_por_tipo(dados: list) -> dict:
    """Conta entidades (por B-) de cada tipo, para ver a cobertura."""
    contagem = {}
    for item in dados:
        for label in item["labels"]:
            if label.startswith("B-"):
                tipo = label[2:]
                contagem[tipo] = contagem.get(tipo, 0) + 1
    return dict(sorted(contagem.items(), key=lambda kv: -kv[1]))


def dividir_treino_teste(dados: list, frac_teste: float, seed: int) -> tuple:
    """Split simples e determinístico (shuffle com seed + corte)."""
    indices = list(range(len(dados)))
    rng = random.Random(seed)
    rng.shuffle(indices)
    n_teste = max(1, int(len(dados) * frac_teste))
    idx_teste = set(indices[:n_teste])
    treino = [dados[i] for i in indices if i not in idx_teste]
    teste = [dados[i] for i in indices if i in idx_teste]
    return treino, teste


def _dataset(dados, tokenizer, label2id):
    import torch
    from torch.utils.data import Dataset

    class DatasetNER(Dataset):
        def __len__(self):
            return len(dados)

        def __getitem__(self, idx):
            item = dados[idx]
            enc = tokenizer(
                item["tokens"], is_split_into_words=True, truncation=True,
                max_length=MAX_LENGTH, padding="max_length", return_tensors="pt",
            )
            label_ids = []
            anterior = None
            for word_id in enc.word_ids():
                if word_id is None:
                    label_ids.append(-100)
                elif word_id != anterior:
                    label_ids.append(label2id.get(item["labels"][word_id], 0))
                else:
                    label_ids.append(-100)
                anterior = word_id
            return {
                "input_ids": enc["input_ids"].squeeze(),
                "attention_mask": enc["attention_mask"].squeeze(),
                "labels": torch.tensor(label_ids),
            }

    return DatasetNER()


def treinar(dados_treino, epocas, lr, batch, de_raiz=True):
    """Treina o modelo. de_raiz=True parte do xlm-roberta-base; senão do saved_model."""
    import torch
    from torch.optim import AdamW
    from torch.utils.data import DataLoader
    from transformers import (AutoTokenizer, XLMRobertaForTokenClassification,
                              get_linear_schedule_with_warmup)
    from ner_model.data.labels import LABEL_LIST, LABEL2ID, ID2LABEL

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    origem = MODEL_BASE if de_raiz else MODEL_PATH
    print(f"[treino] a partir de: {origem} | device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(origem)
    if de_raiz:
        modelo = XLMRobertaForTokenClassification.from_pretrained(
            MODEL_BASE, num_labels=len(LABEL_LIST), id2label=ID2LABEL, label2id=LABEL2ID,
        )
    else:
        modelo = XLMRobertaForTokenClassification.from_pretrained(MODEL_PATH)
    modelo.to(device)

    ds = _dataset(dados_treino, tokenizer, LABEL2ID)
    gerador = torch.Generator()
    gerador.manual_seed(SEED)
    loader = DataLoader(ds, batch_size=batch, shuffle=True, generator=gerador)

    optimizer = AdamW(modelo.parameters(), lr=lr)
    total = len(loader) * epocas
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=max(1, total // 10), num_training_steps=total
    )

    modelo.train()
    for epoca in range(epocas):
        perda_total = 0.0
        for batch_dados in loader:
            saidas = modelo(
                input_ids=batch_dados["input_ids"].to(device),
                attention_mask=batch_dados["attention_mask"].to(device),
                labels=batch_dados["labels"].to(device),
            )
            perda = saidas.loss
            perda_total += perda.item()
            optimizer.zero_grad()
            perda.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
        print(f"  época {epoca + 1}/{epocas} | loss {perda_total / len(loader):.4f}")

    modelo.eval()
    return modelo, tokenizer


def carregar_modelo_atual():
    """Carrega o modelo já treinado em saved_model."""
    import torch
    from transformers import AutoTokenizer, XLMRobertaForTokenClassification

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    modelo = XLMRobertaForTokenClassification.from_pretrained(MODEL_PATH)
    modelo.to(device)
    modelo.eval()
    return modelo, tokenizer


def prever(modelo, tokenizer, tokens) -> list:
    """Devolve a label BIO prevista para cada token (nível-palavra)."""
    import torch
    from ner_model.data.labels import ID2LABEL

    device = next(modelo.parameters()).device
    enc = tokenizer(
        tokens, is_split_into_words=True, truncation=True,
        max_length=MAX_LENGTH, return_tensors="pt",
    )
    with torch.no_grad():
        logits = modelo(
            input_ids=enc["input_ids"].to(device),
            attention_mask=enc["attention_mask"].to(device),
        ).logits
    pred = torch.argmax(logits, dim=-1)[0]

    # primeiro sub-token de cada palavra; palavras truncadas ficam "O"
    labels = ["O"] * len(tokens)
    visto = set()
    for pos, word_id in enumerate(enc.word_ids(batch_index=0)):
        if word_id is None or word_id in visto:
            continue
        visto.add(word_id)
        labels[word_id] = ID2LABEL[pred[pos].item()]
    return labels


def avaliar(modelo, tokenizer, dados_teste) -> None:
    """Imprime relatório P/R/F1 por tipo (seqeval)."""
    from seqeval.metrics import classification_report, f1_score

    gold, predito = [], []
    for item in dados_teste:
        gold.append(item["labels"])
        predito.append(prever(modelo, tokenizer, item["tokens"]))

    print("\n=== Métricas por tipo (nível-entidade) ===")
    print(classification_report(gold, predito, digits=3, zero_division=0))
    print(f"F1 (micro): {f1_score(gold, predito, zero_division=0):.3f}")


def imprimir_cobertura(titulo, dados) -> None:
    print(f"\n{titulo}: {len(dados)} frases")
    for tipo, n in contar_entidades_por_tipo(dados).items():
        print(f"  {tipo:<12} {n}")


def main():
    parser = argparse.ArgumentParser(description="Treino e avaliação do NER.")
    parser.add_argument("--modo", choices=["avaliar-atual", "treinar-avaliar", "treino-final"],
                        default="treinar-avaliar")
    parser.add_argument("--epocas", type=int, default=5)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--frac-teste", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--dados-json", default=None,
                        help="Ler dados de um JSON em vez da BD.")
    parser.add_argument("--guardar", action="store_true",
                        help="Guardar o modelo treinado em saved_model.")
    args = parser.parse_args()

    fixar_seeds(args.seed)

    dados = carregar_dados(args.dados_json)
    if not dados:
        print("Sem dados anotados. Anota notícias e guarda-as primeiro.")
        return
    imprimir_cobertura("Total", dados)

    # Modelo de produção: treina em TODOS os dados (sem split) e guarda.
    if args.modo == "treino-final":
        modelo, tokenizer = treinar(dados, args.epocas, args.lr, args.batch, de_raiz=True)
        modelo.save_pretrained(MODEL_PATH)
        tokenizer.save_pretrained(MODEL_PATH)
        print(f"\nModelo final treinado em todos os dados e guardado em {MODEL_PATH}")
        return

    treino, teste = dividir_treino_teste(dados, args.frac_teste, args.seed)
    imprimir_cobertura("Treino", treino)
    imprimir_cobertura("Teste", teste)
    if len(teste) < 5:
        print("\n[aviso] Conjunto de teste muito pequeno — as métricas são pouco fiáveis.")

    if args.modo == "avaliar-atual":
        print("\n[aviso] o modelo atual pode ter visto estas frases no treino; "
              "as métricas podem estar otimistas.")
        modelo, tokenizer = carregar_modelo_atual()
    else:
        modelo, tokenizer = treinar(treino, args.epocas, args.lr, args.batch, de_raiz=True)

    avaliar(modelo, tokenizer, teste)

    if args.guardar and args.modo == "treinar-avaliar":
        modelo.save_pretrained(MODEL_PATH)
        tokenizer.save_pretrained(MODEL_PATH)
        print(f"\nModelo guardado em {MODEL_PATH}")


if __name__ == "__main__":
    main()