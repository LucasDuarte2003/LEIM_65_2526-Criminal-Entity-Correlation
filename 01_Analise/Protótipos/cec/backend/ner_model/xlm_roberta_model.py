import torch
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.labels import ID2LABEL, LABEL_LIST, LABEL2ID
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, XLMRobertaForTokenClassification, get_linear_schedule_with_warmup

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_model")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class NERModel:
    """
    Wrapper orientado a objetos para o modelo xlm-roberta fine-tuned.
    Interface consistente com GLiNERModel para ser intercambiável via NERManager.
    """

    def __init__(self, model_path: str = MODEL_PATH):
        print(f"A carregar modelo de {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = XLMRobertaForTokenClassification.from_pretrained(model_path)
        self.model.eval()
        self.model = self.model.to(device)
        print("Modelo carregado!")

    def predict_entities(self, text: str) -> list:
        """Extrai entidades do texto."""
        words = text.split()

        encoding = self.tokenizer(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=128
        )

        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)

        predictions = torch.argmax(outputs.logits, dim=-1)[0]
        word_ids = encoding.word_ids(batch_index=0)

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
                    "end_word": word_id
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

    def train(self, dados: list):
        """
        Retreina o modelo com novos dados anotados.
        dados: lista de {"texto": str, "entidades": [...]}
        """
        print(f"[Treino] Device: {device}")
        print(f"[Treino] Model device: {next(self.model.parameters()).device}")
        print(f"[Treino] Nº de frases: {len(dados)}")
        NUM_EPOCHS = 5
        BATCH_SIZE = 2
        LEARNING_RATE = 3e-5
        MAX_LENGTH = 128

        class NERDatasetSimples(Dataset):
            def __init__(self, dados, tokenizer, max_length):
                self.dados = dados
                self.tokenizer = tokenizer
                self.max_length = max_length

            def __len__(self):
                return len(self.dados)

            def __getitem__(self, idx):
                item = self.dados[idx]
                words = item["tokens"]
                labels = item["labels"]

                encoding = self.tokenizer(
                    words,
                    is_split_into_words=True,
                    truncation=True,
                    max_length=self.max_length,
                    padding="max_length",
                    return_tensors="pt"
                )

                label_ids = []
                word_ids = encoding.word_ids()
                prev_word_id = None
                for word_id in word_ids:
                    if word_id is None:
                        label_ids.append(-100)
                    elif word_id != prev_word_id:
                        label_ids.append(LABEL2ID.get(labels[word_id], 0))
                    else:
                        label_ids.append(-100)
                    prev_word_id = word_id

                return {
                    "input_ids": encoding["input_ids"].squeeze(),
                    "attention_mask": encoding["attention_mask"].squeeze(),
                    "labels": torch.tensor(label_ids)
                }

        if not dados:
            print("Sem dados para treinar.")
            return self

        dataset = NERDatasetSimples(dados, self.tokenizer, MAX_LENGTH)
        loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

        optimizer = AdamW(self.model.parameters(), lr=LEARNING_RATE)
        total_steps = len(loader) * NUM_EPOCHS
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=max(1, total_steps // 10),
            num_training_steps=total_steps
        )

        self.model.train()
        for epoch in range(NUM_EPOCHS):
            total_loss = 0
            for batch in loader:
                outputs = self.model(
                    input_ids=batch["input_ids"].to(device),
                    attention_mask=batch["attention_mask"].to(device),
                    labels=batch["labels"].to(device)
                )
                loss = outputs.loss
                total_loss += loss.item()

                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()

            print(f"Época {epoch + 1}/{NUM_EPOCHS} | Loss: {total_loss / len(loader):.4f}")

        self.model.eval()

        # Guarda o modelo retreinado
        self.model.save_pretrained(MODEL_PATH)
        self.tokenizer.save_pretrained(MODEL_PATH)
        print("Modelo retreinado e guardado.")

        return self


# Função standalone mantida para compatibilidade com código existente
def predict_entities(text: str) -> list:
    """Função standalone — usa instância global."""
    return _instancia_global.predict_entities(text)


# Instância global carregada uma vez
_instancia_global = None


def get_instance() -> NERModel:
    global _instancia_global
    if _instancia_global is None:
        _instancia_global = NERModel()
    return _instancia_global