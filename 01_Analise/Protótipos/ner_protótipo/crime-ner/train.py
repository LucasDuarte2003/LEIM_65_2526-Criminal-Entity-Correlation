import torch
import os, sys
from torch.optim import AdamW  # ← mudou aqui
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup
from seqeval.metrics import classification_report

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.dataset_teste import RAW_TRAIN_DATA, RAW_VAL_DATA, LABEL_LIST, LABEL2ID, ID2LABEL
from model.ner_model import NERDataset, load_model

CONFIG = {
    "model_save_path": "./saved_model",
    "num_epochs": 40,        # ← era 10, dataset pequeno precisa de mais
    "batch_size": 2,
    "learning_rate": 3e-5,   # ← era 2e-5, ligeiramente maior
    "max_length": 128,
}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️  A usar: {device}")

model, tokenizer = load_model(
    num_labels=len(LABEL_LIST),
    label2id=LABEL2ID,
    id2label=ID2LABEL
)
model = model.to(device)

train_dataset = NERDataset(RAW_TRAIN_DATA, tokenizer, LABEL2ID, CONFIG["max_length"])
val_dataset = NERDataset(RAW_VAL_DATA, tokenizer, LABEL2ID, CONFIG["max_length"])

train_loader = DataLoader(train_dataset, batch_size=CONFIG["batch_size"], shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=CONFIG["batch_size"])

print(f"📊 Exemplos de treino: {len(train_dataset)} | Validação: {len(val_dataset)}")

optimizer = AdamW(model.parameters(), lr=CONFIG["learning_rate"])
total_steps = len(train_loader) * CONFIG["num_epochs"]
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=total_steps // 10,
    num_training_steps=total_steps
)


def evaluate(model, data_loader):
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=-1)

            for pred_seq, label_seq in zip(predictions, labels):
                pred_list, label_list = [], []
                for p, l in zip(pred_seq, label_seq):
                    if l.item() != -100:
                        pred_list.append(ID2LABEL[p.item()])
                        label_list.append(ID2LABEL[l.item()])
                all_preds.append(pred_list)
                all_labels.append(label_list)

    return classification_report(all_labels, all_preds, zero_division=0)


print("\n🚀 A iniciar treino...\n")

for epoch in range(CONFIG["num_epochs"]):
    model.train()
    total_loss = 0

    for batch in train_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss
        total_loss += loss.item()

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

    avg_loss = total_loss / len(train_loader)
    print(f"Época {epoch + 1}/{CONFIG['num_epochs']} | Loss: {avg_loss:.4f}")

    if (epoch + 1) % 2 == 0:
        print("\n📈 Métricas de validação:")
        print(evaluate(model, val_loader))

print(f"\n💾 A guardar modelo em {CONFIG['model_save_path']}...")
os.makedirs(CONFIG["model_save_path"], exist_ok=True)
model.save_pretrained(CONFIG["model_save_path"])
tokenizer.save_pretrained(CONFIG["model_save_path"])
print("✅ Modelo guardado!")