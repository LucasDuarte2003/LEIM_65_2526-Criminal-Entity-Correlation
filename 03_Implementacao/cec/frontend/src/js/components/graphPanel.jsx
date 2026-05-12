import React from "react";
import {createPortal} from "react-dom";
import ForceGraph2D from "react-force-graph-2d";
import "../../static/css/graphPanel.css";

const AMBITOS = [
    {id: "documento", label: "Documento"},
    {id: "pasta", label: "Pasta"},
    {id: "projeto", label: "Projeto"},
    {id: "global", label: "Global"},
];

const LAYOUTS = [
    {id: "forca", label: "Força"},
    {id: "circular", label: "Circular"},
    {id: "hierarquico", label: "Hierárquico"},
    {id: "radial", label: "Radial"},
];

const GRAPH_VARIANTS = Object.freeze({
    principal: "principal",
    relacionadas: "relacionadas",
});

const GRAPH_SIZES = Object.freeze({
    panelWidth: 260,
    panelHeight: 220,
    defaultNodeSize: 6,
    relatedNodeSize: 5,
    largeNodeRadius: 6,
    smallNodeRadius: 4,
    defaultFontSize: 12,
    smallFontSize: 10,
    maxLabelLength: 10,
    labelOffset: 8,
    noticiaOffset: 18,
});

const GRAPH_COLORS = Object.freeze({
    defaultNode: "#aaa",
    relatedNode: "#888",
    principalLink: "#444",
    totalLink: "#4f7cff",
    partialLink: "#f59e0b",
});

class GraphPanelHandler {
    constructor(component) {
        this.component = component;
    }

    buildViewModel() {
        const {grafo, grafoRelacionadas, isLoading, isLoadingRelacionadas} = this.component.props;
        const {nosRemovidosIds, expandedGraph, expandedLayout, ambito} = this.component.state;
        const visibleNodes = this.createVisibleNodes(grafo, nosRemovidosIds);
        const visibleLinks = this.createVisibleLinks(grafo, nosRemovidosIds);
        const graphData = this.createMainGraphData(visibleNodes, visibleLinks);
        const graphRelacionadasData = this.createRelatedGraphData(visibleNodes, grafoRelacionadas);
        const ambitoLabel = this.getAmbitoLabel(ambito);

        const expandedGraphDataRaw = expandedGraph === GRAPH_VARIANTS.principal ? graphData : graphRelacionadasData;
        const expandedGraphData = this.applyLayout(expandedGraphDataRaw, expandedLayout);

        return {
            grafo,
            isLoading,
            isLoadingRelacionadas,
            graphData,
            graphRelacionadasData,
            ambitoButtons: AMBITOS.map((scope) => this.createAmbitoButtonViewModel(scope, ambito)),
            layoutButtons: LAYOUTS.map((layout) => this.createLayoutButtonViewModel(layout, expandedLayout)),
            ambitoLabel,
            expandedGraph,
            expandedLayout,
            expandedGraphData,
            expandedGraphTitle: expandedGraph === GRAPH_VARIANTS.principal ? "Grafo Principal" : `Relações — ${ambitoLabel}`,
            shouldShowReset: Boolean(grafo) && nosRemovidosIds.length > 0,
            shouldShowEmptyGraphMessage: !isLoading && Boolean(grafo) && graphData.nodes.length === 0,
            shouldShowMainContent: !isLoading && Boolean(grafo) && graphData.nodes.length > 0,
            shouldShowRelacionadas: Boolean(grafoRelacionadas),
            shouldShowRelacionadasResults: Boolean(grafoRelacionadas?.tem_resultados),
            isSearchDisabled: isLoadingRelacionadas || visibleNodes.length === 0,
            useFixedLayout: expandedLayout !== "forca",
            mainNodeLabel: (node) => this.getMainNodeLabel(node),
            relatedNodeLabel: (node) => this.getRelatedNodeLabel(node),
            expandedNodeLabel: (node) => this.getExpandedNodeLabel(node, expandedGraph),
            mainLinkColor: () => GRAPH_COLORS.principalLink,
            relatedLinkColor: (link) => this.getLinkColor(GRAPH_VARIANTS.relacionadas, link),
            relatedLinkWidth: (link) => this.getLinkWidth(GRAPH_VARIANTS.relacionadas, link),
            expandedLinkColor: (link) => this.getLinkColor(expandedGraph, link),
            expandedLinkWidth: (link) => this.getLinkWidth(expandedGraph, link),
            renderPrimaryNode: (node, context, globalScale) => this.renderNode(node, context, globalScale, false),
            renderRelatedNode: (node, context, globalScale) => this.renderNode(node, context, globalScale, !node.origem),
            renderExpandedNode: (node, context, globalScale) => this.renderNode(node, context, globalScale, expandedGraph === GRAPH_VARIANTS.relacionadas && !node.origem),
            handlePesquisar: () => this.component.props.onPesquisarRelacionadas(visibleNodes.map((node) => node.nome), ambito),
        };
    }

    // ── Layouts ────────────────────────────────────────────────────

    applyLayout(graphData, layout) {
        if (!graphData || layout === "forca") return graphData;

        const nodes = graphData.nodes.map((n) => ({...n}));

        // Cria cópias frescas das arestas com ids como strings
        // (o D3 muta source/target para object references após a simulação)
        const links = graphData.links.map((l) => ({
            ...l,
            source: typeof l.source === "object" ? l.source.id : l.source,
            target: typeof l.target === "object" ? l.target.id : l.target,
        }));

        if (layout === "circular") {
            this._applyCircularLayout(nodes, 0, 0, 200);
        } else if (layout === "hierarquico") {
            this._applyHierarchicalLayout(nodes, links);
        } else if (layout === "radial") {
            this._applyRadialLayout(nodes, links);
        }

        return {nodes, links};
    }

    _applyCircularLayout(nodes, cx, cy, radius) {
        const count = nodes.length;
        nodes.forEach((node, i) => {
            const angle = (2 * Math.PI * i) / count - Math.PI / 2;
            node.x = node.fx = radius * Math.cos(angle);
            node.y = node.fy = radius * Math.sin(angle);
        });
    }

    _applyHierarchicalLayout(nodes, links) {
        const degree = {};
        nodes.forEach((n) => {
            degree[n.id] = 0;
        });
        links.forEach((l) => {
            const src = typeof l.source === "object" ? l.source.id : l.source;
            const tgt = typeof l.target === "object" ? l.target.id : l.target;
            if (degree[src] !== undefined) degree[src]++;
            if (degree[tgt] !== undefined) degree[tgt]++;
        });

        const sorted = [...nodes].sort((a, b) => (degree[b.id] || 0) - (degree[a.id] || 0));
        const layers = 4;
        const perLayer = Math.ceil(sorted.length / layers);
        const layerHeight = 120;
        const nodeSpacing = 100;

        sorted.forEach((node, i) => {
            const layer = Math.floor(i / perLayer);
            const posInLayer = i % perLayer;
            const layerCount = Math.min(perLayer, sorted.length - layer * perLayer);
            const target = nodes.find((n) => n.id === node.id);
            if (target) {
                target.x = target.fx = (posInLayer - (layerCount - 1) / 2) * nodeSpacing;
                target.y = target.fy = (layer - (layers - 1) / 2) * layerHeight;
            }
        });
    }

    _applyRadialLayout(nodes, links) {
        if (nodes.length === 0) return;

        const degree = {};
        nodes.forEach((n) => {
            degree[n.id] = 0;
        });
        links.forEach((l) => {
            const src = typeof l.source === "object" ? l.source.id : l.source;
            const tgt = typeof l.target === "object" ? l.target.id : l.target;
            if (degree[src] !== undefined) degree[src]++;
            if (degree[tgt] !== undefined) degree[tgt]++;
        });

        const sorted = [...nodes].sort((a, b) => (degree[b.id] || 0) - (degree[a.id] || 0));
        const ringSize = 6;
        const ringRadius = 100;

        sorted.forEach((node, i) => {
            const target = nodes.find((n) => n.id === node.id);
            if (!target) return;
            if (i === 0) {
                target.x = target.fx = 0;
                target.y = target.fy = 0;
                return;
            }
            const ring = Math.ceil(i / ringSize);
            const posInRing = (i - 1) % ringSize;
            const countInRing = Math.min(ringSize, sorted.length - 1 - (ring - 1) * ringSize);
            const angle = (2 * Math.PI * posInRing) / countInRing - Math.PI / 2;
            target.x = target.fx = ringRadius * ring * Math.cos(angle);
            target.y = target.fy = ringRadius * ring * Math.sin(angle);
        });
    }

    // ── View model helpers ─────────────────────────────────────────

    createVisibleNodes(grafo, removedNodeIds) {
        if (!grafo) return [];
        return grafo.nos.filter((node) => !removedNodeIds.includes(node.id));
    }

    createVisibleLinks(grafo, removedNodeIds) {
        if (!grafo) return [];
        return grafo.arestas.filter((edge) => {
            return !removedNodeIds.includes(edge.origem) && !removedNodeIds.includes(edge.destino);
        });
    }

    createMainGraphData(visibleNodes, visibleLinks) {
        return {
            nodes: visibleNodes.map((node) => this.createMainNode(node)),
            links: visibleLinks.map((edge) => ({source: edge.origem, target: edge.destino})),
        };
    }

    createRelatedGraphData(visibleNodes, grafoRelacionadas) {
        if (!grafoRelacionadas) return null;
        return {
            nodes: [
                ...visibleNodes.map((node) => this.createRelatedSourceNode(node)),
                ...grafoRelacionadas.nos.filter((node) => !node.origem).map((node) => this.createRelatedTargetNode(node)),
            ],
            links: grafoRelacionadas.arestas.map((edge) => ({
                source: edge.origem,
                target: edge.destino,
                tipo: edge.relacao,
            })),
        };
    }

    createMainNode(node) {
        const {labelMap} = this.component.props;
        return {id: node.id, name: node.nome, tipo: node.tipo, color: labelMap[node.tipo] || GRAPH_COLORS.defaultNode};
    }

    createRelatedSourceNode(node) {
        const {labelMap} = this.component.props;
        return {
            id: node.nome,
            name: node.nome,
            tipo: node.tipo,
            color: labelMap[node.tipo] || GRAPH_COLORS.defaultNode,
            origem: true
        };
    }

    createRelatedTargetNode(node) {
        const {labelMap} = this.component.props;
        return {
            id: node.id,
            name: node.nome,
            tipo: node.tipo,
            color: labelMap[node.tipo] || GRAPH_COLORS.relatedNode,
            origem: false,
            noticia_ids: node.noticia_ids || [],
        };
    }

    createAmbitoButtonViewModel(scope, ambitoAtual) {
        return {
            id: scope.id,
            label: scope.label,
            className: `ambito-btn ${ambitoAtual === scope.id ? "active" : ""}`,
            onClick: () => this.component.handleAmbitoChange(scope.id),
        };
    }

    createLayoutButtonViewModel(layout, layoutAtual) {
        return {
            id: layout.id,
            label: layout.label,
            className: `layout-btn ${layoutAtual === layout.id ? "active" : ""}`,
            onClick: () => this.component.handleLayoutChange(layout.id),
        };
    }

    getAmbitoLabel(ambitoId) {
        return AMBITOS.find((scope) => scope.id === ambitoId)?.label || "Global";
    }

    getMainNodeLabel(node) {
        return `${node.name} (${node.tipo})`;
    }

    getRelatedNodeLabel(node) {
        if (node.origem) return `${node.name} (${node.tipo})`;
        const noticias = node.noticia_ids?.join(", ") || "";
        return `${node.name} (${node.tipo}) — ${noticias}`;
    }

    getExpandedNodeLabel(node, expandedGraph) {
        if (expandedGraph === GRAPH_VARIANTS.principal) return this.getMainNodeLabel(node);
        return this.getRelatedNodeLabel(node);
    }

    getLinkColor(graphVariant, link) {
        if (graphVariant === GRAPH_VARIANTS.principal) return GRAPH_COLORS.principalLink;
        return link.tipo === "total" ? GRAPH_COLORS.totalLink : GRAPH_COLORS.partialLink;
    }

    getLinkWidth(graphVariant, link) {
        if (graphVariant === GRAPH_VARIANTS.principal) return 1;
        return link.tipo === "total" ? 2 : 1;
    }

    renderNode(node, context, globalScale, isSmall) {
        const radius = isSmall ? GRAPH_SIZES.smallNodeRadius : GRAPH_SIZES.largeNodeRadius;
        const fontSize = (isSmall ? GRAPH_SIZES.smallFontSize : GRAPH_SIZES.defaultFontSize) / globalScale;

        context.font = `${fontSize}px Sans-Serif`;
        context.fillStyle = node.color;
        context.beginPath();
        context.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        context.fill();

        if (!node.origem) {
            context.strokeStyle = this.getCssVariable("--graph-outline", "rgba(255,255,255,0.2)");
            context.lineWidth = 0.8;
            context.stroke();
        }

        context.fillStyle = this.getCssVariable("--graph-text", "#ffffff");
        context.textAlign = "center";
        context.textBaseline = "middle";
        context.fillText(this.truncateLabel(node.name), node.x, node.y + radius + GRAPH_SIZES.labelOffset);

        if (!node.origem && node.noticia_ids?.length > 0) {
            context.fillStyle = this.getCssVariable("--graph-secondary-text", "rgba(255,255,255,0.35)");
            context.font = `${fontSize * 0.75}px Sans-Serif`;
            const label = node.noticia_ids.length === 1
                ? node.noticia_ids[0]
                : `${node.noticia_ids.length} notícias`;
            context.fillText(label, node.x, node.y + radius + GRAPH_SIZES.noticiaOffset);
        }
    }

    truncateLabel(name) {
        if (name.length <= GRAPH_SIZES.maxLabelLength) return name;
        return `${name.slice(0, GRAPH_SIZES.maxLabelLength)}...`;
    }

getCssVariable(name, fallback) {
    if (typeof window === "undefined") return fallback;

    return getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim() || fallback;
}
}

class GraphPanelRenderer {
    renderHeader(viewModel, component) {
        return (
            <div className="panel-header">
                <h2>Grafo</h2>
                {viewModel.shouldShowReset && (
                    <button className="btn-reset" onClick={component.handleReset}>Repor</button>
                )}
            </div>
        );
    }

    renderStatusMessages(viewModel) {
        return (
            <>
                {viewModel.isLoading && <p className="panel-msg">A carregar grafo...</p>}
                {!viewModel.isLoading && !viewModel.grafo && (
                    <p className="panel-msg">Clica em <strong>◉</strong> numa frase para ver as relações.</p>
                )}
                {viewModel.shouldShowEmptyGraphMessage && (
                    <p className="panel-msg">Esta frase não tem entidades relacionadas.</p>
                )}
            </>
        );
    }

    renderAmbitoButtons(viewModel) {
        return viewModel.ambitoButtons.map((button) => (
            <button key={button.id} className={button.className} onClick={button.onClick}>{button.label}</button>
        ));
    }

    renderLayoutButtons(viewModel) {
        return viewModel.layoutButtons.map((button) => (
            <button key={button.id} className={button.className} onClick={button.onClick}>{button.label}</button>
        ));
    }

    renderMainGraph(viewModel, component) {
        return (
            <div className="panel-grafo-principal">
                <div className="panel-hint panel-inline-header">
                    <span>Clica num nó para o remover.</span>
                    <button className="btn-expand" title="Expandir grafo" onClick={component.handleOpenPrincipal}>⛶
                    </button>
                </div>
                <ForceGraph2D
                    graphData={viewModel.graphData}
                    width={GRAPH_SIZES.panelWidth}
                    height={GRAPH_SIZES.panelHeight}
                    nodeLabel={viewModel.mainNodeLabel}
                    nodeRelSize={GRAPH_SIZES.defaultNodeSize}
                    linkColor={viewModel.mainLinkColor}
                    nodeCanvasObject={viewModel.renderPrimaryNode}
                    onNodeClick={component.handleNodeClick}
                />
                <div className="ambito-selector">{this.renderAmbitoButtons(viewModel)}</div>
                <button className="btn-pesquisar" onClick={viewModel.handlePesquisar}
                        disabled={viewModel.isSearchDisabled}>
                    {viewModel.isLoadingRelacionadas ? "A pesquisar..." : "Procurar relações"}
                </button>
            </div>
        );
    }

    renderRelatedGraph(viewModel, component) {
        if (!viewModel.shouldShowRelacionadas) return null;
        return (
            <div className="panel-grafo-relacionadas">
                <div className="relacionadas-header panel-inline-header">
                    <span>Relações — {viewModel.ambitoLabel}</span>
                    <button className="btn-expand" title="Expandir grafo" onClick={component.handleOpenRelacionadas}>⛶
                    </button>
                </div>
                {!viewModel.shouldShowRelacionadasResults ? (
                    <p className="panel-msg">Não foram encontradas relações neste âmbito.</p>
                ) : (
                    <>
                        <div className="relacionadas-legenda">
                            <span className="legenda-total">— Total</span>
                            <span className="legenda-parcial">— Parcial</span>
                        </div>
                        <ForceGraph2D
                            graphData={viewModel.graphRelacionadasData}
                            width={GRAPH_SIZES.panelWidth}
                            height={GRAPH_SIZES.panelHeight}
                            nodeLabel={viewModel.relatedNodeLabel}
                            nodeRelSize={GRAPH_SIZES.relatedNodeSize}
                            linkColor={viewModel.relatedLinkColor}
                            linkWidth={viewModel.relatedLinkWidth}
                            nodeCanvasObject={viewModel.renderRelatedNode}
                        />
                    </>
                )}
            </div>
        );
    }

    renderExpandedGraph(viewModel, component) {
        if (!viewModel.expandedGraph) return null;

        return createPortal(
            <div className="graph-modal-overlay" onClick={component.handleCloseExpanded}>
                <div className="graph-modal" onClick={component.handleModalContentClick}>
                    <div className="graph-modal-header">
                        <h2>{viewModel.expandedGraphTitle}</h2>
                        <div className="layout-selector">
                            {this.renderLayoutButtons(viewModel)}
                        </div>
                        <button className="btn-close" onClick={component.handleCloseExpanded}>✕</button>
                    </div>
                    <ForceGraph2D
                        graphData={viewModel.expandedGraphData}
                        width={window.innerWidth * 0.7}
                        height={window.innerHeight * 0.7 - 60}
                        nodeLabel={viewModel.expandedNodeLabel}
                        nodeRelSize={viewModel.expandedGraph === GRAPH_VARIANTS.principal ? GRAPH_SIZES.defaultNodeSize : GRAPH_SIZES.relatedNodeSize}
                        linkColor={viewModel.expandedLinkColor}
                        linkWidth={viewModel.expandedLinkWidth}
                        nodeCanvasObject={viewModel.renderExpandedNode}
                        onNodeClick={viewModel.expandedGraph === GRAPH_VARIANTS.principal ? component.handleNodeClick : undefined}
                        cooldownTicks={viewModel.useFixedLayout ? 0 : undefined}
                        dagMode={null}
                    />
                </div>
            </div>,
            document.body
        );
    }

    renderMainContent(viewModel, component) {
        if (!viewModel.shouldShowMainContent) return null;
        return (
            <div className="panel-body-split">
                {this.renderMainGraph(viewModel, component)}
                {this.renderRelatedGraph(viewModel, component)}
            </div>
        );
    }

    render(viewModel, component) {
        return (
            <aside className="right-panel">
                {this.renderHeader(viewModel, component)}
                {this.renderStatusMessages(viewModel)}
                {this.renderMainContent(viewModel, component)}
                {this.renderExpandedGraph(viewModel, component)}
            </aside>
        );
    }
}

export default class GraphPanel extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            nosRemovidosIds: [],
            expandedGraph: null,
            expandedLayout: "forca",
            ambito: "global",
        };
        this.handler = new GraphPanelHandler(this);
        this.renderer = new GraphPanelRenderer();
    }

    handleNodeClick = (node) => {
        this.setState((previousState) => {
            if (previousState.nosRemovidosIds.includes(node.id)) return null;
            return {nosRemovidosIds: [...previousState.nosRemovidosIds, node.id]};
        });
    };

    handleReset = () => {
        this.setState({nosRemovidosIds: []});
    };

    handleAmbitoChange = (novoAmbito) => {
        this.setState({ambito: novoAmbito});
        this.props.onLimparRelacionadas();
    };

    handleLayoutChange = (novoLayout) => {
        this.setState({expandedLayout: novoLayout});
    };

    handleOpenPrincipal = () => {
        this.setState({expandedGraph: GRAPH_VARIANTS.principal, expandedLayout: "forca"});
    };

    handleOpenRelacionadas = () => {
        this.setState({expandedGraph: GRAPH_VARIANTS.relacionadas, expandedLayout: "forca"});
    };

    handleCloseExpanded = () => {
        this.setState({expandedGraph: null});
    };

    handleModalContentClick = (event) => {
        event.stopPropagation();
    };

    render() {
        const viewModel = this.handler.buildViewModel();
        return this.renderer.render(viewModel, this);
    }
}