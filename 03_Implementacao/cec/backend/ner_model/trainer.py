import threading
import logging
import time

logger = logging.getLogger(__name__)

INTERVALO_VERIFICACAO = 300
MIN_NOTICIAS_PARA_TREINO = 5
MIN_FRASES_PARA_TREINO = 20
FRAC_VALIDACAO = 0.2
EPOCAS_RETREINO = 8
MAX_SHARD = "200MB"


class Trainer:
    """
    Retreina o modelo NER em background, de forma SEGURA:
    treina um candidato de raiz, mede-o num val que não viu, e só promove se o
    F1 honesto dele for >= ao melhor F1 honesto já alcançado (guardado no Neo4j).
    A gravação é feita numa pasta temporária e só depois trocada pela de produção,
    por isso uma gravação falhada nunca destrói o modelo em produção.
    """

    def __init__(self, ner_manager, neo4j_service):
        self._ner_manager = ner_manager
        self._neo4j_service = neo4j_service
        self._thread = None
        self._stop_event = threading.Event()
        self._noticias_desde_ultimo_treino = 0

    def iniciar(self):
        """Arranca a thread de treino em background."""
        self._thread = threading.Thread(target=self._loop, daemon=True, name="TrainerThread")
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
        t = threading.Thread(target=self._executar_treino, daemon=True, name="TreinarAgora")
        t.start()

    def _loop(self):
        """Loop principal — verifica periodicamente se deve retreinar."""
        logger.info("Trainer loop iniciado.")
        while not self._stop_event.is_set():
            if self._noticias_desde_ultimo_treino >= MIN_NOTICIAS_PARA_TREINO:
                self._executar_treino()
            time.sleep(INTERVALO_VERIFICACAO)

    def _gravar_e_promover(self, candidato, tokenizer, MODEL_PATH):
        """Grava o candidato em shards pequenos numa pasta temporária e só depois
        a troca pela de produção (com backup reversível)."""
        import gc
        import os
        import shutil
        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Grava para uma pasta temporária. Se falhar aqui, produção fica intacta.
        temp_dir = MODEL_PATH + "__novo"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        candidato.save_pretrained(temp_dir, max_shard_size=MAX_SHARD)
        tokenizer.save_pretrained(temp_dir)
        del candidato
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Troca a pasta de produção pela nova, com backup para poder reverter.
        backup_dir = MODEL_PATH + "__old"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.rename(MODEL_PATH, backup_dir)
        try:
            os.rename(temp_dir, MODEL_PATH)
        except Exception:
            os.rename(backup_dir, MODEL_PATH)  # reverte e propaga
            raise

        # Carrega o novo modelo (liberta o antigo) antes de limpar o backup.
        from ner_model.xlm_roberta_model import NERModel
        self._ner_manager.trocar_modelo(NERModel(), "xlm-roberta")
        gc.collect()
        try:
            shutil.rmtree(backup_dir)
        except Exception:
            pass

    def _executar_treino(self):
        """Retreino seguro: treina candidato, avalia, e promove só se melhorar."""
        if not self._ner_manager.iniciar_treino():
            logger.info("Treino já em curso, a ignorar.")
            return

        logger.info("A iniciar retreino seguro...")
        print("[retreino] a iniciar (treino seguro)...", flush=True)
        try:
            tipo = self._ner_manager._tipo
            if tipo != "xlm-roberta":
                logger.info(f"Retreino só se aplica ao xlm-roberta (tipo atual: {tipo}). A ignorar.")
                return

            from ner_model import avaliacao
            from ner_model.xlm_roberta_model import MODEL_PATH

            dados = self._neo4j_service.exportar_dados_treino()
            if len(dados) < MIN_FRASES_PARA_TREINO:
                logger.warning(f"Dados insuficientes para retreinar ({len(dados)} frases).")
                return

            avaliacao.fixar_seeds()
            treino, val = avaliacao.dividir_treino_teste(dados, FRAC_VALIDACAO)

            # Candidato treinado de raiz, avaliado num val que não viu (F1 honesto).
            candidato, tokenizer = avaliacao.treinar_de_raiz(treino, epocas=EPOCAS_RETREINO)
            f1_candidato = avaliacao.micro_f1(candidato, tokenizer, val)
            del val

            # Compara contra o melhor F1 honesto já alcançado (guardado no Neo4j).
            melhor = self._neo4j_service.melhor_f1_promovido()
            promovido = (melhor is None or f1_candidato >= melhor)

            if promovido:
                self._gravar_e_promover(candidato, tokenizer, MODEL_PATH)
                anterior = "-" if melhor is None else f"{melhor:.3f}"
                print(f"[retreino] PROMOVIDO (F1 honesto {anterior} -> {f1_candidato:.3f})", flush=True)
            else:
                print(f"[retreino] DESCARTADO (candidato {f1_candidato:.3f} < melhor {melhor:.3f})", flush=True)

            # Regista sempre o retreino (promovido ou não) para histórico.
            self._neo4j_service.registar_retreino(f1_candidato, len(treino), EPOCAS_RETREINO, promovido)
            self._noticias_desde_ultimo_treino = 0

        except Exception as e:
            logger.error(f"Erro durante o retreino: {e}", exc_info=True)
        finally:
            self._ner_manager.terminar_treino()