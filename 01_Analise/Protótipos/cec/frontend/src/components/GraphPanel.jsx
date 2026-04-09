import React, { useCallback, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

export default function GraphPanel({ grafo, labelMap, isLoading }) {
  const [nosRemovidosIds, setNosRemovidosIds] = useState([]);

  // Filtra nós e arestas removidos
  const nosVisiveis = grafo
    ? grafo.nos.filter((n) => !nosRemovidosIds.includes(n.id))
    : [];

  const arestasVisiveis = grafo
    ? grafo.arestas.filter(
        (a) => !nosRemovidosIds.includes(a.origem) && !nosRemovidosIds.includes(a.destino)
      )
    : [];

  const graphData = {
    nodes: nosVisiveis.map((n) => ({
      id: n.id,
      name: n.nome,
      tipo: n.tipo,
      color: labelMap[n.tipo] || "#aaa",
    })),
    links: arestasVisiveis.map((a) => ({
      source: a.origem,
      target: a.destino,
    })),
  };

  const handleNodeClick = useCallback((node) => {
    setNosRemovidosIds((prev) => [...prev, node.id]);
  }, []);

  const handleReset = () => setNosRemovidosIds([]);

  return (
    <aside className="right-panel">
      <div className="panel-header">
        <h2>Grafo</h2>
        {grafo && nosRemovidosIds.length > 0 && (
          <button className="btn-reset" onClick={handleReset}>
            Repor
          </button>
        )}
      </div>

      {isLoading && <p className="panel-msg">A carregar grafo...</p>}

      {!isLoading && !grafo && (
        <p className="panel-msg">
          Clica em <strong>◉</strong> numa frase para ver as relações.
        </p>
      )}

      {!isLoading && grafo && graphData.nodes.length === 0 && (
        <p className="panel-msg">Esta frase não tem entidades relacionadas.</p>
      )}

      {!isLoading && grafo && graphData.nodes.length > 0 && (
        <>
          <p className="panel-hint">Clica num nó para o remover.</p>
          <ForceGraph2D
            graphData={graphData}
            width={280}
            height={400}
            nodeLabel={(n) => `${n.name} (${n.tipo})`}
            nodeColor={(n) => n.color}
            nodeRelSize={6}
            linkColor={() => "#555"}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.fillStyle = node.color;
              ctx.beginPath();
              ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
              ctx.fill();
              ctx.fillStyle = "#fff";
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillText(
                label.length > 12 ? label.slice(0, 12) + "…" : label,
                node.x,
                node.y + 14
              );
            }}
            onNodeClick={handleNodeClick}
          />
        </>
      )}
    </aside>
  );
}