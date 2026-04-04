# Responsável por:
#   1. Ler o dataset_anotado.json (formato universal)
#   2. Converter para Token BIO em memória
#   3. Dar um Dataset PyTorch pronto para treino

import json
import torch
from torch.utils.data import Dataset
from data.labels import LABEL2ID


def load_json(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def span_to_bio(article: dict) -> list[tuple[str, str]]:
    """
    Converte um artigo do formato JSON span-based para Token BIO.
    Retorna lista de (palavra, label).
    """
    text     = article["text"]
    entities = article.get("entities", [])
    words    = text.split()

    # Calcular posição de cada palavra no texto original
    word_spans = []
    pos = 0
    for word in words:
        start = text.find(word, pos)
        end   = start + len(word)
        word_spans.append((start, end))
        pos = end

    labels = ["O"] * len(words)

    for ent in entities:
        ent_start = ent["start"]
        ent_end   = ent["end"]
        ent_label = ent["label"]
        first = True
        for i, (w_start, w_end) in enumerate(word_spans):
            if w_start >= ent_start and w_end <= ent_end:
                labels[i] = f"B-{ent_label}" if first else f"I-{ent_label}"
                first = False

    return list(zip(words, labels))


def load_bio_from_json(filepath: str) -> list[list[tuple[str, str]]]:
    """
    Lê o JSON e devolve todas as frases em formato BIO.
    Ignora artigos sem entidades anotadas.
    """
    data = load_json(filepath)
    return [span_to_bio(article) for article in data if article.get("entities")]


class NERDataset(Dataset):
    """
    Dataset PyTorch para treino do modelo NER.
    Recebe frases em formato BIO e tokeniza com o tokenizador do modelo.
    """

    def __init__(self, sentences: list, tokenizer, max_length: int = 256):
        self.examples = []

        for sentence in sentences:
            words  = [pair[0] for pair in sentence]
            labels = [pair[1] for pair in sentence]

            encoding = tokenizer(
                words,
                is_split_into_words=True,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt"
            )

            word_ids       = encoding.word_ids(batch_index=0)
            aligned_labels = []
            previous_word_id = None

            for word_id in word_ids:
                if word_id is None:
                    aligned_labels.append(-100)
                elif word_id != previous_word_id:
                    label = labels[word_id]
                    aligned_labels.append(LABEL2ID.get(label, 0))
                else:
                    aligned_labels.append(-100)
                previous_word_id = word_id

            self.examples.append({
                "input_ids":      encoding["input_ids"].squeeze(),
                "attention_mask": encoding["attention_mask"].squeeze(),
                "labels":         torch.tensor(aligned_labels)
            })

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]