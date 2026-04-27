import React, { useState, useEffect } from "react";
import { getTodasAsPastas, moverNoticia } from "../api/client";

export default function NewsList({
  lista, noticiaAtiva, onSelecionar,
  onAdicionar, onApagar, onVoltar, onMover, isLoading,
}) {
  const [modalMover, setModalMover] = useState(false);
  const [todasPastas, setTodasPastas] = useState([]);
  const [isMovendo, setIsMovendo] = useState(false);

  const abrirModalMover = async () => {
    const pastas = await getTodasAsPastas();
    setTodasPastas(pastas);
    setModalMover(true);
  };

    const confirmarMover = async (pastaId) => {
      if (!noticiaAtiva) return;
      setIsMovendo(true);
      try {
        await moverNoticia(noticiaAtiva.id, pastaId);
        setModalMover(false);
        if (onMover) onMover(noticiaAtiva.id);
      } catch (e) {
        alert("Erro ao mover a notícia.");
      } finally {
        setIsMovendo(false);
      }
    };

  // Agrupa pastas por projeto para mostrar no modal
  const pastasPorProjeto = todasPastas.reduce((acc, pasta) => {
    if (!acc[pasta.projeto_nome]) acc[pasta.projeto_nome] = [];
    acc[pasta.projeto_nome].push(pasta);
    return acc;
  }, {});

  return (
    <aside className="sidebar">
      <button className="btn-voltar" onClick={onVoltar}>← Projetos</button>
      <h2>Notícias</h2>

      <label className={`upload-btn ${isLoading ? "loading" : ""}`}>
        {isLoading ? "A analisar..." : "+ Adicionar notícia"}
        <input
          type="file"
          accept=".txt"
          multiple
          style={{ display: "none" }}
          disabled={isLoading}
          onChange={(e) => {
            const files = Array.from(e.target.files);
            if (!files.length) return;
            files.reduce((promise, file) => {
              return promise.then(() => new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (ev) => { onAdicionar(ev.target.result); resolve(); };
                reader.readAsText(file, "utf-8");
              }));
            }, Promise.resolve());
            e.target.value = "";
          }}
        />
      </label>

      <div className="news-list">
        {lista.map((item) => (
          <div key={item.id} className="news-item-row">
            <button
              className={`news-item ${noticiaAtiva?.id === item.id ? "active" : ""}`}
              onClick={() => onSelecionar(item.id)}
            >
              {item.titulo}
            </button>
            {noticiaAtiva?.id === item.id && (
              <>
                <button
                  className="btn-mover-noticia"
                  onClick={abrirModalMover}
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
              </>
            )}
          </div>
        ))}
      </div>

      {/* Modal de mover */}
      {modalMover && (
        <div className="modal-overlay" onClick={() => setModalMover(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Mover notícia</h2>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px" }}>
              Seleciona a pasta de destino:
            </p>
            <div className="mover-lista">
              {Object.entries(pastasPorProjeto).map(([projetoNome, pastas]) => (
                <div key={projetoNome} className="mover-grupo">
                  <span className="mover-projeto-nome">{projetoNome}</span>
                  {pastas.map((pasta) => (
                    <button
                      key={pasta.id}
                      className="mover-pasta-btn"
                      onClick={() => confirmarMover(pasta.id)}
                      disabled={isMovendo}
                    >
                      📁 {pasta.nome}
                    </button>
                  ))}
                </div>
              ))}
            </div>
            <div className="modal-actions">
              <button className="btn-cancelar" onClick={() => setModalMover(false)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}