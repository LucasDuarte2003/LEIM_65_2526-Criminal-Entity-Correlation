import json
import os

DATASET_ANOTADO = "dataset_anotado.json"

def clean_labelstudio_export(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = []
    for i, article in enumerate(data):
        if not article.get("annotations"):
            continue
        annotation = article["annotations"][0]
        if annotation.get("was_cancelled"):
            continue

        text = article["data"]["text"]
        original_id = article["data"].get("original_id") or article.get("id") or f"{os.path.basename(filepath)}-{i}"

        entities = []
        for item in annotation.get("result", []):
            val = item["value"]
            entities.append({
                "start": val["start"],
                "end":   val["end"],
                "text":  val["text"],
                "label": val["labels"][0]
            })

        entities.sort(key=lambda x: x["start"])
        cleaned.append({"id": original_id, "text": text, "entities": entities})

    return cleaned


def merge_with_existing(new_data, existing_filepath):
    if os.path.exists(existing_filepath):
        with open(existing_filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    existing_map = {str(item["id"]): item for item in existing}
    for item in new_data:
        existing_map[str(item["id"])] = item

    return list(existing_map.values())


if __name__ == "__main__":
    ficheiros = [
        "label_studio/datasets_anotados/noticias_anotadas_16-20.json",
    ]

    for ficheiro in ficheiros:
        if not os.path.exists(ficheiro):
            print(f"Ficheiro não encontrado: {ficheiro}")
            continue

        new_data = clean_labelstudio_export(ficheiro)
        merged   = merge_with_existing(new_data, DATASET_ANOTADO)

        with open(DATASET_ANOTADO, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        print(f"{len(merged)} notícias em {DATASET_ANOTADO}")