from pydantic import BaseModel
from typing import List, Optional


# --- Entidades e Frases ---

class Entidade(BaseModel):
    nome: str
    tipo: str
    inicio: int
    fim: int


class Frase(BaseModel):
    id: str
    texto: str
    ordem: int
    noticia_id: str
    entidades: List[Entidade] = []


# --- Notícias ---

class Noticia(BaseModel):
    id: str
    titulo: str
    frases: List[Frase] = []


class NoticiaResumo(BaseModel):
    """Usado na listagem — sem frases nem entidades."""
    id: str
    titulo: str


class PredictInput(BaseModel):
    texto: str
    pasta_id: str  # notícia é sempre adicionada a uma pasta


class GuardarInput(BaseModel):
    id: str
    titulo: str
    frases: List[Frase]


# --- Labels ---

class Label(BaseModel):
    nome: str
    cor: str


# --- Grafo ---

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


# --- Pastas ---

class PastaResumo(BaseModel):
    id: str
    nome: str
    projeto_id: str
    total_noticias: int = 0


class Pasta(BaseModel):
    id: str
    nome: str
    projeto_id: str
    noticias: List[NoticiaResumo] = []


class CriarPastaInput(BaseModel):
    nome: str
    projeto_id: str


class AtualizarPastaInput(BaseModel):
    nome: str


class MoverNoticiaInput(BaseModel):
    pasta_id_destino: str


# --- Projetos ---

class ProjetoResumo(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    total_pastas: int = 0
    total_noticias: int = 0


class Projeto(BaseModel):
    id: str
    nome: str
    descricao: Optional[str] = None
    pastas: List[PastaResumo] = []


class CriarProjetoInput(BaseModel):
    nome: str
    descricao: Optional[str] = None


class AtualizarProjetoInput(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None