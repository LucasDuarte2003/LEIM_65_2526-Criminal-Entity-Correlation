import React from "react";
import { getTodasAsPastas, moverNoticia } from "../api/client.jsx";
import "../../static/css/newsList.css";

class NewsListHandler {
  constructor(component) {
    this.component = component;
  }

  async abrirModalMover() {
    const pastas = await getTodasAsPastas();
    this.component.setState({ todasPastas: pastas, modalMover: true });
  }

  async confirmarMover(pastaId) {
    const { noticiaAtiva, onMover } = this.component.props;
    if (!noticiaAtiva) return;

    this.component.setState({ isMovendo: true });
    try {
      await moverNoticia(noticiaAtiva.id, pastaId);
      this.component.setState({ modalMover: false });
      if (onMover) onMover(noticiaAtiva.id);
    } catch {
      alert("Erro ao mover a notícia.");
    } finally {
      this.component.setState({ isMovendo: false });
    }
  }

  async processarFicheiros(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;

    for (const file of files) {
      const content = await this.lerFicheiro(file);
      await this.component.props.onAdicionar(content);
    }
  }

  lerFicheiro(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (event) => resolve(event.target?.result || "");
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file, "utf-8");
    });
  }

  agruparPastasPorProjeto(todasPastas) {
    const groupedFolders = todasPastas.reduce((accumulator, pasta) => {
      if (!accumulator[pasta.projeto_nome]) accumulator[pasta.projeto_nome] = [];
      accumulator[pasta.projeto_nome].push(pasta);
      return accumulator;
    }, {});

    return Object.entries(groupedFolders).map(([projectName, folders]) => ({
      projectName,
      folders,
    }));
  }

  buildNewsItemViewModel(item) {
    const { noticiaAtiva, onSelecionar, onApagar } = this.component.props;
    const isActive = noticiaAtiva?.id === item.id;

    return {
      id: item.id,
      title: item.titulo,
      className: `news-item ${isActive ? "active" : ""}`,
      isActive,
      onSelect: () => onSelecionar(item.id),
      onMove: () => this.abrirModalMover(),
      onDelete: onApagar,
    };
  }

  buildViewModel() {
    const { lista, onVoltar, isLoading } = this.component.props;
    const { modalMover, todasPastas, isMovendo } = this.component.state;

    return {
      uploadButtonClassName: `upload-btn ${isLoading ? "loading" : ""}`,
      uploadButtonLabel: isLoading ? "A analisar..." : "+ Adicionar notícia",
      isUploadDisabled: isLoading,
      newsItems: lista.map((item) => this.buildNewsItemViewModel(item)),
      isMoveModalVisible: modalMover,
      moveGroups: this.agruparPastasPorProjeto(todasPastas),
      isMovendo,
      onVoltar,
    };
  }
}

class NewsListRenderer {
  renderNewsItem(item) {
    return (
      <div key={item.id} className="news-item-row">
        <button className={item.className} onClick={item.onSelect}>
          {item.title}
        </button>
        {item.isActive && (
          <>
            <button className="btn-mover-noticia" onClick={item.onMove} title="Mover notícia">
              ↗
            </button>
            <button className="btn-apagar-noticia" onClick={item.onDelete} title="Apagar notícia">
              🗑
            </button>
          </>
        )}
      </div>
    );
  }

  renderMoveGroups(viewModel, component) {
    return viewModel.moveGroups.map((group) => (
      <div key={group.projectName} className="mover-grupo">
        <span className="mover-projeto-nome">{group.projectName}</span>
        {group.folders.map((folder) => (
          <button
            key={folder.id}
            className="mover-pasta-btn"
            onClick={() => component.handleConfirmarMover(folder.id)}
            disabled={viewModel.isMovendo}
          >
            📁 {folder.nome}
          </button>
        ))}
      </div>
    ));
  }

  renderMoveModal(viewModel, component) {
    if (!viewModel.isMoveModalVisible) return null;

    return (
      <div className="news-list-modal-overlay" onClick={component.handleCloseMoveModal}>
        <div className="news-list-modal" onClick={component.handleModalContentClick}>
          <h2>Mover notícia</h2>
          <p className="news-list-helper-text">Seleciona a pasta de destino:</p>
          <div className="mover-lista">{this.renderMoveGroups(viewModel, component)}</div>
          <div className="news-list-modal-actions">
            <button className="news-list-btn-cancelar" onClick={component.handleCloseMoveModal}>
              Cancelar
            </button>
          </div>
        </div>
      </div>
    );
  }

  render(viewModel, component) {
    return (
      <aside className="sidebar">
        <button className="btn-voltar" onClick={viewModel.onVoltar}>← Projetos</button>
        <h2>Notícias</h2>

        <label className={viewModel.uploadButtonClassName}>
          {viewModel.uploadButtonLabel}
          <input
            type="file"
            accept=".txt"
            multiple
            className="news-list-file-input"
            disabled={viewModel.isUploadDisabled}
            onChange={component.handleFileSelectionChange}
          />
        </label>

        <div className="news-list">{viewModel.newsItems.map((item) => this.renderNewsItem(item))}</div>

        {this.renderMoveModal(viewModel, component)}
      </aside>
    );
  }
}

export default class NewsList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      modalMover: false,
      todasPastas: [],
      isMovendo: false,
    };
    this.handler = new NewsListHandler(this);
    this.renderer = new NewsListRenderer();
  }

  handleCloseMoveModal = () => {
    this.setState({ modalMover: false });
  };

  handleModalContentClick = (event) => {
    event.stopPropagation();
  };

  handleConfirmarMover = async (pastaId) => {
    await this.handler.confirmarMover(pastaId);
  };

  handleFileSelectionChange = async (event) => {
    await this.handler.processarFicheiros(event.target.files);
    event.target.value = "";
  };

  render() {
    const viewModel = this.handler.buildViewModel();
    return this.renderer.render(viewModel, this);
  }
}
