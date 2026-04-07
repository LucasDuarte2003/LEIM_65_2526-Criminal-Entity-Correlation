import json

with open("datasets_por_anotar/noticias_11-20.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Primeiras 5 → para ti
with open("datasets_por_anotar/noticias_11-15.json", "w", encoding="utf-8") as f:
    json.dump(data[:5], f, ensure_ascii=False, indent=2)

# Últimas 5 → para o Afonso
with open("datasets_por_anotar/noticias_16-20.json", "w", encoding="utf-8") as f:
    json.dump(data[5:], f, ensure_ascii=False, indent=2)

print("Dividido!")