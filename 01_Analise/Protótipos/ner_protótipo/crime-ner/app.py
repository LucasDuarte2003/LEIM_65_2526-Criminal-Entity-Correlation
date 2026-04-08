import uuid
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from predict import predict_entities

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

NEWS_PATH = r"C:\Users\lucas\Documents\GitHub\LEIM_65_2526-Criminal-Entity-Correlation\01_Analise\Protótipos\web_prototipo\frontend\src\data\news.json"


def load_news():
    with open(NEWS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_news(data):
    with open(NEWS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def convert_to_char_offsets(text: str, entities: list) -> list:
    """Converte start_word/end_word para offsets de caracteres."""
    words = text.split()
    word_starts = []
    pos = 0
    for word in words:
        pos = text.find(word, pos)
        word_starts.append(pos)
        pos += len(word)

    result = []
    for ent in entities:
        start_word = ent["start_word"]
        end_word = ent["end_word"]
        char_start = word_starts[start_word]
        char_end = word_starts[end_word] + len(words[end_word])
        result.append({
            "start": char_start,
            "end": char_end,
            "text": ent["text"],
            "label": ent["label"]
        })
    return result


class TextInput(BaseModel):
    text: str


@app.get("/api/noticias")
def get_noticias():
    return load_news()


@app.post("/api/predict")
def predict_route(body: TextInput):
    text = body.text.strip()
    if not text:
        return {"error": "Texto vazio"}

    raw_entities = predict_entities(text)
    entities = convert_to_char_offsets(text, raw_entities)

    noticia = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "entities": entities
    }

    news = load_news()
    news.append(noticia)
    save_news(news)

    return noticia


class SaveInput(BaseModel):
    id: str
    text: str
    entities: list


@app.post("/api/guardar")
def guardar_noticia(body: SaveInput):
    news = load_news()

    # Substitui a notícia com o mesmo id pela versão editada
    updated = False
    for i, n in enumerate(news):
        if n["id"] == body.id:
            news[i] = {"id": body.id, "text": body.text, "entities": body.entities}
            updated = True
            break

    # Se por algum motivo não encontrar, adiciona
    if not updated:
        news.append({"id": body.id, "text": body.text, "entities": body.entities})

    save_news(news)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)