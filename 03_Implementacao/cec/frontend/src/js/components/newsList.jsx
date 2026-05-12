import React from "react";
import { getHierarquia, getTodasAsPastas, moverNoticia } from "../api/client.jsx";
import "../../static/css/newsList.css";

// ── Handler ────────────────────────────────────────────────────────────────

class NewsListHandler {
  constructor(component) {
    this.component = component;
  }

  async carregarHierarquia() {
    const hierarquia = await getHierarquia();
    const { pastaId } = this.component.props;

    // Expande automaticamente o projeto e pasta actuais
    const projetosExpandidos = new Set();
    const pastasExpandidas = new Set();

    for (const proj of hierarquia) {
      for (const pasta of proj.pastas) {
        if (pasta.id === pastaId) {
          projetosExpandidos.add(proj.id);
          pastasExpandidas.add(pasta.id);
        }
      }
    }

    this.component.setState({ hierarquia, projetosExpandidos, pastasExpandidas });
  }

  toggleProjeto(projetoId) {
    this.component.setState((prev) => {
      const next = new Set(prev.projetosExpandidos);
      next.has(projetoId) ? next.delete(projetoId) : next.add(projetoId);
      return { projetosExpandidos: next };
    });
  }

  togglePasta(pastaId) {
    this.component.setState((prev) => {
      const next = new Set(prev.pastasExpandidas);
      next.has(pastaId) ? next.delete(pastaId) : next.add(pastaId);
      return { pastasExpandidas: next };
    });
  }

  async abrirModalMover() {
    const pastas = await getTodasAsPastas();
    this.component.setState({ todasPastas: pastas, modalMover: true });
  }

  async confirmarMover(pastaDestino) {
    const { noticiaAtiva, onMover } = this.component.props;
    if (!noticiaAtiva) return;
    this.component.setState({ isMovendo: true });
    try {
      await moverNoticia(noticiaAtiva.id, pastaDestino);
      this.component.setState({ modalMover: false });
      await this.carregarHierarquia();
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
    // onAdicionar é assíncrono — aguarda antes de recarregar
    await this.carregarHierarquia();
  }

  lerFicheiro(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result || "");
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file, "utf-8");
    });
  }

  agruparPastasPorProjeto(todasPastas) {
    const grupos = todasPastas.reduce((acc, pasta) => {
      if (!acc[pasta.projeto_nome]) acc[pasta.projeto_nome] = [];
      acc[pasta.projeto_nome].push(pasta);
      return acc;
    }, {});
    return Object.entries(grupos).map(([projectName, folders]) => ({ projectName, folders }));
  }
}

// ── Renderer ───────────────────────────────────────────────────────────────

class NewsListRenderer {
  renderNoticia(noticia, pastaId, projetoId, component) {
    const { noticiaAtiva, onSelecionar, onApagar, onMudarPasta } = component.props;
    const isAtiva = noticiaAtiva?.id === noticia.id;

    const handleSelect = () => {
      if (pastaId !== component.props.pastaId && onMudarPasta) {
        onMudarPasta(projetoId, pastaId);
      }
      onSelecionar(noticia.id);
    };

    return (
      <div key={noticia.id} className="sidebar-noticia-row">
        <button
          className={`sidebar-noticia-btn ${isAtiva ? "active" : ""}`}
          onClick={handleSelect}
          title={noticia.titulo}
        >
          {noticia.titulo}
        </button>
        {isAtiva && (
          <div className="sidebar-noticia-acoes">
            <button
              className="btn-mover-noticia"
              onClick={() => component.handler.abrirModalMover()}
              title="Mover notícia"
            >
              ↗
            </button>
            <button
              className="btn-apagar-noticia"
              onClick={onApagar}
              title="Apagar notícia"
            >
              🗑
            </button>
          </div>
        )}
      </div>
    );
  }

  renderPasta(pasta, projetoId, component) {
    const { pastasExpandidas } = component.state;
    const { pastaId, isLoading } = component.props;
    const expandida = pastasExpandidas.has(pasta.id);
    const eAtual = pasta.id === pastaId;

    return (
      <div key={pasta.id} className="sidebar-pasta">
        <button
          className={`sidebar-pasta-btn ${eAtual ? "pasta-atual" : ""}`}
          onClick={() => component.handler.togglePasta(pasta.id)}
        >
          <span className="sidebar-chevron">{expandida ? "▾" : "▸"}</span>
          <span className="sidebar-pasta-icon">📁</span>
          <span className="sidebar-pasta-nome">{pasta.nome}</span>
          <span className="sidebar-pasta-count">{pasta.noticias.length}</span>
        </button>

        {expandida && (
          <div className="sidebar-pasta-conteudo">
            {pasta.noticias.length === 0 ? (
              <span className="sidebar-vazio">Sem notícias</span>
            ) : (
              pasta.noticias.map((n) => this.renderNoticia(n, pasta.id, projetoId, component))
            )}

            {eAtual && (
              <label className={`upload-btn ${isLoading ? "loading" : ""}`}>
                {isLoading ? "A analisar..." : "+ Adicionar"}
                <input
                  type="file"
                  accept=".txt"
                  multiple
                  className="news-list-file-input"
                  disabled={isLoading}
                  onChange={component.handleFileSelectionChange}
                />
              </label>
            )}
          </div>
        )}
      </div>
    );
  }

  renderProjeto(projeto, component) {
    const { projetosExpandidos } = component.state;
    const expandido = projetosExpandidos.has(projeto.id);

    return (
      <div key={projeto.id} className="sidebar-projeto">
        <button
          className="sidebar-projeto-btn"
          onClick={() => component.handler.toggleProjeto(projeto.id)}
        >
          <span className="sidebar-chevron">{expandido ? "▾" : "▸"}</span>
          <span className="sidebar-projeto-nome">{projeto.nome}</span>
          <span className="sidebar-pasta-count">{projeto.pastas.length}</span>
        </button>

        {expandido && (
          <div className="sidebar-projeto-conteudo">
            {projeto.pastas.length === 0 ? (
              <span className="sidebar-vazio">Sem pastas</span>
            ) : (
              projeto.pastas.map((p) => this.renderPasta(p, projeto.id, component))
            )}
          </div>
        )}
      </div>
    );
  }

  renderMoveModal(component) {
    const { modalMover, todasPastas, isMovendo } = component.state;
    if (!modalMover) return null;

    const grupos = component.handler.agruparPastasPorProjeto(todasPastas);

    return (
      <div className="news-list-modal-overlay" onClick={component.handleCloseMoveModal}>
        <div className="news-list-modal" onClick={(e) => e.stopPropagation()}>
          <h2>Mover notícia</h2>
          <p className="news-list-helper-text">Seleciona a pasta de destino:</p>
          <div className="mover-lista">
            {grupos.map((grupo) => (
              <div key={grupo.projectName} className="mover-grupo">
                <span className="mover-projeto-nome">{grupo.projectName}</span>
                {grupo.folders.map((folder) => (
                  <button
                    key={folder.id}
                    className="mover-pasta-btn"
                    onClick={() => component.handleConfirmarMover(folder.id)}
                    disabled={isMovendo}
                  >
                    📁 {folder.nome}
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div className="news-list-modal-actions">
            <button className="news-list-btn-cancelar" onClick={component.handleCloseMoveModal}>
              Cancelar
            </button>
          </div>
        </div>
      </div>
    );
  }

    render(component) {
      const { hierarquia } = component.state;

      return (
        <aside className="sidebar">
          <div className="sidebar-header">
            <button className="btn-voltar" onClick={() => component.props.onVoltar?.()}>
              ← Dashboard
            </button>
            <span className="sidebar-titulo">Projetos</span>
          </div>

        <div className="sidebar-hierarquia">
          {hierarquia.length === 0 ? (
            <span className="sidebar-vazio">Sem projetos</span>
          ) : (
            hierarquia.map((proj) => this.renderProjeto(proj, component))
          )}
        </div>

        {this.renderMoveModal(component)}
      </aside>
    );
  }
}

// ── Componente principal ───────────────────────────────────────────────────

export default class NewsList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hierarquia: [],
      projetosExpandidos: new Set(),
      pastasExpandidas: new Set(),
      modalMover: false,
      todasPastas: [],
      isMovendo: false,
    };
    this.handler = new NewsListHandler(this);
    this.renderer = new NewsListRenderer();
  }

  componentDidMount() {
    this.handler.carregarHierarquia();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.pastaId !== this.props.pastaId && this.props.pastaId) {
      this.handler.carregarHierarquia();
      return;
    }
    if (prevProps.noticiaCount !== this.props.noticiaCount) {
      this.handler.carregarHierarquia();
    }
  }

  handleCloseMoveModal = () => this.setState({ modalMover: false });

  handleConfirmarMover = async (pastaId) => {
    await this.handler.confirmarMover(pastaId);
  };

  handleFileSelectionChange = async (event) => {
    await this.handler.processarFicheiros(event.target.files);
    event.target.value = "";
  };

  render() {
    return this.renderer.render(this);
  }
}