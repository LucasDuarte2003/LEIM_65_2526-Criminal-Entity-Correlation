import json

with open("dataset_anotado.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total de notícias: {len(data)}\n")

for article in data:
    entities = article["entities"]
    print(f"  ID: {article['id']}")
    print(f"  Entidades: {len(entities)}")
    for label in ["PESSOA", "LOCAL", "ORGANIZACAO", "CRIME", "DATA", "MONTANTE"]:
        count = sum(1 for e in entities if e["label"] == label)
        if count > 0:
            print(f"    {label}: {count}")
    print()