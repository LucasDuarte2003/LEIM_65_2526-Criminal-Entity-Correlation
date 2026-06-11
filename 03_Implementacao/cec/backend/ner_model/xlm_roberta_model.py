import os

import torch
from transformers import AutoTokenizer, XLMRobertaForTokenClassification

from ner_model.data.labels import ID2LABEL

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_model")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class NERModel:
    """
    Wrapper do modelo xlm-roberta fine-tuned.

    Carregado e mantido em cache pelo NERManager. Expõe predict_entities(texto),
    que devolve entidades em offsets de palavra (start_word/end_word) — a conversão
    para offsets de caractere é feita no ner_service.
    """

    def __init__(self, model_path: str = MODEL_PATH):
        print(f"A carregar modelo de {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = XLMRobertaForTokenClassification.from_pretrained(model_path)
        self.model.eval()
        self.model = self.model.to(device)
        print("Modelo carregado!")

    def predict_entities(self, text: str) -> list:
        """Extrai entidades do texto (offsets a nível de palavra)."""
        words = text.split()

        encoding = self.tokenizer(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )

        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)

        predictions = torch.argmax(outputs.logits, dim=-1)[0]
        word_ids = encoding.word_ids(batch_index=0)

        # Primeiro sub-token de cada palavra define a label dessa palavra.
        word_predictions = {}
        for token_idx, word_id in enumerate(word_ids):
            if word_id is None:
                continue
            if word_id not in word_predictions:
                word_predictions[word_id] = ID2LABEL[predictions[token_idx].item()]

        entities = []
        current_entity = None
        for word_id, label in sorted(word_predictions.items()):
            if label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    "text": words[word_id],
                    "label": label[2:],
                    "start_word": word_id,
                    "end_word": word_id,
                }
            elif label.startswith("I-") and current_entity:
                current_entity["text"] += " " + words[word_id]
                current_entity["end_word"] = word_id
            else:
                if current_entity:
                    entities.append(current_entity)
                current_entity = None

        if current_entity:
            entities.append(current_entity)

        return entities