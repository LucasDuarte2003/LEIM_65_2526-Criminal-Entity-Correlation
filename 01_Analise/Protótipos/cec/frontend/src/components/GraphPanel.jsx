import React, {useCallback, useState} from "react";
import ForceGraph2D from "react-force-graph-2d";

export default function GraphPanel({
                                       grafo,
                                       grafoRelacionadas,
                                       labelMap,
                                       isLoading,
                                       isLoadingRelacionadas,
                                       onPesquisarRelacionadas,
                                   }) {
    const [nosRemovidosIds, setNosRemovidosIds] = useState([]);

    const [expandedGraph, setExpandedGraph] = useState(null);
    // Valores possíveis: null | "principal" | "relacionadas"

    const openExpanded = (type) => setExpandedGraph(type);
    const closeExpanded = () => setExpandedGraph(null);


    const nosVisiveis = grafo
        ? grafo.nos.filter((n) => !nosRemovidosIds.includes(n.id))
        : [];

    const arestasVisiveis = grafo
        ? grafo.arestas.filter(
            (a) =>
                !nosRemovidosIds.includes(a.origem) &&
                !nosRemovidosIds.includes(a.destino)
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

    const graphRelacionadasData = grafoRelacionadas
        ? {
            nodes: [
                ...nosVisiveis.map((n) => ({
                    id: n.nome,
                    name: n.nome,
                    tipo: n.tipo,
                    color: labelMap[n.tipo] || "#aaa",
                    origem: true,
                })),
                ...grafoRelacionadas.nos
                    .filter((n) => !n.origem)
                    .map((n) => ({
                        id: n.id,
                        name: n.nome,
                        tipo: n.tipo,
                        color: labelMap[n.tipo] || "#888",
                        origem: false,
                        noticia_id: n.noticia_id,
                    })),
            ],
            links: grafoRelacionadas.arestas.map((a) => ({
                source: a.origem,
                target: a.destino,
                tipo: a.relacao,
            })),
        }
        : null;

    const handleNodeClick = useCallback((node) => {
        setNosRemovidosIds((prev) => [...prev, node.id]);
    }, []);

    const handleReset = () => setNosRemovidosIds([]);

    const handlePesquisar = () => {
        onPesquisarRelacionadas(nosVisiveis.map((n) => n.nome));
    };

    const renderNo = (node, ctx, globalScale, small) => {
        const raio = small ? 4 : 6;
        const fontSize = (small ? 10 : 12) / globalScale;
        ctx.font = `${fontSize}px Sans-Serif`;
        ctx.fillStyle = node.color;
        ctx.beginPath();
        ctx.arc(node.x, node.y, raio, 0, 2 * Math.PI);
        ctx.fill();
        if (!node.origem) {
            ctx.strokeStyle = "rgba(255,255,255,0.2)";
            ctx.lineWidth = 0.8;
            ctx.stroke();
        }
        ctx.fillStyle = "#fff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const label = node.name.length > 10 ? node.name.slice(0, 10) + "..." : node.name;
        ctx.fillText(label, node.x, node.y + raio + 8);
        if (!node.origem && node.noticia_id) {
            ctx.fillStyle = "rgba(255,255,255,0.35)";
            ctx.font = `${fontSize * 0.75}px Sans-Serif`;
            ctx.fillText(node.noticia_id, node.x, node.y + raio + 18);
        }
    };

    return (
        <>
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
                    <p className="panel-msg">
                        Esta frase não tem entidades relacionadas.
                    </p>
                )}

                {!isLoading && grafo && graphData.nodes.length > 0 && (
                    <div className="panel-body-split">
                        {/* ── Grafo Principal ───────────────────────────── */}
                        <div className="panel-grafo-principal">
                            <div className="panel-hint"
                                 style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
                                <span>Clica num nó para o remover.</span>
                                <button
                                    className="btn-expand"
                                    title="Expandir grafo"
                                    onClick={() => openExpanded("principal")}
                                >
                                    ⛶
                                </button>
                            </div>

                            <ForceGraph2D
                                graphData={graphData}
                                width={260}
                                height={260}
                                nodeLabel={(n) => `${n.name} (${n.tipo})`}
                                nodeRelSize={6}
                                linkColor={() => "#444"}
                                nodeCanvasObject={(node, ctx, gs) =>
                                    renderNo(node, ctx, gs, false)
                                }
                                onNodeClick={handleNodeClick}
                            />

                            <button
                                className="btn-pesquisar"
                                onClick={handlePesquisar}
                                disabled={
                                    isLoadingRelacionadas || nosVisiveis.length === 0
                                }
                            >
                                {isLoadingRelacionadas
                                    ? "A pesquisar..."
                                    : "Procurar relações noutras notícias"}
                            </button>
                        </div>

                        {/* ── Grafo de Relações ─────────────────────────── */}
                        {grafoRelacionadas && (
                            <div className="panel-grafo-relacionadas">
                                <div
                                    className="relacionadas-header"
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                    }}
                                >
                                    <span>Relações encontradas</span>
                                    <button
                                        className="btn-expand"
                                        title="Expandir grafo"
                                        onClick={() => openExpanded("relacionadas")}
                                    >
                                        ⛶
                                    </button>
                                </div>

                                {!grafoRelacionadas.tem_resultados ? (
                                    <p className="panel-msg">
                                        Não foram encontradas relações noutras notícias.
                                    </p>
                                ) : (
                                    <>
                                        <div className="relacionadas-legenda">
                                            <span className="legenda-total">— Total</span>
                                            <span className="legenda-parcial">— Parcial</span>
                                        </div>

                                        <ForceGraph2D
                                            graphData={graphRelacionadasData}
                                            width={260}
                                            height={260}
                                            nodeLabel={(n) =>
                                                n.origem
                                                    ? `${n.name} (${n.tipo})`
                                                    : `${n.name} (${n.tipo}) — ${n.noticia_id}`
                                            }
                                            nodeRelSize={5}
                                            linkColor={(link) =>
                                                link.tipo === "total" ? "#4f7cff" : "#f59e0b"
                                            }
                                            linkWidth={(link) =>
                                                link.tipo === "total" ? 2 : 1
                                            }
                                            nodeCanvasObject={(node, ctx, gs) =>
                                                renderNo(node, ctx, gs, !node.origem)
                                            }
                                        />
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </aside>

            {/* ── Modal de Expansão ───────────────────────────── */}
            {expandedGraph && (
                <div
                    className="graph-modal-overlay"
                    onClick={closeExpanded}
                >
                    <div
                        className="graph-modal"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="graph-modal-header">
                            <h2>
                                {expandedGraph === "principal"
                                    ? "Grafo Principal"
                                    : "Relações Encontradas"}
                            </h2>
                            <button
                                className="btn-close"
                                onClick={closeExpanded}
                            >
                                ✕
                            </button>
                        </div>

                        <ForceGraph2D
                            graphData={
                                expandedGraph === "principal"
                                    ? graphData
                                    : graphRelacionadasData
                            }
                            width={window.innerWidth * 0.7}
                            height={window.innerHeight * 0.7}
                            nodeLabel={(n) =>
                                expandedGraph === "principal"
                                    ? `${n.name} (${n.tipo})`
                                    : n.origem
                                        ? `${n.name} (${n.tipo})`
                                        : `${n.name} (${n.tipo}) — ${n.noticia_id}`
                            }
                            nodeRelSize={
                                expandedGraph === "principal" ? 6 : 5
                            }
                            linkColor={(link) =>
                                expandedGraph === "principal"
                                    ? "#444"
                                    : link.tipo === "total"
                                        ? "#4f7cff"
                                        : "#f59e0b"
                            }
                            linkWidth={(link) =>
                                link.tipo === "total" ? 2 : 1
                            }
                            nodeCanvasObject={(node, ctx, gs) =>
                                renderNo(
                                    node,
                                    ctx,
                                    gs,
                                    expandedGraph === "relacionadas" &&
                                    !node.origem
                                )
                            }
                            onNodeClick={
                                expandedGraph === "principal"
                                    ? handleNodeClick
                                    : undefined
                            }
                        />
                    </div>
                </div>
            )}
        </>
    );
}