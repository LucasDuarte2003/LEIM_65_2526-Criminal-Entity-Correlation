import React from "react";

export default function ActionBar({
  labelSelecionada,
  textoSelecionado,
  onUpdate,
  onRemover,
  onGuardar,
  isLoading,
}) {
  return (
    <div className="action-bar">
      <div className="action-info">
        <span>
          <strong>Tipo:</strong> {labelSelecionada || "nenhum"}
        </span>
        <span>
          <strong>Seleção:</strong>{" "}
          {textoSelecionado ? `"${textoSelecionado}"` : "nenhuma"}
        </span>
      </div>

      <div className="action-buttons">
        <button className="btn btn-update" onClick={onUpdate}>
          Adicionar entidade
        </button>
        <button className="btn btn-remove" onClick={onRemover}>
          Remover entidade
        </button>
        <button className="btn btn-save" onClick={onGuardar} disabled={isLoading}>
          {isLoading ? "A guardar..." : "Guardar"}
        </button>
      </div>
    </div>
  );
}