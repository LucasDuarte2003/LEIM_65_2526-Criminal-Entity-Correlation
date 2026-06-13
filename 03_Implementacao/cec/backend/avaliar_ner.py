"""
avaliar_ner.py — treino e avaliação do modelo NER (XLM-RoBERTa) com métricas por tipo.

    # 1) Avaliar o modelo que já tens em ner_model/saved_model
    python avaliar_ner.py --modo avaliar-atual

    # 2) Treinar de raiz (desde xlm-roberta-base) e avaliar num conjunto de teste
    python avaliar_ner.py --modo treinar-avaliar --epocas 5

    # 2b) ... e guardar o modelo treinado por cima do saved_model
    python avaliar_ner.py --modo treinar-avaliar --epocas 5 --guardar

    # 3) Modelo de produção: treinar em TODOS os dados (sem split) e guardar
    python avaliar_ner.py --modo treino-final --epocas 12 --guardar

Dependências extra: pip install seqeval  (o resto — torch, transformers — já tens.)

Notas:
- Os dados vêm da BD via services.neo4j_service.exportar_dados_treino().
  Alternativa sem BD ligada: --dados-json caminho.json (lista de {"tokens","labels"}).
- O treino, o split e a avaliação são partilhados com o retreino da app (ner_model.avaliacao),
  por isso há uma única forma de treinar e medir em todo o projeto.
- A avaliação é a nível de entidade (seqeval), não a nível de token.
"""

import argparse
import json
import os
import sys

# Garante que os imports do projeto funcionam quando corrido a partir de backend/.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carrega o .env (NEO4J_URI/USER/PASSWORD) como a app faz no arranque, ANTES de
# importar o neo4j_service (que lê estas variáveis ao ser importado).
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

from ner_model import avaliacao
from ner_model.xlm_roberta_model import MODEL_PATH

MAX_SHARD = "200MB"  # shards pequenos ao gravar (evita pico de RAM / MemoryError)


def carregar_dados(dados_json: str = None) -> list:
    """Carrega [{'tokens': [...], 'labels': [...]}] da BD ou de um ficheiro JSON."""
    if dados_json:
        with open(dados_json, "r", encoding="utf-8") as f:
            return json.load(f)
    from services.neo4j_service import exportar_dados_treino
    return exportar_dados_treino()


def contar_entidades_por_tipo(dados: list) -> dict:
    """Conta entidades (por B-) de cada tipo, para ver a cobertura."""
    contagem = {}
    for item in dados:
        for label in item["labels"]:
            if label.startswith("B-"):
                tipo = label[2:]
                contagem[tipo] = contagem.get(tipo, 0) + 1
    return dict(sorted(contagem.items(), key=lambda kv: -kv[1]))


def carregar_modelo_atual():
    """Carrega o modelo já treinado em saved_model (para o modo avaliar-atual)."""
    import torch
    from transformers import AutoTokenizer, XLMRobertaForTokenClassification

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    modelo = XLMRobertaForTokenClassification.from_pretrained(MODEL_PATH)
    modelo.to(device)
    modelo.eval()
    return modelo, tokenizer


def avaliar(modelo, tokenizer, dados_teste) -> None:
    """Imprime relatório P/R/F1 por tipo (seqeval)."""
    from seqeval.metrics import classification_report, f1_score

    gold, predito = [], []
    for item in dados_teste:
        gold.append(item["labels"])
        predito.append(avaliacao.prever(modelo, tokenizer, item["tokens"]))

    print("\n=== Métricas por tipo (nível-entidade) ===")
    print(classification_report(gold, predito, digits=3, zero_division=0))
    print(f"F1 (micro): {f1_score(gold, predito, zero_division=0):.3f}")


def imprimir_cobertura(titulo: str, dados: list) -> None:
    print(f"\n{titulo}: {len(dados)} frases")
    for tipo, n in contar_entidades_por_tipo(dados).items():
        print(f"  {tipo:<12} {n}")


def guardar(modelo, tokenizer) -> None:
    modelo.save_pretrained(MODEL_PATH, max_shard_size=MAX_SHARD)
    tokenizer.save_pretrained(MODEL_PATH)
    print(f"\nModelo guardado em {MODEL_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Treino e avaliação do NER.")
    parser.add_argument("--modo", choices=["avaliar-atual", "treinar-avaliar", "treino-final"],
                        default="treinar-avaliar")
    parser.add_argument("--epocas", type=int, default=5)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--frac-teste", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=avaliacao.SEED)
    parser.add_argument("--dados-json", default=None, help="Ler dados de um JSON em vez da BD.")
    parser.add_argument("--guardar", action="store_true",
                        help="Guardar o modelo treinado em saved_model.")
    args = parser.parse_args()

    avaliacao.fixar_seeds(args.seed)

    dados = carregar_dados(args.dados_json)
    if not dados:
        print("Sem dados anotados. Anota notícias e guarda-as primeiro.")
        return
    imprimir_cobertura("Total", dados)

    # Modelo de produção: treina em TODOS os dados (sem split) e guarda.
    if args.modo == "treino-final":
        modelo, tokenizer = avaliacao.treinar_de_raiz(dados, epocas=args.epocas, lr=args.lr, batch=args.batch)
        guardar(modelo, tokenizer)
        return

    treino, teste = avaliacao.dividir_treino_teste(dados, args.frac_teste, args.seed)
    imprimir_cobertura("Treino", treino)
    imprimir_cobertura("Teste", teste)
    if len(teste) < 5:
        print("\n[aviso] Conjunto de teste muito pequeno — as métricas são pouco fiáveis.")

    if args.modo == "avaliar-atual":
        print("\n[aviso] o modelo atual pode ter visto estas frases no treino; "
              "as métricas podem estar otimistas.")
        modelo, tokenizer = carregar_modelo_atual()
    else:
        modelo, tokenizer = avaliacao.treinar_de_raiz(treino, epocas=args.epocas, lr=args.lr, batch=args.batch)

    avaliar(modelo, tokenizer, teste)

    if args.guardar and args.modo == "treinar-avaliar":
        guardar(modelo, tokenizer)


if __name__ == "__main__":
    main()