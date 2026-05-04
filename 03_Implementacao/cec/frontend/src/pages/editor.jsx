import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useNoticias } from "../js/hooks/useNoticias.jsx";
import { useLabels } from "../js/hooks/useLabels.jsx";
import { useGrafo } from "../js/hooks/useGrafo.jsx";
import NewsList from "../js/components/NewsList.jsx";
import LabelBar from "../js/components/LabelBar.jsx";
import ActionBar from "../js/components/ActionBar.jsx";
import ArticleViewer from "../js/components/ArticleViewer.jsx";
import GraphPanel from "../js/components/GraphPanel.jsx";
import { getNoticias_semelhantes } from "../js/api/client.jsx";
import "../static/css/app.css";

export default function Editor() {
  const { pastaId } = useParams();
  const navigate = useNavigate();

  const {
    lista, noticia, isLoading,
    selecionar, adicionarNoticia, guardar,
    atualizarFrase, apagarNoticia, removerDaLista,
  } = useNoticias(pastaId);

  const { labels, labelMap } = useLabels();
  const {
    grafo, grafoRelacionadas, fraseAtiva, fraseFundida, isLoading: grafoLoading,
    isLoadingRelacionadas, carregarGrafo, fundirFrase, pesquisarRelacionadas,
    limparGrafo, limparRelacionadas,
  } = useGrafo();

  const [labelSelecionada, setLabelSelecionada] = useState(null);
  const [entidadeSelecionada, setEntidadeSelecionada] = useState(null);
  const [pendingSelection, setPendingSelection] = useState(null);
  const [semelhantes, setSemelhantes] = useState(null);
  const [isLoadingSemelhantes, setIsLoadingSemelhantes] = useState(false);

  const ORDEM_LABELS = [
    "PESSOA", "LOCAL", "ORGANIZACAO", "CRIME", "DATA",
    "VIATURA", "MATRICULA", "TELEMOVEL", "EMAIL", "CRIPTO", "MONTANTE"
  ];
  const LABEL_SHORTCUTS = [
    "0","1","2","3","4","5","6","7","8","9",
    "A","B","C","D","E","F","G","H","I","J",
    "K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"
  ];

  const labelsOrdenadas = [...labels].sort(
    (a, b) => ORDEM_LABELS.indexOf(a.nome) - ORDEM_LABELS.indexOf(b.nome)
  );
  const labelsComAtalho = labelsOrdenadas.map((label, index) => ({
    ...label,
    shortcut: LABEL_SHORTCUTS[index] || null,
  }));

  useEffect(() => {
    const handleKeyDown = (event) => {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      const tecla = event.key.toUpperCase();
      const labelEncontrada = labelsComAtalho.find((l) => l.shortcut === tecla);
      if (labelEncontrada) setLabelSelecionada(labelEncontrada.nome);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [labelsComAtalho]);

  const handleTextSelect = (e, frase) => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
    const range = selection.getRangeAt(0);
    const texto = selection.toString().trim();
    if (!texto) return;
    const preRange = range.cloneRange();
    preRange.selectNodeContents(e.currentTarget);
    preRange.setEnd(range.startContainer, range.startOffset);
    const inicio = preRange.toString().length;
    const fim = inicio + texto.length;
    setPendingSelection({ fraseId: frase.id, inicio, fim, texto });
    setEntidadeSelecionada(null);
  };

  const handleUpdate = () => {
    if (!labelSelecionada) return alert("Seleciona um tipo de entidade.");
    if (!pendingSelection) return alert("Seleciona texto na notícia.");
    if (!noticia) return;
    const frase = noticia.frases.find((f) => f.id === pendingSelection.fraseId);
    if (!frase) return;
    const { inicio, fim, texto, fraseId } = pendingSelection;
    const overlap = frase.entidades.some((e) => inicio < e.fim && fim > e.inicio);
    if (overlap) return alert("A seleção sobrepõe-se a uma entidade existente.");
    const novasEntidades = [
      ...frase.entidades,
      { nome: texto, tipo: labelSelecionada, inicio, fim },
    ].sort((a, b) => a.inicio - b.inicio);
    atualizarFrase(fraseId, novasEntidades);
    setPendingSelection(null);
    window.getSelection()?.removeAllRanges();
  };

  const handleRemover = () => {
    if (!entidadeSelecionada) return alert("Clica numa entidade para a selecionar.");
    if (!noticia) return;
    const { fraseId, index } = entidadeSelecionada;
    const frase = noticia.frases.find((f) => f.id === fraseId);
    if (!frase) return;
    const novasEntidades = frase.entidades.filter((_, i) => i !== index);
    atualizarFrase(fraseId, novasEntidades);
    setEntidadeSelecionada(null);
  };

  const handleEntidadeClick = (fraseId, index, entidade) => {
    setEntidadeSelecionada({ fraseId, index, entidade });
    setLabelSelecionada(entidade.tipo);
    setPendingSelection(null);
  };

  const handleApagarNoticia = async () => {
    if (!noticia) return;
    if (!confirm(`Apagar a notícia "${noticia.titulo}"? Esta ação não pode ser revertida.`)) return;
    await apagarNoticia(noticia.id);
    limparGrafo();
  };

  const handleSemelhantes = async () => {
    if (!noticia) return;
    setIsLoadingSemelhantes(true);
    try {
      const resultado = await getNoticias_semelhantes(noticia.id);
      setSemelhantes(resultado);
    } catch {
      alert("Erro ao procurar notícias semelhantes.");
    } finally {
      setIsLoadingSemelhantes(false);
    }
  };

  return (
    <div className="app">
      <NewsList
        lista={lista}
        noticiaAtiva={noticia}
        pastaId={pastaId}
        onSelecionar={selecionar}
        onAdicionar={(texto) => adicionarNoticia(texto, pastaId)}
        onApagar={handleApagarNoticia}
        onMover={removerDaLista}
        onVoltar={() => navigate("/")}
        isLoading={isLoading}
      />

      <main className="main-content">
        <h1>Criminal Entity Correlation</h1>
        <LabelBar
          labels={labelsComAtalho}
          labelSelecionada={labelSelecionada}
          onSelecionar={setLabelSelecionada}
        />
        <ActionBar
          labelSelecionada={labelSelecionada}
          textoSelecionado={pendingSelection?.texto}
          onUpdate={handleUpdate}
          onRemover={handleRemover}
          onGuardar={() => guardar(limparGrafo)}
          onSemelhantes={handleSemelhantes}
          noticiaId={noticia?.id}
          isLoading={isLoading || isLoadingSemelhantes}
        />
        <ArticleViewer
          noticia={noticia}
          labelMap={labelMap}
          fraseAtiva={fraseAtiva}
          fraseFundida={fraseFundida}
          entidadeSelecionada={entidadeSelecionada}
          onFraseClick={carregarGrafo}
          onFraseFundir={fundirFrase}
          onEntidadeClick={handleEntidadeClick}
          onTextSelect={handleTextSelect}
        />
      </main>

      <GraphPanel
        grafo={grafo}
        grafoRelacionadas={grafoRelacionadas}
        labelMap={labelMap}
        isLoading={grafoLoading}
        isLoadingRelacionadas={isLoadingRelacionadas}
        onPesquisarRelacionadas={pesquisarRelacionadas}
        onLimparRelacionadas={limparRelacionadas}
      />

      {/* Modal de notícias semelhantes */}
      {semelhantes && (
        <div className="modal-overlay" onClick={() => setSemelhantes(null)}>
          <div className="modal semelhantes-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Notícias Semelhantes</h2>
            {semelhantes.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "13px" }}>
                Não foram encontradas notícias semelhantes.
              </p>
            ) : (
              <div className="semelhantes-lista">
                {semelhantes.map((n) => (
                  <div key={n.id} className="semelhante-item" onClick={() => {
                    selecionar(n.id);
                    setSemelhantes(null);
                  }}>
                    <div className="semelhante-header">
                      <span className="semelhante-titulo">{n.titulo}</span>
                      <span className="semelhante-score">{n.percentagem}%</span>
                    </div>
                    <div className="semelhante-meta">
                      <span>📁 {n.pasta_nome || "—"}</span>
                      <span>📂 {n.projeto_nome || "—"}</span>
                      <span>{n.entidades_comuns} entidade{n.entidades_comuns !== 1 ? "s" : ""} em comum</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="modal-actions">
              <button className="btn-confirmar" onClick={() => setSemelhantes(null)}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}