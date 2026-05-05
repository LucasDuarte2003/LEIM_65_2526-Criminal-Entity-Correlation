import threading
import logging
import datetime

logger = logging.getLogger(__name__)


class NERManager:
    """
    Gere o modelo NER ativo com suporte a hot-swap thread-safe.
    Usa RLock para bloquear durante a troca do modelo.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._modelo = None
        self._tipo = "xlm-roberta"  # "xlm-roberta" | "gliner"
        self._ultimo_treino = None
        self._a_treinar = False

    def carregar_modelo_inicial(self):
        """Carrega o modelo ao arrancar o servidor."""
        from ner_model.xlm_roberta_model import NERModel
        logger.info("A carregar modelo inicial...")
        with self._lock:
            self._modelo = NERModel()
        logger.info("Modelo carregado.")

    def predict_entities(self, texto: str) -> list:
        """Predição thread-safe."""
        with self._lock:
            if self._modelo is None:
                raise RuntimeError("Modelo não está carregado.")
            return self._modelo.predict_entities(texto)

    def predict_entities_ambos(self, texto: str) -> dict:
        """Corre os dois modelos em paralelo e devolve ambos os resultados."""
        import concurrent.futures
        from ner_model.xlm_roberta_model import NERModel
        from ner_model.gliner_model import GLiNERModel

        def run_xlm():
            with self._lock:
                modelo_xlm = NERModel()
            return modelo_xlm.predict_entities(texto)

        def run_gliner():
            modelo_gliner = GLiNERModel()
            return modelo_gliner.predict_entities(texto)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_xlm = executor.submit(run_xlm)
            future_gliner = executor.submit(run_gliner)
            entidades_xlm = future_xlm.result()
            entidades_gliner = future_gliner.result()

        return {"xlm": entidades_xlm, "gliner": entidades_gliner}
    def trocar_modelo(self, novo_modelo, tipo: str):
        """Hot-swap thread-safe."""
        with self._lock:
            self._modelo = novo_modelo
            self._tipo = tipo
            self._ultimo_treino = datetime.datetime.now().isoformat()
        logger.info(f"Modelo trocado para: {tipo}")

    def get_status(self) -> dict:
        """Devolve o estado atual do modelo."""
        return {
            "tipo": self._tipo,
            "ultimo_treino": self._ultimo_treino,
            "a_treinar": self._a_treinar,
            "modelo_carregado": self._modelo is not None,
        }

    def set_tipo(self, tipo: str):
        """Altera o tipo de modelo a usar na próxima predição."""
        if tipo not in ("xlm-roberta", "gliner"):
            raise ValueError(f"Tipo inválido: {tipo}")
        with self._lock:
            self._tipo = tipo
            # Carrega o modelo do novo tipo imediatamente
            if tipo == "xlm-roberta":
                from ner_model.xlm_roberta_model import NERModel
                self._modelo = NERModel()
            elif tipo == "gliner":
                from ner_model.gliner_model import GLiNERModel
                self._modelo = GLiNERModel()
        logger.info(f"Tipo de modelo alterado para: {tipo}")


# Instância global
ner_manager = NERManager()