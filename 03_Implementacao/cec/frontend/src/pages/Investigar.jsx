import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { getInvestigar } from "../js/api/client.jsx";
import { useLabels } from "../js/hooks/useLabels.jsx";
import "../static/css/investigar.css";

const TIPOS_ENTIDADE = [
    "PESSOA", "LOCAL", "ORGANIZACAO", "CRIME", "DATA",
    "VIATURA", "MATRICULA", "TELEMOVEL", "EMAIL", "CRIPTO", "MONTANTE"
];

export default function Investigar() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { labelMap } = useLabels();

    const [query, setQuery] = useState(searchParams.get("nome") || "");
    const [tipoFiltro, setTipoFiltro] = useState("");
    const [ambito, setAmbito] = useState("global");
    const [resultado, setResultado] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [erro, setErro] = useState(null);

    const inputRef = useRef(null);

    // Se veio com ?nome= na URL, pesquisa automaticamente
    useEffect(() => {
        const nomeParam = searchParams.get("nome");
        if (nomeParam) {
            setQuery(nomeParam);
            executarPesquisa(nomeParam, "", "global");
        } else {
            inputRef.current?.focus();
        }
    }, []);

    const executarPesquisa = async (nome, tipo, amb) => {
        if (!nome?.trim()) return;
        setIsLoading(true);
        setErro(null);
        try {
            const data = await getInvestigar(nome.trim(), tipo || null, amb);
            setResultado(data);
        } catch {
            setErro("Erro ao pesquisar. Tenta novamente.");
            setResultado(null);
        } finally {
            setIsLoading(false);
        }
    };

    const handlePesquisar = () => executarPesquisa(query, tipoFiltro, ambito);

    const handleKeyDown = (e) => {
        if (e.key === "Enter") handlePesquisar();
    };

    const handleNoticiaClick = (noticia) => {
        if (noticia.projeto_id && noticia.pasta_id) {
            navigate(`/projeto/${noticia.projeto_id}/pasta/${noticia.pasta_id}?noticia=${noticia.id}`);
        }
    };

    const handleEntidadeRelacionadaClick = (nome) => {
        setQuery(nome);
        executarPesquisa(nome, tipoFiltro, ambito);
    };

    const buildGrafoData = () => {
        if (!resultado?.grafo) return { nodes: [], links: [] };
        return {
            nodes: resultado.grafo.nos.map((n) => ({
                id: n.id,
                name: n.nome,
                tipo: n.tipo,
                origem: n.origem,
                color: labelMap[n.tipo] || "#aaa",
            })),
            links: resultado.grafo.arestas.map((a) => ({
                source: a.origem,
                target: a.destino,
            })),
        };
    };

    const renderNode = (node, ctx, globalScale) => {
        const radius = node.origem ? 8 : 5;
        const fontSize = 11 / globalScale;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = node.color;
        ctx.fill();

        if (node.origem) {
            ctx.strokeStyle = "rgba(255,255,255,0.6)";
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        ctx.font = `${fontSize}px Sans-Serif`;
        ctx.fillStyle = getComputedStyle(document.documentElement)
    .getPropertyValue("--graph-text").trim() || "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(
            node.name.length > 12 ? node.name.slice(0, 12) + "…" : node.name,
            node.x,
            node.y + radius + 3
        );
    };

    return (
        <div className="investigar-page">
            {/* ── Header ── */}
            <header className="investigar-header">
                <button className="btn-voltar-inv" onClick={() => navigate(-1)}>← Voltar</button>
                <h1 className="investigar-titulo">Investigação</h1>
            </header>

            {/* ── Barra de pesquisa ── */}
            <div className="investigar-search-bar">
                <input
                    ref={inputRef}
                    className="investigar-input"
                    type="text"
                    placeholder="Nome da entidade..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                />
                <select
                    className="investigar-select"
                    value={tipoFiltro}
                    onChange={(e) => setTipoFiltro(e.target.value)}
                >
                    <option value="">Todos os tipos</option>
                    {TIPOS_ENTIDADE.map((t) => (
                        <option key={t} value={t}>{t}</option>
                    ))}
                </select>
                <select
                    className="investigar-select"
                    value={ambito}
                    onChange={(e) => setAmbito(e.target.value)}
                >
                    <option value="global">Global</option>
                    <option value="projeto">Projeto</option>
                    <option value="pasta">Pasta</option>
                    <option value="documento">Documento</option>
                </select>
                <button
                    className="investigar-btn-pesquisar"
                    onClick={handlePesquisar}
                    disabled={isLoading || !query.trim()}
                >
                    {isLoading ? "A pesquisar..." : "Pesquisar"}
                </button>
            </div>

            {/* ── Erros / estados ── */}
            {erro && <p className="investigar-erro">{erro}</p>}
            {!isLoading && !resultado && !erro && (
                <p className="investigar-placeholder">
                    Pesquisa uma entidade para investigar as suas relações.
                </p>
            )}
            {!isLoading && resultado?.entidade === null && (
                <p className="investigar-placeholder">Entidade não encontrada.</p>
            )}

            {/* ── Resultados ── */}
            {resultado?.entidade && (
                <div className="investigar-resultados">

                    {/* Cabeçalho da entidade */}
                    <div className="investigar-entidade-header">
                        <span
                            className="investigar-entidade-badge"
                            style={{ background: labelMap[resultado.entidade.tipo] || "#aaa" }}
                        >
                            {resultado.entidade.tipo}
                        </span>
                        <h2 className="investigar-entidade-nome">{resultado.entidade.nome}</h2>
                        <span className="investigar-entidade-count">
                            {resultado.noticias.length} notícia{resultado.noticias.length !== 1 ? "s" : ""}
                        </span>
                    </div>

                    {/* ── 3 colunas ── */}
                    <div className="investigar-colunas">

                        {/* Coluna 1 — Notícias */}
                        <div className="investigar-coluna">
                            <h3 className="investigar-coluna-titulo">Notícias</h3>
                            {resultado.noticias.length === 0 ? (
                                <p className="investigar-vazio">Sem notícias.</p>
                            ) : (
                                <div className="investigar-noticias-lista">
                                    {resultado.noticias.map((n) => (
                                        <div
                                            key={n.id}
                                            className="investigar-noticia-item"
                                            onClick={() => handleNoticiaClick(n)}
                                            title="Abrir no editor"
                                        >
                                            <span className="investigar-noticia-titulo">{n.titulo}</span>
                                            <div className="investigar-noticia-meta">
                                                {n.projeto_nome && <span>📂 {n.projeto_nome}</span>}
                                                {n.pasta_nome && <span>📁 {n.pasta_nome}</span>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Coluna 2 — Grafo */}
                        <div className="investigar-coluna investigar-coluna-grafo">
                            <h3 className="investigar-coluna-titulo">Grafo de co-ocorrências</h3>
                            {resultado.grafo.nos.length <= 1 ? (
                                <p className="investigar-vazio">Sem co-ocorrências encontradas.</p>
                            ) : (
                                <ForceGraph2D
                                    graphData={buildGrafoData()}
                                    width={380}
                                    height={380}
                                    nodeLabel={(n) => `${n.name} (${n.tipo})`}
                                    nodeRelSize={6}
                                    linkColor={() => "rgba(255,255,255,0.15)"}
                                    nodeCanvasObject={renderNode}
                                    onNodeDoubleClick={(node) => handleEntidadeRelacionadaClick(node.name)}
                                />
                            )}
                            <p className="investigar-hint">Double-click num nó para investigar essa entidade.</p>
                        </div>

                        {/* Coluna 3 — Entidades relacionadas */}
                        <div className="investigar-coluna">
                            <h3 className="investigar-coluna-titulo">Entidades relacionadas</h3>
                            {resultado.relacionadas.length === 0 ? (
                                <p className="investigar-vazio">Sem entidades relacionadas.</p>
                            ) : (
                                <div className="investigar-relacionadas-lista">
                                    {resultado.relacionadas.map((r) => (
                                        <button
                                            key={r.nome}
                                            className="investigar-relacionada-item"
                                            onClick={() => handleEntidadeRelacionadaClick(r.nome)}
                                        >
                                            <span
                                                className="investigar-relacionada-tipo"
                                                style={{ background: labelMap[r.tipo] || "#aaa" }}
                                            >
                                                {r.tipo}
                                            </span>
                                            <span className="investigar-relacionada-nome">{r.nome}</span>
                                            <span className="investigar-relacionada-count">{r.co_ocorrencias}×</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}