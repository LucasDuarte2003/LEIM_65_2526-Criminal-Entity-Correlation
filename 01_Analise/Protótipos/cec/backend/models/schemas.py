from pydantic import BaseModel
from typing import List, Optional


class Entidade(BaseModel):
    nome: str
    tipo: str
    inicio: int  # offset de caracteres na frase
    fim: int


class Frase(BaseModel):
    id: str
    texto: str
    ordem: int
    noticia_id: str
    entidades: List[Entidade] = []


class Noticia(BaseModel):
    id: str
    titulo: str
    frases: List[Frase] = []


class NoticiaResumo(BaseModel):
    """Usado na listagem — sem frases nem entidades."""
    id: str
    titulo: str


class Label(BaseModel):
    nome: str
    cor: str


class PredictInput(BaseModel):
    texto: str


class GuardarInput(BaseModel):
    id: str
    titulo: str
    frases: List[Frase]


class NoGrafo(BaseModel):
    id: str
    nome: str
    tipo: str


class ArestaGrafo(BaseModel):
    origem: str
    destino: str
    relacao: str


class GrafoFrase(BaseModel):
    nos: List[NoGrafo]
    arestas: List[ArestaGrafo]