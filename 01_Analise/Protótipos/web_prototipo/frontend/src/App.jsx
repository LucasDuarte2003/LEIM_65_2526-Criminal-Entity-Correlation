import "./App.css";
import { useState } from "react";
import data from "./data/news.json";

function App() {
  // Estado que guarda a notícia atualmente selecionada.
  // Inicialmente, começa com a primeira notícia do dataset.
  const [selectedNews, setSelectedNews] = useState(data[0]);

  /**
   * Gera uma pré-visualização curta de um texto.
   * Recebe o texto completo de uma notícia e devolve apenas
   * as primeiras 5 palavras seguidas de "..." para mostrar na lista lateral.
   */
  const getPreview = (text) => {
    return text.split(" ").slice(0, 5).join(" ") + "...";
  };

  /**
   * Extrai os tipos de entidades únicos de uma notícia.
   * Recebe a lista de entidades e devolve um array sem repetições
   * (ex: ["PESSOA", "LOCAL", "DATA"]), usado para mostrar os "chips".
   */
  const getUniqueLabels = (entities) => {
    return [...new Set(entities.map((entity) => entity.label))];
  };

/**
 * Constrói o texto da notícia com destaque visual nas entidades.
 *
 * Em vez de confiar diretamente nos índices (start/end), este método
 * utiliza o texto da própria entidade (entity.text) e procura essa
 * ocorrência dentro do texto original.
 *
 * O processo funciona assim:
 * - Ordena as entidades para manter a leitura sequencial
 * - Procura cada entidade no texto a partir da posição atual
 * - Divide o texto em partes:
 *    • texto normal
 *    • entidades destacadas com classes CSS
 *
 * Isto torna o método mais robusto quando os índices do dataset
 * não estão perfeitamente alinhados com o texto.
 *
 * No final devolve um array de elementos React (<span>) que,
 * combinados, formam o texto completo com highlights.
 */
const renderHighlightedText = (text, entities) => {
  const parts = [];
  let currentIndex = 0;

  // Ordena entidades pela posição start
  const sortedEntities = [...entities].sort((a, b) => a.start - b.start);

  sortedEntities.forEach((entity, index) => {
    const entityText = entity.text?.trim();

    // Ignora entidades sem texto
    if (!entityText) return;

    // Procura a entidade no texto a partir da posição atual
    const foundIndex = text.indexOf(entityText, currentIndex);

    // Se não encontrar, ignora
    if (foundIndex === -1) return;

    // Adiciona texto normal antes da entidade
    if (currentIndex < foundIndex) {
      parts.push(
        <span key={`text-${index}`}>
          {text.slice(currentIndex, foundIndex)}
        </span>
      );
    }

    // Adiciona entidade destacada
    parts.push(
      <span
        key={`entity-${index}`}
        className={`highlight ${entity.label.toLowerCase()}`}
        title={entity.label}
      >
        {entityText}
      </span>
    );

    // Atualiza posição atual
    currentIndex = foundIndex + entityText.length;
  });

  // Adiciona o resto do texto
  if (currentIndex < text.length) {
    parts.push(
      <span key="text-final">
        {text.slice(currentIndex)}
      </span>
    );
  }

  return parts;
};

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Notícias</h2>

        <div className="news-list">
          {data.map((item) => (
            <button
              key={item.id}
              className={`news-item ${
                selectedNews.id === item.id ? "active" : ""
              }`}
              onClick={() => setSelectedNews(item)}
            >
              {getPreview(item.text)}
            </button>
          ))}
        </div>
      </aside>

      <main className="main-content">
        <h1>Criminal Entity Correlation</h1>

        <div className="labels-bar">
          {getUniqueLabels(selectedNews.entities).map((label) => (
            <span key={label} className={`label-chip ${label.toLowerCase()}`}>
              {label}
            </span>
          ))}
        </div>

        <div className="news-full">
          <p>{renderHighlightedText(selectedNews.text, selectedNews.entities)}</p>
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