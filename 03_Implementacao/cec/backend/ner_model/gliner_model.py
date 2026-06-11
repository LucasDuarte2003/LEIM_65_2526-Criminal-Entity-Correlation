import logging

from ner_model.data.labels import LABEL_LIST

logger = logging.getLogger(__name__)

# Tipos de entidade derivados das labels BIO (sem o "O", sem os prefixos B-/I-).
LABELS = list(dict.fromkeys(label[2:] for label in LABEL_LIST if label != "O"))


class GLiNERModel:
    """
    Wrapper do modelo GLiNER (zero-shot — não precisa de treino).

    Carregado e mantido em cache pelo NERManager. Expõe predict_entities(texto),
    que devolve entidades já em offsets de caractere (nome/tipo/inicio/fim).
    """

    def __init__(self):
        try:
            from gliner import GLiNER
            self._model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
            logger.info("Modelo GLiNER carregado.")
        except ImportError:
            raise ImportError("GLiNER não está instalado. Corre: pip install gliner")

    def predict_entities(self, texto: str) -> list:
        """Extrai entidades do texto (offsets de caractere)."""
        entidades = self._model.predict_entities(texto, LABELS)
        return [
            {
                "nome": e["text"],
                "tipo": e["label"],
                "inicio": e["start"],
                "fim": e["end"],
            }
            for e in entidades
        ]