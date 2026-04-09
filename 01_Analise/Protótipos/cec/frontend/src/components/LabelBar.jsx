import React from "react";

export default function LabelBar({ labels, labelSelecionada, onSelecionar }) {
  if (!labels.length) return null;

  return (
    <div className="labels-bar">
      {labels.map((label) => (
        <button
          key={label.nome}
          className={`label-chip ${labelSelecionada === label.nome ? "active-chip" : ""}`}
          style={{ backgroundColor: label.cor, opacity: labelSelecionada === label.nome ? 1 : 0.55 }}
          onClick={() => onSelecionar(labelSelecionada === label.nome ? null : label.nome)}
        >
          {label.nome}
        </button>
      ))}
    </div>
  );
}