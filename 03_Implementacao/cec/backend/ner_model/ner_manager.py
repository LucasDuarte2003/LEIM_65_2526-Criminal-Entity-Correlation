import threading
import logging
import datetime

logger = logging.getLogger(__name__)


class NERManager:
    """
    Gere os modelos NER com carregamento único e thread-safe.

    Mantém em cache uma instância de cada modelo (xlm-roberta e gliner),
    carregadas à medida que são precisas e reutilizadas entre pedidos.
    O retreino substitui a instância em cache via trocar_modelo(), por isso
    nunca fica um modelo "preso" com pesos antigos.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._xlm = None
        self._gliner = None
        self._tipo = "xlm-roberta"  # "xlm-roberta" | "gliner"
        self._ultimo_treino = None
        self._a_treinar = False

    def iniciar_treino(self) -> bool:
        """Marca o início de um treino de forma atómica.
        Devolve False se já houver um treino a decorrer (resolve a race condition)."""
        with self._lock:
            if self._a_treinar:
                return False
            self._a_treinar = True
            return True

    def terminar_treino(self) -> None:
        """Marca o fim de um treino."""
        with self._lock:
            self._a_treinar = False

    def esta_a_treinar(self) -> bool:
        """Indica se há um treino a decorrer."""
        with self._lock:
            return self._a_treinar

    def get_xlm(self):
        """Devolve a instância xlm-roberta, carregando-a uma única vez."""
        with self._lock:
            if self._xlm is None:
                from ner_model.xlm_roberta_model import NERModel
                logger.info("A carregar modelo xlm-roberta...")
                self._xlm = NERModel()
            return self._xlm

    def get_gliner(self):
        """Devolve a instância GLiNER, carregando-a uma única vez."""
        with self._lock:
            if self._gliner is None:
                from ner_model.gliner_model import GLiNERModel
                logger.info("A carregar modelo GLiNER...")
                self._gliner = GLiNERModel()
            return self._gliner

    def _modelo_ativo(self):
        """Devolve o modelo do tipo atualmente selecionado."""
        return self.get_gliner() if self._tipo == "gliner" else self.get_xlm()

    def carregar_modelo_inicial(self):
        """Pré-carrega o modelo ativo ao arrancar o servidor."""
        logger.info("A carregar modelo inicial...")
        self._modelo_ativo()
        logger.info("Modelo carregado.")

    def predict_entities(self, texto: str) -> list:
        """Predição com o modelo ativo. A inferência corre fora do lock."""
        return self._modelo_ativo().predict_entities(texto)

    def trocar_modelo(self, novo_modelo, tipo: str):
        """Substitui a instância em cache após um retreino (hot-swap).

        Atualiza só os pesos em cache do tipo indicado; não mexe no modelo
        atualmente selecionado (_tipo), para um retreino em background não
        roubar a escolha do utilizador.
        """
        with self._lock:
            if tipo == "gliner":
                self._gliner = novo_modelo
            else:
                self._xlm = novo_modelo
            self._ultimo_treino = datetime.datetime.now().isoformat()
        logger.info(f"Instância '{tipo}' atualizada (hot-swap).")

    def set_tipo(self, tipo: str):
        """Altera o tipo de modelo a usar nas próximas predições."""
        if tipo not in ("xlm-roberta", "gliner"):
            raise ValueError(f"Tipo inválido: {tipo}")
        with self._lock:
            self._tipo = tipo
        # Garante que o modelo escolhido fica carregado.
        self._modelo_ativo()
        logger.info(f"Tipo de modelo alterado para: {tipo}")

    def get_status(self) -> dict:
        """Devolve o estado atual do modelo."""
        return {
            "tipo": self._tipo,
            "ultimo_treino": self._ultimo_treino,
            "a_treinar": self._a_treinar,
            "modelo_carregado": self._xlm is not None or self._gliner is not None,
        }


# Instância global
ner_manager = NERManager()