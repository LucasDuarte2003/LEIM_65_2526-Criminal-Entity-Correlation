import { useRef, useState } from "react";
import { useNoticias } from "./hooks/useNoticias";
import { useLabels } from "./hooks/useLabels";
import { useGrafo } from "./hooks/useGrafo";
import NewsList from "./components/NewsList";
import LabelBar from "./components/LabelBar";
import ActionBar from "./components/ActionBar";
import ArticleViewer from "./components/ArticleViewer";
import GraphPanel from "./components/GraphPanel";
import "./App.css";

export default function App() {
  const { lista, noticia, isLoading, selecionar, adicionarNoticia, guardar, atualizarFrase } =
    useNoticias();
  const { labels, labelMap } = useLabels();
  const { grafo, fraseAtiva, isLoading: grafoLoading, carregarGrafo } = useGrafo();

  const [labelSelecionada, setLabelSelecionada] = useState(null);
  const [entidadeSelecionada, setEntidadeSelecionada] = useState(null); // { fraseId, index, entidade }
  const [pendingSelection, setPendingSelection] = useState(null);       // { fraseId, inicio, fim, texto }

  // ── Selecionar texto numa frase ──────────────────────────────────────────
  const handleTextSelect = (e, frase) => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;

    const range = selection.getRangeAt(0);
    const texto = selection.toString().trim();
    if (!texto) return;

    // Calcula offsets relativos ao texto da frase
    const preRange = range.cloneRange();
    preRange.selectNodeContents(e.currentTarget);
    preRange.setEnd(range.startContainer, range.startOffset);
    const inicio = preRange.toString().length;
    const fim = inicio + texto.length;

    setPendingSelection({ fraseId: frase.id, inicio, fim, texto });
    setEntidadeSelecionada(null);
  };

  // ── Adicionar entidade manualmente ──────────────────────────────────────
  const handleUpdate = () => {
    if (!labelSelecionada) return alert("Seleciona um tipo de entidade.");
    if (!pendingSelection) return alert("Seleciona texto na notícia.");

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

  // ── Remover entidade selecionada ─────────────────────────────────────────
  const handleRemover = () => {
    if (!entidadeSelecionada) return alert("Clica numa entidade para a selecionar.");

    const { fraseId, index } = entidadeSelecionada;
    const frase = noticia.frases.find((f) => f.id === fraseId);
    if (!frase) return;

    const novasEntidades = frase.entidades.filter((_, i) => i !== index);
    atualizarFrase(fraseId, novasEntidades);
    setEntidadeSelecionada(null);
  };

  // ── Clicar numa entidade highlighted ────────────────────────────────────
  const handleEntidadeClick = (fraseId, index, entidade) => {
    setEntidadeSelecionada({ fraseId, index, entidade });
    setLabelSelecionada(entidade.tipo);
    setPendingSelection(null);
  };

  return (
    <div className="app">
      <NewsList
        lista={lista}
        noticiaAtiva={noticia}
        onSelecionar={selecionar}
        onAdicionar={adicionarNoticia}
        isLoading={isLoading}
      />

      <main className="main-content">
        <h1>Criminal Entity Correlation</h1>

        <LabelBar
          labels={labels}
          labelSelecionada={labelSelecionada}
          onSelecionar={setLabelSelecionada}
        />

        <ActionBar
          labelSelecionada={labelSelecionada}
          textoSelecionado={pendingSelection?.texto}
          onUpdate={handleUpdate}
          onRemover={handleRemover}
          onGuardar={guardar}
          isLoading={isLoading}
        />

        <ArticleViewer
          noticia={noticia}
          labelMap={labelMap}
          fraseAtiva={fraseAtiva}
          entidadeSelecionada={entidadeSelecionada}
          onFraseClick={carregarGrafo}
          onEntidadeClick={handleEntidadeClick}
          onTextSelect={handleTextSelect}
        />
      </main>

      <GraphPanel
        grafo={grafo}
        labelMap={labelMap}
        isLoading={grafoLoading}
      />
    </div>
  );
}