import torch
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers import AutoTokenizer, XLMRobertaForTokenClassification
from data.labels import ID2LABEL


MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_model")

print(f"A carregar modelo de {MODEL_PATH}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = XLMRobertaForTokenClassification.from_pretrained(MODEL_PATH)
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print("Modelo carregado!\n")


def predict_entities(text: str) -> list[dict]:
    words = text.split()

    encoding = tokenizer(
        words,
        is_split_into_words=True,
        return_tensors="pt",
        truncation=True,
        max_length=128
    )

    input_ids      = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)

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


def print_entities(text, entities):
    print(f"\n📝 Texto: {text}")
    if entities:
        print("Entidades encontradas:")
        for ent in entities:
            print(f"   [{ent['label']}] → '{ent['text']}'")
    else:
        print("   (nenhuma entidade encontrada)")
    print()


# No fim do predict.py, substitui tudo a partir dos testes por isto:

if __name__ == "__main__":
    test_sentences = [
        "João Silva foi detido pela PSP em Lisboa no dia 3 de março de 2024.",
        "O suspeito conduzia um BMW Serie 3 com a matrícula 45-AB-12 quando foi intercetado.",
        "As autoridades apreenderam o telemóvel com o número 963 412 871 e encontraram emails enviados para suspeito.anonimo@gmail.com.",
        "Foram identificadas transferências para a carteira Bitcoin bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh no valor de 45 000 euros.",
        "A Polícia Judiciária de Braga deteve Pedro Alves Ferreira por tráfico de droga em fevereiro de 2024.",
    ]

    print("=" * 60)
    print("TESTES AUTOMÁTICOS")
    print("=" * 60)
    for sentence in test_sentences:
        print_entities(sentence, predict_entities(sentence))

    print("=" * 60)
    print("MODO INTERATIVO (escreve 'sair' para terminar)")
    print("=" * 60)
    while True:
        text = input("\nFrase: ").strip()
        if text.lower() == "sair":
            break
        if text:
            print_entities(text, predict_entities(text))