import { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useNoticias } from "../js/hooks/useNoticias.jsx";
import { useLabels } from "../js/hooks/useLabels.jsx";
import { useGrafo } from "../js/hooks/useGrafo.jsx";
import { useTheme } from "../js/hooks/useTheme.jsx";
import NewsList from "../js/components/NewsList.jsx";
import LabelBar from "../js/components/LabelBar.jsx";
import ActionBar from "../js/components/ActionBar.jsx";
import ArticleViewer from "../js/components/ArticleViewer.jsx";
import GraphPanel from "../js/components/GraphPanel.jsx";
import { getNoticias_semelhantes } from "../js/api/client.jsx";
import "../static/css/app.css";

export default function Editor() {
    const { pastaId } = useParams();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { theme, toggleTheme } = useTheme();
    const [vistaAtiva, setVistaAtiva] = useState(
        () => localStorage.getItem("modoExtracao") || "ambos"
    );

    const {
        lista, noticia, frasesGliner, isLoading,
        selecionar, adicionarNoticia, guardar,
        atualizarFrase, atualizarFraseGliner, apagarNoticia, removerDaLista,
    } = useNoticias(pastaId);

    const { labels, labelMap } = useLabels();
    const {
        grafo, grafoRelacionadas, fraseAtiva, fraseFundida, isLoading: grafoLoading,
        isLoadingRelacionadas, carregarGrafo, fundirFrase, pesquisarRelacionadas,
        limparGrafo, limparRelacionadas,
    } = useGrafo();

    const [labelSelecionada, setLabelSelecionada] = useState(null);
    const [entidadeSelecionada, setEntidadeSelecionada] = useState(null);
    const [pendingSelection, setPendingSelection] = useState(null);
    const [semelhantes, setSemelhantes] = useState(null);
    const [isLoadingSemelhantes, setIsLoadingSemelhantes] = useState(false);

    const ORDEM_LABELS = [
        "PESSOA", "LOCAL", "ORGANIZACAO", "CRIME", "DATA",
        "VIATURA", "MATRICULA", "TELEMOVEL", "EMAIL", "CRIPTO", "MONTANTE"
    ];
    const LABEL_SHORTCUTS = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
        "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ];

    const labelsOrdenadas = [...labels].sort(
        (a, b) => ORDEM_LABELS.indexOf(a.nome) - ORDEM_LABELS.indexOf(b.nome)
    );
    const labelsComAtalho = labelsOrdenadas.map((label, index) => ({
        ...label,
        shortcut: LABEL_SHORTCUTS[index] || null,
    }));

    // Atalhos de teclado para labels
    useEffect(() => {
        const handleKeyDown = (event) => {
            const tag = document.activeElement?.tagName;
            if (tag === "INPUT" || tag === "TEXTAREA") return;
            const tecla = event.key.toUpperCase();
            const labelEncontrada = labelsComAtalho.find((l) => l.shortcut === tecla);
            if (labelEncontrada) setLabelSelecionada(labelEncontrada.nome);
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [labelsComAtalho]);

    // Selecciona noticia passada via query param ?noticia=id
    // Aguarda que a lista esteja carregada antes de seleccionar
    useEffect(() => {
        const noticiaId = searchParams.get("noticia");
        if (!noticiaId || lista.length === 0) return;
        const existe = lista.some((n) => n.id === noticiaId);
        if (existe) selecionar(noticiaId);
    }, [lista, searchParams]);

    const handleTextSelect = (e, frase) => {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
        const range = selection.getRangeAt(0);
        const texto = selection.toString().trim();
        if (!texto) return;
        const preRange = range.cloneRange();
        preRange.selectNodeContents(e.currentTarget);
        preRange.setEnd(range.startContainer, range.startOffset);
        const inicio = preRange.toString().length;
        const fim = inicio + texto.length;
        setPendingSelection({ fraseId: frase.id, inicio, fim, texto });
        setEntidadeSelecionada(null);
    };

    const handleUpdate = () => {
        if (!labelSelecionada) return alert("Seleciona um tipo de entidade.");
        if (!pendingSelection) return alert("Seleciona texto na noticia.");
        if (!noticia) return;

        const frase = noticia.frases.find((f) => f.id === pendingSelection.fraseId);
        if (!frase) return;

        const { inicio, fim, texto, fraseId } = pendingSelection;
        const overlap = frase.entidades.some((e) => inicio < e.fim && fim > e.inicio);
        if (overlap) return alert("A selecao sobrepoem-se a uma entidade existente.");

        const novasEntidades = [
            ...frase.entidades,
            { nome: texto, tipo: labelSelecionada, inicio, fim },
        ].sort((a, b) => a.inicio - b.inicio);

        atualizarFrase(fraseId, novasEntidades);

        if (vistaAtiva === "ambos" && frasesGliner) {
            const fraseGliner = frasesGliner.find((f) => f.id === fraseId);
            if (fraseGliner) {
                const novasEntidadesGliner = [
                    ...fraseGliner.entidades,
                    { nome: texto, tipo: labelSelecionada, inicio, fim },
                ].sort((a, b) => a.inicio - b.inicio);
                atualizarFraseGliner(fraseId, novasEntidadesGliner);
            }
        }

        setPendingSelection(null);
        window.getSelection()?.removeAllRanges();
    };

    const handleRemover = () => {
        if (!entidadeSelecionada) return alert("Clica numa entidade para a selecionar.");
        if (!noticia) return;

        const { fraseId, index, entidade } = entidadeSelecionada;
        const fonte = entidade?.fonte;

        if (vistaAtiva === "gliner" && frasesGliner) {
            const fraseGliner = frasesGliner.find((f) => f.id === fraseId);
            if (!fraseGliner) return;
            atualizarFraseGliner(fraseId, fraseGliner.entidades.filter((_, i) => i !== index));
        } else if (vistaAtiva === "ambos") {
            if (fonte === "xlm" || fonte === "ambos") {
                const frase = noticia.frases.find((f) => f.id === fraseId);
                if (frase) atualizarFrase(fraseId, frase.entidades.filter((_, i) => i !== index));
            }
            if (fonte === "gliner" || fonte === "ambos") {
                const fraseGliner = frasesGliner?.find((f) => f.id === fraseId);
                if (fraseGliner) {
                    atualizarFraseGliner(fraseId, fraseGliner.entidades.filter(
                        (e) => !(e.nome === entidade.nome && e.inicio === entidade.inicio)
                    ));
                }
            }
        } else {
            const frase = noticia.frases.find((f) => f.id === fraseId);
            if (!frase) return;
            atualizarFrase(fraseId, frase.entidades.filter((_, i) => i !== index));
        }

        setEntidadeSelecionada(null);
    };

    const handleEntidadeClick = (fraseId, index, entidade) => {
        setEntidadeSelecionada({ fraseId, index, entidade });
        setLabelSelecionada(entidade.tipo);
        setPendingSelection(null);
    };

    const handleApagarNoticia = async () => {
        if (!noticia) return;
        if (!confirm(`Apagar a noticia "${noticia.titulo}"? Esta acao nao pode ser revertida.`)) return;
        await apagarNoticia(noticia.id);
        limparGrafo();
    };

    const handleSemelhantes = async () => {
        if (!noticia) return;
        setIsLoadingSemelhantes(true);
        try {
            const resultado = await getNoticias_semelhantes(noticia.id);
            setSemelhantes(resultado);
        } catch {
            alert("Erro ao procurar noticias semelhantes.");
        } finally {
            setIsLoadingSemelhantes(false);
        }
    };

    const handleMudarPasta = (novoProjetoId, novaPastaId) => {
        navigate(`/projeto/${novoProjetoId}/pasta/${novaPastaId}`);
    };

    return (
        <div className="app">
            <NewsList
                noticiaAtiva={noticia}
                noticiaCount={lista.length}
                pastaId={pastaId}
                onSelecionar={selecionar}
                onAdicionar={(texto) => adicionarNoticia(texto, pastaId)}
                onApagar={handleApagarNoticia}
                onMover={removerDaLista}
                onMudarPasta={handleMudarPasta}
                onVoltar={() => navigate("/")}
                isLoading={isLoading}
            />

            <main className="main-content">
                <div className="editor-topbar">
                    <h1>Criminal Entity Correlation</h1>
                    <div className="editor-topbar-actions">
                        <button className="btn-investigar" onClick={() => navigate("/investigar")}>
                            Investigar entidades
                        </button>
                        <button className="btn-theme-toggle" onClick={toggleTheme}>
                            {theme === "dark" ? "Modo claro" : "Modo escuro"}
                        </button>
                    </div>
                </div>

                <LabelBar
                    labels={labelsComAtalho}
                    labelSelecionada={labelSelecionada}
                    onSelecionar={setLabelSelecionada}
                    vistaAtiva={vistaAtiva}
                    onVistaChange={setVistaAtiva}
                    modoExtracao={localStorage.getItem("modoExtracao") || "xlm-roberta"}
                />

                <ActionBar
                    labelSelecionada={labelSelecionada}
                    textoSelecionado={pendingSelection?.texto}
                    onUpdate={handleUpdate}
                    onRemover={handleRemover}
                    onGuardar={() => guardar(limparGrafo)}
                    onSemelhantes={handleSemelhantes}
                    noticiaId={noticia?.id}
                    isLoading={isLoading || isLoadingSemelhantes}
                />

                <ArticleViewer
                    noticia={noticia}
                    labelMap={labelMap}
                    fraseAtiva={fraseAtiva}
                    fraseFundida={fraseFundida}
                    entidadeSelecionada={entidadeSelecionada}
                    onFraseClick={carregarGrafo}
                    onFraseFundir={fundirFrase}
                    onEntidadeClick={handleEntidadeClick}
                    onTextSelect={handleTextSelect}
                    frasesGliner={frasesGliner}
                    vistaAtiva={vistaAtiva}
                />
            </main>

            <GraphPanel
                grafo={grafo}
                grafoRelacionadas={grafoRelacionadas}
                labelMap={labelMap}
                isLoading={grafoLoading}
                isLoadingRelacionadas={isLoadingRelacionadas}
                onPesquisarRelacionadas={pesquisarRelacionadas}
                onLimparRelacionadas={limparRelacionadas}
            />

            {semelhantes && (
                <div className="modal-overlay" onClick={() => setSemelhantes(null)}>
                    <div className="modal semelhantes-modal" onClick={(e) => e.stopPropagation()}>
                        <h2>Noticias Semelhantes</h2>
                        {semelhantes.length === 0 ? (
                            <p style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "13px" }}>
                                Nao foram encontradas noticias semelhantes.
                            </p>
                        ) : (
                            <div className="semelhantes-lista">
                                {semelhantes.map((n) => (
                                    <div key={n.id} className="semelhante-item" onClick={() => {
                                        selecionar(n.id);
                                        setSemelhantes(null);
                                    }}>
                                        <div className="semelhante-header">
                                            <span className="semelhante-titulo">{n.titulo}</span>
                                            <span className="semelhante-score">{n.percentagem}%</span>
                                        </div>
                                        <div className="semelhante-meta">
                                            <span>pasta: {n.pasta_nome || "—"}</span>
                                            <span>projeto: {n.projeto_nome || "—"}</span>
                                            <span>
                                                {n.entidades_comuns} entidade{n.entidades_comuns !== 1 ? "s" : ""} em comum
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                        <div className="modal-actions">
                            <button className="btn-confirmar" onClick={() => setSemelhantes(null)}>
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}