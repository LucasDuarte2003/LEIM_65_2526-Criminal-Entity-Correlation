import React, { useRef } from "react";

export default function ArticleViewer({
  noticia,
  labelMap,
  fraseAtiva,
  entidadeSelecionada,
  onFraseClick,
  onEntidadeClick,
  onTextSelect,
}) {
  const refs = useRef({});

  if (!noticia) {
    return <div className="news-full placeholder">Seleciona uma notícia ou adiciona uma nova.</div>;
  }

  return (
    <div className="news-full">
      {noticia.frases.map((frase) => (
        <span
          key={frase.id}
          className={`frase ${fraseAtiva === frase.id ? "frase-ativa" : ""}`}
          ref={(el) => (refs.current[frase.id] = el)}
          onMouseUp={(e) => {
            onTextSelect(e, frase);
          }}
        >
          {/* Botão para ver o grafo desta frase */}
          <button
            className="frase-grafo-btn"
            title="Ver grafo desta frase"
            onClick={() => onFraseClick(frase.id)}
          >
            ◉
          </button>

          {/* Texto da frase com entidades destacadas */}
          {renderFrase(frase, labelMap, entidadeSelecionada, onEntidadeClick)}

          {" "}
        </span>
      ))}
    </div>
  );
}

function calcularOffsets(texto, ent) {
  // Usa o nome da entidade para verificar se os offsets estão corretos.
  // Se o slice não bater certo, procura o nome no texto a partir do inicio.
  const slice = texto.slice(ent.inicio, ent.fim);
  if (slice === ent.nome) return { inicio: ent.inicio, fim: ent.fim };

  // Offset desalinhado — procura o nome a partir de uma janela à volta do inicio
  const searchFrom = Math.max(0, ent.inicio - 3);
  const found = texto.indexOf(ent.nome, searchFrom);
  if (found !== -1) return { inicio: found, fim: found + ent.nome.length };

  // Fallback — usa os offsets originais mesmo que errados
  return { inicio: ent.inicio, fim: ent.fim };
}

function renderFrase(frase, labelMap, entidadeSelecionada, onEntidadeClick) {
  const texto = frase.texto;

  // Corrige offsets e reordena
  const entidades = [...frase.entidades]
    .map((ent) => ({ ...ent, ...calcularOffsets(texto, ent) }))
    .sort((a, b) => a.inicio - b.inicio);

  const parts = [];
  let cursor = 0;

  entidades.forEach((ent, idx) => {
    if (ent.inicio < cursor) return; // sobreposição, ignora

    if (cursor < ent.inicio) {
      parts.push(
        <span key={`t-${frase.id}-${idx}`}>
          {texto.slice(cursor, ent.inicio)}
        </span>
      );
    }

    const cor = labelMap[ent.tipo] || "#ccc";
    const isSelected =
      entidadeSelecionada?.fraseId === frase.id &&
      entidadeSelecionada?.index === idx;

    parts.push(
      <mark
        key={`e-${frase.id}-${idx}`}
        className={`entidade ${isSelected ? "entidade-selecionada" : ""}`}
        style={{
          backgroundColor: cor + "28",
          borderBottom: `2px solid ${cor}`,
          color: "var(--text)",
        }}
        title={ent.tipo}
        onClick={() => onEntidadeClick(frase.id, idx, ent)}
      >
        {texto.slice(ent.inicio, ent.fim)}
      </mark>
    );

    cursor = ent.fim;
  });

  if (cursor < texto.length) {
    parts.push(
      <span key={`t-${frase.id}-final`}>{texto.slice(cursor)}</span>
    );
  }

  return parts;
}