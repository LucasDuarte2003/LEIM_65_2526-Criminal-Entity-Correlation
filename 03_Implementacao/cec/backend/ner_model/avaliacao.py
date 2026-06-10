"""
Treino de raiz e avaliação partilhados do subsistema NER.

Fonte única de "como treinamos (desde xlm-roberta-base) e como medimos (seqeval)".
Usado pelo Trainer para o retreino seguro. O avaliar_ner.py pode passar a importar
daqui mais tarde, para não haver duas formas de medir.
"""

import random

from ner_model.data.labels import LABEL_LIST, LABEL2ID, ID2LABEL

SEED = 42
MODEL_BASE = "xlm-roberta-base"
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


def dividir_treino_teste(dados: list, frac_teste: float, seed: int = SEED):
    """Split determinístico (shuffle com seed + corte)."""
    indices = list(range(len(dados)))
    rng = random.Random(seed)
    rng.shuffle(indices)
    n_teste = max(1, int(len(dados) * frac_teste))
    idx_teste = set(indices[:n_teste])
    treino = [dados[i] for i in indices if i not in idx_teste]
    teste = [dados[i] for i in indices if i in idx_teste]
    return treino, teste


def treinar_de_raiz(dados_treino: list, epocas: int = 12, lr: float = 3e-5, batch: int = 2):
    """Treina um XLM-RoBERTa desde o xlm-roberta-base. Devolve (modelo, tokenizer)."""
    import torch
    from torch.optim import AdamW
    from torch.utils.data import DataLoader, Dataset
    from transformers import (AutoTokenizer, XLMRobertaForTokenClassification,
                              get_linear_schedule_with_warmup)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_BASE)
    modelo = XLMRobertaForTokenClassification.from_pretrained(
        MODEL_BASE, num_labels=len(LABEL_LIST), id2label=ID2LABEL, label2id=LABEL2ID,
    ).to(device)

    class _DatasetNER(Dataset):
        def __len__(self):
            return len(dados_treino)

        def __getitem__(self, idx):
            item = dados_treino[idx]
            enc = tokenizer(
                item["tokens"], is_split_into_words=True, truncation=True,
                max_length=MAX_LENGTH, padding="max_length", return_tensors="pt",
            )
            label_ids, anterior = [], None
            for wid in enc.word_ids():
                if wid is None:
                    label_ids.append(-100)
                elif wid != anterior:
                    label_ids.append(LABEL2ID.get(item["labels"][wid], 0))
                else:
                    label_ids.append(-100)
                anterior = wid
            return {
                "input_ids": enc["input_ids"].squeeze(),
                "attention_mask": enc["attention_mask"].squeeze(),
                "labels": torch.tensor(label_ids),
            }

    gerador = torch.Generator()
    gerador.manual_seed(SEED)
    loader = DataLoader(_DatasetNER(), batch_size=batch, shuffle=True, generator=gerador)

    optimizer = AdamW(modelo.parameters(), lr=lr)
    total = len(loader) * epocas
    scheduler = get_linear_schedule_with_warmup(optimizer, max(1, total // 10), total)

    print(f"[retreino] device: {device} | {len(dados_treino)} frases | {epocas} épocas", flush=True)
    modelo.train()
    for epoca in range(epocas):
        perda_total = 0.0
        for b in loader:
            saidas = modelo(
                input_ids=b["input_ids"].to(device),
                attention_mask=b["attention_mask"].to(device),
                labels=b["labels"].to(device),
            )
            perda_total += saidas.loss.item()
            saidas.loss.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        print(f"  época {epoca + 1}/{epocas} | loss {perda_total / len(loader):.4f}", flush=True)
    modelo.eval()
    return modelo, tokenizer


def prever(modelo, tokenizer, tokens: list) -> list:
    """Devolve a label BIO prevista para cada token (nível-palavra)."""
    import torch

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

    labels = ["O"] * len(tokens)
    visto = set()
    for pos, wid in enumerate(enc.word_ids(batch_index=0)):
        if wid is None or wid in visto:
            continue
        visto.add(wid)
        labels[wid] = ID2LABEL[pred[pos].item()]
    return labels


def micro_f1(modelo, tokenizer, dados: list) -> float:
    """Micro-F1 a nível de entidade (seqeval) sobre um conjunto de dados."""
    from seqeval.metrics import f1_score

    if not dados:
        return 0.0
    gold = [item["labels"] for item in dados]
    predito = [prever(modelo, tokenizer, item["tokens"]) for item in dados]
    return f1_score(gold, predito, zero_division=0)