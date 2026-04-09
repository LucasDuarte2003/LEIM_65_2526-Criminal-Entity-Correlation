import React from "react";

export default function NewsList({ lista, noticiaAtiva, onSelecionar, onAdicionar, isLoading }) {
  return (
    <aside className="sidebar">
      <h2>Notícias</h2>
      <label className={`upload-btn ${isLoading ? "loading" : ""}`}>
        {isLoading ? "A analisar..." : "+ Adicionar notícia"}
        <input
          type="file"
          accept=".txt"
          style={{ display: "none" }}
          disabled={isLoading}
          onChange={(e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => onAdicionar(ev.target.result);
            reader.readAsText(file, "utf-8");
            e.target.value = "";
          }}
        />
      </label>

      <div className="news-list">
        {lista.map((item) => (
          <button
            key={item.id}
            className={`news-item ${noticiaAtiva?.id === item.id ? "active" : ""}`}
            onClick={() => onSelecionar(item.id)}
          >
            {item.titulo}
          </button>
        ))}
      </div>
    </aside>
  );
}