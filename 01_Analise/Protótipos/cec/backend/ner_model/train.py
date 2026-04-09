import os
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, XLMRobertaForTokenClassification, get_linear_schedule_with_warmup
from seqeval.metrics import classification_report

from data.labels import LABEL_LIST, LABEL2ID, ID2LABEL
from data.json_dataset import load_bio_from_json, NERDataset

# CONFIGURAÇÃO
DATASET_PATH = "data/dataset_anotado.json"
MODEL_SAVE_PATH = "saved_model"
MODEL_NAME = "xlm-roberta-base"
NUM_EPOCHS = 40
BATCH_SIZE = 2
LEARNING_RATE = 3e-5
MAX_LENGTH = 256

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Dispositivo: {device}")

# DADOS
all_data = load_bio_from_json(DATASET_PATH)

split = int(len(all_data) * 0.8)
train_data = all_data[:split]
val_data = all_data[split:]

print(f"Treino: {len(train_data)} | Validação: {len(val_data)}")

# MODELO
print(f"A carregar {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = XLMRobertaForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABEL_LIST),
    id2label=ID2LABEL,
    label2id=LABEL2ID,
    ignore_mismatched_sizes=True
)
model = model.to(device)

# DATASETS E DATALOADERS
train_dataset = NERDataset(train_data, tokenizer, MAX_LENGTH)
val_dataset = NERDataset(val_data, tokenizer, MAX_LENGTH)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

# OPTIMIZER E SCHEDULER
optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
total_steps = len(train_loader) * NUM_EPOCHS
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=total_steps // 10,
    num_training_steps=total_steps
)

# AVALIAÇÃO
def evaluate(model, loader):
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch in loader:
            outputs = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device)
            )
            predictions = torch.argmax(outputs.logits, dim=-1)

            for pred_seq, label_seq in zip(predictions, batch["labels"]):
                pred_list, label_list = [], []
                for p, l in zip(pred_seq, label_seq):
                    if l.item() != -100:
                        pred_list.append(ID2LABEL[p.item()])
                        label_list.append(ID2LABEL[l.item()])
                all_preds.append(pred_list)
                all_labels.append(label_list)

    return classification_report(all_labels, all_preds, zero_division=0)

# TREINO
print("A iniciar treino...\n")

for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0

    for batch in train_loader:
        outputs = model(
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device),
            labels=batch["labels"].to(device)
        )
        loss = outputs.loss
        total_loss += loss.item()

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

    avg_loss = total_loss / len(train_loader)
    print(f"Época {epoch + 1}/{NUM_EPOCHS} | Loss: {avg_loss:.4f}")

    if (epoch + 1) % 5 == 0:
        print(evaluate(model, val_loader))

# GUARDAR
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
model.save_pretrained(MODEL_SAVE_PATH)
tokenizer.save_pretrained(MODEL_SAVE_PATH)
print(f"\nModelo guardado em {MODEL_SAVE_PATH}")