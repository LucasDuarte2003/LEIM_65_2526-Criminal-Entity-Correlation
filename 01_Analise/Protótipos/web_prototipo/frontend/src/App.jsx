import "./App.css";
import { useMemo, useRef, useState } from "react";
import data from "./data/news.json";

// Lista global de labels possíveis.
// Aqui vamos buscar todas as labels existentes no dataset
// para poderes sempre escolhê-las no topo.
const ALL_LABELS = [...new Set(data.flatMap((news) =>
  news.entities.map((entity) => entity.label)
))];

function App() {
  // Guarda todas as notícias num estado editável.
  // Isto permite alterar entidades no frontend sem mexer diretamente no import original.
  const [newsList, setNewsList] = useState(data);

  // Guarda o id da notícia selecionada.
  const [selectedNewsId, setSelectedNewsId] = useState(data[0]?.id);

  // Guarda a label atualmente escolhida pelo utilizador.
  // Exemplo: "PESSOA", "LOCAL", etc.
  const [selectedLabel, setSelectedLabel] = useState(null);

  // Guarda a entidade clicada atualmente, caso queiras realçá-la visualmente.
  const [selectedEntityIndex, setSelectedEntityIndex] = useState(null);

  // Guarda a seleção de texto feita pelo utilizador dentro da notícia.
  // Exemplo: { start: 120, end: 145, text: "John Smith" }
  const [pendingSelection, setPendingSelection] = useState(null);

  // Referência para o bloco onde o texto completo da notícia é renderizado.
  // É usada para calcular corretamente os offsets do texto selecionado.
  const articleRef = useRef(null);

  // Obtém a notícia atualmente selecionada a partir do id guardado no estado.
  const selectedNews = useMemo(() => {
    return newsList.find((item) => item.id === selectedNewsId);
  }, [newsList, selectedNewsId]);

  /**
   * Gera uma pré-visualização curta para a barra lateral.
   * Mostra apenas as primeiras 5 palavras da notícia.
   */
  const getPreview = (text) => {
    return text.split(" ").slice(0, 5).join(" ") + "...";
  };

  /**
   * Extrai as labels únicas presentes numa notícia.
   * Pode ser útil para análises futuras, embora aqui estejamos a mostrar ALL_LABELS.
   */
  const getUniqueLabels = (entities) => {
    return [...new Set(entities.map((entity) => entity.label))];
  };

  /**
   * Constrói o texto da notícia com destaque visual nas entidades.
   *
   * Em vez de depender totalmente dos índices start/end, este método
   * procura o texto de cada entidade (`entity.text`) dentro do texto completo.
   * Isto ajuda quando alguns índices do dataset não estão perfeitamente alinhados.
   *
   * Além disso, cada entidade destacada passa a ser clicável, para que
   * o utilizador a possa selecionar.
   */
  const renderHighlightedText = (text, entities) => {
    const parts = [];
    let currentIndex = 0;

    const sortedEntities = [...entities].sort((a, b) => a.start - b.start);

    sortedEntities.forEach((entity, index) => {
      const entityText = entity.text?.trim();

      if (!entityText) return;

      const foundIndex = text.indexOf(entityText, currentIndex);

      if (foundIndex === -1) return;

      if (currentIndex < foundIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {text.slice(currentIndex, foundIndex)}
          </span>
        );
      }

      parts.push(
        <span
          key={`entity-${index}`}
          className={`highlight ${entity.label.toLowerCase()} ${
            selectedEntityIndex === index ? "selected-entity" : ""
          }`}
          title={entity.label}
          onClick={() => {
            setSelectedLabel(entity.label);
            setSelectedEntityIndex(index);
          }}
        >
          {entityText}
        </span>
      );

      currentIndex = foundIndex + entityText.length;
    });

    if (currentIndex < text.length) {
      parts.push(
        <span key="text-final">
          {text.slice(currentIndex)}
        </span>
      );
    }

    return parts;
  };

  /**
   * Calcula a posição real (start/end) da seleção de texto feita pelo utilizador
   * dentro do bloco da notícia.
   *
   * Isto é necessário porque, quando o texto tem vários <span>,
   * não basta usar apenas o texto selecionado: precisamos também dos offsets
   * para criar uma nova entidade corretamente.
   */
  const getSelectionOffsets = () => {
    const selection = window.getSelection();

    if (!selection || selection.rangeCount === 0) return null;

    const range = selection.getRangeAt(0);

    // Ignora seleções vazias
    if (range.collapsed) return null;

    // Garante que a seleção foi feita dentro da notícia
    if (!articleRef.current || !articleRef.current.contains(range.commonAncestorContainer)) {
      return null;
    }

    const rawSelectedText = selection.toString();
    if (!rawSelectedText.trim()) return null;

    // Cria um range desde o início do texto até ao início da seleção
    const preRange = range.cloneRange();
    preRange.selectNodeContents(articleRef.current);
    preRange.setEnd(range.startContainer, range.startOffset);

    let start = preRange.toString().length;
    let end = start + rawSelectedText.length;

    // Remove espaços no início/fim da seleção para a entidade ficar limpa
    const trimmedText = rawSelectedText.trim();
    const leadingSpaces = rawSelectedText.length - rawSelectedText.trimStart().length;
    const trailingSpaces = rawSelectedText.length - rawSelectedText.trimEnd().length;

    start += leadingSpaces;
    end -= trailingSpaces;

    return {
      start,
      end,
      text: trimmedText,
    };
  };

  /**
   * É chamado quando o utilizador acaba de selecionar texto na notícia.
   * Guarda temporariamente essa seleção para depois ser usada no botão UPDATE.
   */
  const handleTextMouseUp = () => {
    const selectionData = getSelectionOffsets();
    setPendingSelection(selectionData);
  };

  /**
   * Verifica se a nova entidade entra em conflito com entidades já existentes.
   * Aqui consideramos conflito quando os intervalos se sobrepõem.
   */
  const hasOverlap = (newStart, newEnd, entities) => {
    return entities.some((entity) => {
      return newStart < entity.end && newEnd > entity.start;
    });
  };

  /**
   * Adiciona uma nova entidade à notícia selecionada com base:
   * - na label escolhida no topo
   * - no texto atualmente selecionado pelo utilizador
   *
   * Este método atualiza o frontend imediatamente.
   */
  const handleUpdate = () => {
    if (!selectedNews) return;

    if (!selectedLabel) {
      alert("Primeiro tens de selecionar o tipo de entidade.");
      return;
    }

    if (!pendingSelection) {
      alert("Primeiro tens de selecionar uma parte do texto.");
      return;
    }

    const { start, end, text } = pendingSelection;

    if (hasOverlap(start, end, selectedNews.entities)) {
      alert("A seleção escolhida sobrepõe-se a uma entidade já existente.");
      return;
    }

    const newEntity = {
      start,
      end,
      text,
      label: selectedLabel,
    };

    const updatedNewsList = newsList.map((news) => {
      if (news.id !== selectedNews.id) return news;

      return {
        ...news,
        entities: [...news.entities, newEntity].sort((a, b) => a.start - b.start),
      };
    });

    setNewsList(updatedNewsList);
    setPendingSelection(null);
    setSelectedEntityIndex(null);

    // Limpa a seleção visível do browser
    window.getSelection()?.removeAllRanges();
  };

  /**
   * Remove a entidade atualmente selecionada.
   * Isto é útil porque, ao editar anotações, também vais precisar de apagar.
   */
  const handleRemoveSelectedEntity = () => {
    if (selectedEntityIndex === null || !selectedNews) return;

    const updatedNewsList = newsList.map((news) => {
      if (news.id !== selectedNews.id) return news;

      return {
        ...news,
        entities: news.entities.filter((_, index) => index !== selectedEntityIndex),
      };
    });

    setNewsList(updatedNewsList);
    setSelectedEntityIndex(null);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Notícias</h2>

        <div className="news-list">
          {newsList.map((item) => (
            <button
              key={item.id}
              className={`news-item ${selectedNews?.id === item.id ? "active" : ""}`}
              onClick={() => {
                setSelectedNewsId(item.id);
                setPendingSelection(null);
                setSelectedEntityIndex(null);
              }}
            >
              {getPreview(item.text)}
            </button>
          ))}
        </div>
      </aside>

      <main className="main-content">
        <h1>Criminal Entity Correlation</h1>

        <div className="labels-bar">
          {ALL_LABELS.map((label) => (
            <button
              key={label}
              className={`label-chip ${label.toLowerCase()} ${
                selectedLabel === label ? "active-chip" : ""
              }`}
              onClick={() => setSelectedLabel(label)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="action-bar">
          <p>
            <strong>Tipo selecionado:</strong>{" "}
            {selectedLabel || "nenhum"}
          </p>

          <p>
            <strong>Texto selecionado:</strong>{" "}
            {pendingSelection ? `"${pendingSelection.text}"` : "nenhum"}
          </p>

          <button onClick={handleUpdate}>UPDATE</button>
          <button onClick={handleRemoveSelectedEntity}>REMOVER ENTIDADE</button>
        </div>

        <div
          className="news-full"
          ref={articleRef}
          onMouseUp={handleTextMouseUp}
        >
          <p>{selectedNews && renderHighlightedText(selectedNews.text, selectedNews.entities)}</p>
        </div>
      </main>

      <aside className="right-panel">
        <h2>Neo4j</h2>
        <div className="neo4j-placeholder">
          Área reservada para o grafo e correlações.
        </div>
      </aside>
    </div>
  );
}

export default App;