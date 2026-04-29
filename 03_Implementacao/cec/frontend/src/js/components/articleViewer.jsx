import React from "react";
import "../../static/css/articleViewer.css";

const PLACEHOLDER_MESSAGE = "Seleciona uma notícia ou adiciona uma nova.";

class ArticleViewerHandler {
  constructor({ labelMap, entidadeSelecionada, onEntidadeClick }) {
    this.labelMap = labelMap;
    this.entidadeSelecionada = entidadeSelecionada;
    this.onEntidadeClick = onEntidadeClick;
  }

  buildViewModel({ noticia, fraseAtiva, fraseFundida, onFraseClick, onFraseFundir, onTextSelect }) {
    return {
      hasNoticia: Boolean(noticia),
      placeholderMessage: PLACEHOLDER_MESSAGE,
      phraseViewModels: noticia ? noticia.frases.map((frase) => this.createPhraseViewModel(frase, fraseAtiva, fraseFundida)) : [],
      handleTextSelect: onTextSelect,
      handlePhraseClick: onFraseClick,
      handlePhraseMerge: onFraseFundir,
    };
  }

  createPhraseViewModel(frase, fraseAtiva, fraseFundida) {
    const isAtiva = fraseAtiva === frase.id;
    const isFundida = fraseFundida === frase.id;

    return {
      id: frase.id,
      rawFrase: frase,
      className: `frase ${isAtiva ? "frase-ativa" : ""} ${isFundida ? "frase-fundida" : ""}`,
      canMerge: Boolean(fraseAtiva) && !isAtiva,
      mergeButtonClassName: `frase-fundir-btn ${isFundida ? "ativa" : ""}`,
      mergeButtonTitle: isFundida ? "Desfazer fusão" : "Fundir com frase ativa",
      segments: this.createSegments(frase),
    };
  }

  createSegments(frase) {
    const normalizedEntities = this.createNormalizedEntities(frase);
    const segments = [];
    let cursor = 0;

    normalizedEntities.forEach((entity, index) => {
      if (entity.inicio < cursor) return;
      this.pushTextSegment(segments, frase, cursor, entity.inicio, index);
      segments.push(this.createEntitySegment(frase, entity, index));
      cursor = entity.fim;
    });

    this.pushFinalTextSegment(segments, frase, cursor);
    return segments;
  }

  createNormalizedEntities(frase) {
    return [...frase.entidades]
      .map((entidade) => ({ ...entidade, ...this.resolveOffsets(frase.texto, entidade) }))
      .sort((firstEntity, secondEntity) => firstEntity.inicio - secondEntity.inicio);
  }

  resolveOffsets(texto, entidade) {
    const currentSlice = texto.slice(entidade.inicio, entidade.fim);
    if (currentSlice === entidade.nome) return { inicio: entidade.inicio, fim: entidade.fim };

    const searchStartIndex = Math.max(0, entidade.inicio - 3);
    const foundIndex = texto.indexOf(entidade.nome, searchStartIndex);
    if (foundIndex !== -1) return { inicio: foundIndex, fim: foundIndex + entidade.nome.length };

    return { inicio: entidade.inicio, fim: entidade.fim };
  }

  pushTextSegment(segments, frase, startIndex, endIndex, index) {
    if (startIndex >= endIndex) return;

    segments.push({
      key: `t-${frase.id}-${index}`,
      type: "text",
      text: frase.texto.slice(startIndex, endIndex),
    });
  }

  pushFinalTextSegment(segments, frase, cursor) {
    if (cursor >= frase.texto.length) return;

    segments.push({
      key: `t-${frase.id}-final`,
      type: "text",
      text: frase.texto.slice(cursor),
    });
  }

  createEntitySegment(frase, entidade, index) {
    const isSelected = this.isSelectedEntity(frase.id, index);
    const entityTypeClassName = this.getEntityTypeClassName(entidade.tipo);

    return {
      key: `e-${frase.id}-${index}`,
      type: "entity",
      text: frase.texto.slice(entidade.inicio, entidade.fim),
      title: entidade.tipo,
      className: `entidade ${entityTypeClassName} ${isSelected ? "entidade-selecionada" : ""}`,
      onClick: () => this.onEntidadeClick(frase.id, index, entidade),
    };
  }

  isSelectedEntity(fraseId, entityIndex) {
    return this.entidadeSelecionada?.fraseId === fraseId && this.entidadeSelecionada?.index === entityIndex;
  }

  getEntityTypeClassName(entityType) {
    const normalizedType = entityType.toLowerCase();
    const knownTypes = [
      "pessoa",
      "local",
      "organizacao",
      "crime",
      "data",
      "viatura",
      "matricula",
      "telemovel",
      "email",
      "cripto",
      "montante",
    ];

    return knownTypes.includes(normalizedType) ? `entidade--${normalizedType}` : "entidade--default";
  }
}

class ArticleViewerRenderer {
  renderPlaceholder(message) {
    return <div className="news-full placeholder">{message}</div>;
  }

  renderSegments(segments) {
    return segments.map((segment) => this.renderSegment(segment));
  }

  renderSegment(segment) {
    if (segment.type === "text") return <span key={segment.key}>{segment.text}</span>;

    return (
      <mark key={segment.key} className={segment.className} title={segment.title} onClick={segment.onClick}>
        {segment.text}
      </mark>
    );
  }

  renderPhrase(phrase, viewModel) {
    return (
      <span key={phrase.id} className={phrase.className} onMouseUp={(event) => viewModel.handleTextSelect(event, phrase.rawFrase)}>
        <button className="frase-grafo-btn" title="Ver grafo desta frase" onClick={() => viewModel.handlePhraseClick(phrase.id)}>
          ◉
        </button>

        {phrase.canMerge && (
          <button className={phrase.mergeButtonClassName} title={phrase.mergeButtonTitle} onClick={() => viewModel.handlePhraseMerge(phrase.id)}>
            ⊕
          </button>
        )}

        {this.renderSegments(phrase.segments)} {" "}
      </span>
    );
  }

  renderContent(viewModel) {
    return <div className="news-full">{viewModel.phraseViewModels.map((phrase) => this.renderPhrase(phrase, viewModel))}</div>;
  }
}

export default class ArticleViewer extends React.Component {
  constructor(props) {
    super(props);
    this.renderer = new ArticleViewerRenderer();
  }

  createHandler() {
    return new ArticleViewerHandler({
      labelMap: this.props.labelMap,
      entidadeSelecionada: this.props.entidadeSelecionada,
      onEntidadeClick: this.props.onEntidadeClick,
    });
  }

  render() {
    const handler = this.createHandler();
    const viewModel = handler.buildViewModel(this.props);

    if (!viewModel.hasNoticia) return this.renderer.renderPlaceholder(viewModel.placeholderMessage);
    return this.renderer.renderContent(viewModel);
  }
}