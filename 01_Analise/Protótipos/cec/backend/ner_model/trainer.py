import threading
import logging
import time

logger = logging.getLogger(__name__)

INTERVALO_VERIFICACAO = 300  # 5 minutos entre verificações
MIN_NOTICIAS_PARA_TREINO = 5  # mínimo de notícias novas para retreinar


class Trainer:
    """
    Treina o modelo NER em background.
    Corre numa thread daemon e verifica periodicamente
    se há dados suficientes para retreinar.
    """

    def __init__(self, ner_manager, neo4j_service):
        self._ner_manager = ner_manager
        self._neo4j_service = neo4j_service
        self._thread = None
        self._stop_event = threading.Event()
        self._noticias_desde_ultimo_treino = 0

    def iniciar(self):
        """Arranca a thread de treino em background."""
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="TrainerThread"
        )
        self._thread.start()
        logger.info("Trainer iniciado em background.")

    def parar(self):
        """Para a thread de treino."""
        self._stop_event.set()

    def notificar_nova_noticia(self):
        """Chamado sempre que uma notícia é guardada pelo utilizador."""
        self._noticias_desde_ultimo_treino += 1
        logger.info(
            f"Nova notícia guardada. "
            f"Total desde último treino: {self._noticias_desde_ultimo_treino}"
        )

    def treinar_agora(self):
        """Força um retreino imediato em nova thread (botão na interface)."""
        t = threading.Thread(
            target=self._executar_treino,
            daemon=True,
            name="TreinarAgora"
        )
        t.start()

    def _loop(self):
        """Loop principal — verifica periodicamente se deve retreinar."""
        logger.info("Trainer loop iniciado.")
        while not self._stop_event.is_set():
            if self._noticias_desde_ultimo_treino >= MIN_NOTICIAS_PARA_TREINO:
                self._executar_treino()
            time.sleep(INTERVALO_VERIFICACAO)

    def _executar_treino(self):
        """Executa o treino e faz hot-swap do modelo."""
        if self._ner_manager._a_treinar:
            logger.info("Treino já em curso, a ignorar.")
            return

        self._ner_manager._a_treinar = True
        logger.info("A iniciar retreino do modelo...")

        try:
            dados = self._neo4j_service.exportar_dados_treino()
            if not dados:
                logger.warning("Sem dados suficientes para retreinar.")
                return

            tipo = self._ner_manager._tipo

            if tipo == "xlm-roberta":
                from ner_model.predict import NERModel
                novo_modelo = NERModel()
                novo_modelo.train(dados)
            elif tipo == "gliner":
                from ner_model.gliner_model import GLiNERModel
                novo_modelo = GLiNERModel()
                novo_modelo.train(dados)
            else:
                logger.error(f"Tipo de modelo desconhecido: {tipo}")
                return

            self._ner_manager.trocar_modelo(novo_modelo, tipo)
            self._noticias_desde_ultimo_treino = 0
            logger.info("Retreino concluído com sucesso.")

        except Exception as e:
            logger.error(f"Erro durante o retreino: {e}", exc_info=True)
        finally:
            self._ner_manager._a_treinar = False