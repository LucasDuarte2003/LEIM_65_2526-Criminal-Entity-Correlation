import logging

logger = logging.getLogger(__name__)

LABELS = [
    "PESSOA", "LOCAL", "ORGANIZACAO", "CRIME", "DATA",
    "VIATURA", "MATRICULA", "TELEMOVEL", "EMAIL", "CRIPTO", "MONTANTE"
]


class GLiNERModel:
    """
    Wrapper para o modelo GLiNER.
    Interface idêntica ao NERModel para ser intercambiável.
    GLiNER é zero-shot — não precisa de treino para começar a funcionar.
    """

    def __init__(self):
        try:
            from gliner import GLiNER
            self._model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
            logger.info("Modelo GLiNER carregado.")
        except ImportError:
            raise ImportError(
                "GLiNER não está instalado. "
                "Corre: pip install gliner"
            )

    def predict_entities(self, texto: str) -> list:
        """Extrai entidades do texto usando GLiNER."""
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

    def train(self, dados):
        """
        GLiNER é zero-shot — não requer treino.
        Este método existe apenas para manter a interface consistente.
        """
        logger.info("GLiNER é zero-shot, treino ignorado.")
        return self