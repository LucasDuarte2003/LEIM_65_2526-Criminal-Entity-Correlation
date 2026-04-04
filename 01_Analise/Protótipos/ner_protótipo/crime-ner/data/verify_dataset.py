# verify.py
from data.json_dataset import load_bio_from_json
from data.labels import LABEL_LIST
data = load_bio_from_json("dataset_anotado.json")

print(f"Total de notícias: {len(data)}")
print(f"Treino (~80%): {int(len(data) * 0.8)}")
print(f"Validação (~20%): {len(data) - int(len(data) * 0.8)}")
print()
print(f"\nLabels definidas: {len(LABEL_LIST)}")
print(LABEL_LIST)
# Mostrar algumas entidades da primeira notícia
print("Amostra da primeira notícia:")
for word, label in data[0]:
    if label != "O":
        print(f"  {word:30} → {label}")