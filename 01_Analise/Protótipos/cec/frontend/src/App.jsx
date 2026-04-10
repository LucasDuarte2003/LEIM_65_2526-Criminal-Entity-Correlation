import {useEffect, useState} from "react";
import {useNoticias} from "./hooks/useNoticias";
import {useLabels} from "./hooks/useLabels";
import {useGrafo} from "./hooks/useGrafo";
import NewsList from "./components/NewsList";
import LabelBar from "./components/LabelBar";
import ActionBar from "./components/ActionBar";
import ArticleViewer from "./components/ArticleViewer";
import GraphPanel from "./components/GraphPanel";
import "./App.css";

export default function App() {
    const {
        lista,
        noticia,
        isLoading,
        selecionar,
        adicionarNoticia,
        guardar,
        atualizarFrase
    } = useNoticias();

    const {labels, labelMap} = useLabels();
    const {
        grafo,
        grafoRelacionadas,
        fraseAtiva,
        isLoading: grafoLoading,
        isLoadingRelacionadas,
        carregarGrafo,
        pesquisarRelacionadas,
    } = useGrafo();

    const [labelSelecionada, setLabelSelecionada] = useState(null);
    const [entidadeSelecionada, setEntidadeSelecionada] = useState(null); // { fraseId, index, entidade }
    const [pendingSelection, setPendingSelection] = useState(null); // { fraseId, inicio, fim, texto }

    /**
     * Lista de atalhos usados para selecionar labels pelo teclado.
     * As primeiras labels recebem 0-9 e as seguintes recebem A-Z.
     */
    const LABEL_SHORTCUTS = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
        "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
        "U", "V", "W", "X", "Y", "Z"
    ];

    /**
     * Ordem fixa das labels para garantir que os atalhos
     * ficam sempre associados às mesmas entidades.
     */
    const ORDEM_LABELS = [
        "PESSOA",
        "LOCAL",
        "ORGANIZACAO",
        "CRIME",
        "DATA",
        "VIATURA",
        "MATRICULA",
        "TELEMOVEL",
        "EMAIL",
        "CRIPTO",
        "MONTANTE"
    ];

    /**
     * Ordena as labels e acrescenta o respetivo atalho
     * para serem mostradas no LabelBar.
     */
    const labelsOrdenadas = [...labels].sort(
        (a, b) => ORDEM_LABELS.indexOf(a.nome) - ORDEM_LABELS.indexOf(b.nome)
    );

    const labelsComAtalho = labelsOrdenadas.map((label, index) => ({
        ...label,
        shortcut: LABEL_SHORTCUTS[index] || null
    }));

    /**
     * Fica à escuta do teclado e, quando o utilizador carregar
     * numa tecla correspondente a um atalho, seleciona automaticamente
     * a respetiva label.
     */
    useEffect(() => {
        const handleKeyDown = (event) => {
            const tag = document.activeElement?.tagName;

            // Evita atalhos enquanto o utilizador estiver a escrever
            if (tag === "INPUT" || tag === "TEXTAREA") return;

            const tecla = event.key.toUpperCase();

            const labelEncontrada = labelsComAtalho.find(
                (label) => label.shortcut === tecla
            );

            if (labelEncontrada) {
                setLabelSelecionada(labelEncontrada.nome);
            }
        };

        window.addEventListener("keydown", handleKeyDown);

        return () => {
            window.removeEventListener("keydown", handleKeyDown);
        };
    }, [labelsComAtalho]);

    // ── Selecionar texto numa frase ──────────────────────────────────────────
    const handleTextSelect = (e, frase) => {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;

        const range = selection.getRangeAt(0);
        const texto = selection.toString().trim();
        if (!texto) return;

        // Calcula offsets relativos ao texto da frase
        const preRange = range.cloneRange();
        preRange.selectNodeContents(e.currentTarget);
        preRange.setEnd(range.startContainer, range.startOffset);
        const inicio = preRange.toString().length;
        const fim = inicio + texto.length;

        setPendingSelection({fraseId: frase.id, inicio, fim, texto});
        setEntidadeSelecionada(null);
    };

    // ── Adicionar entidade manualmente ──────────────────────────────────────
    const handleUpdate = () => {
        if (!labelSelecionada) return alert("Seleciona um tipo de entidade.");
        if (!pendingSelection) return alert("Seleciona texto na notícia.");
        if (!noticia) return;

        const frase = noticia.frases.find((f) => f.id === pendingSelection.fraseId);
        if (!frase) return;

        const {inicio, fim, texto, fraseId} = pendingSelection;

        const overlap = frase.entidades.some((e) => inicio < e.fim && fim > e.inicio);
        if (overlap) return alert("A seleção sobrepõe-se a uma entidade existente.");

        const novasEntidades = [
            ...frase.entidades,
            {nome: texto, tipo: labelSelecionada, inicio, fim}
        ].sort((a, b) => a.inicio - b.inicio);

        atualizarFrase(fraseId, novasEntidades);
        setPendingSelection(null);
        window.getSelection()?.removeAllRanges();
    };

    // ── Remover entidade selecionada ─────────────────────────────────────────
    const handleRemover = () => {
        if (!entidadeSelecionada) return alert("Clica numa entidade para a selecionar.");
        if (!noticia) return;

        const {fraseId, index} = entidadeSelecionada;
        const frase = noticia.frases.find((f) => f.id === fraseId);
        if (!frase) return;

        const novasEntidades = frase.entidades.filter((_, i) => i !== index);
        atualizarFrase(fraseId, novasEntidades);
        setEntidadeSelecionada(null);
    };

    // ── Clicar numa entidade highlighted ────────────────────────────────────
    const handleEntidadeClick = (fraseId, index, entidade) => {
        setEntidadeSelecionada({fraseId, index, entidade});
        setLabelSelecionada(entidade.tipo);
        setPendingSelection(null);
    };

    return (
        <div className="app">
            <NewsList
                lista={lista}
                noticiaAtiva={noticia}
                onSelecionar={selecionar}
                onAdicionar={adicionarNoticia}
                isLoading={isLoading}
            />

            <main className="main-content">
                <h1>Criminal Entity Correlation</h1>

                <LabelBar
                    labels={labelsComAtalho}
                    labelSelecionada={labelSelecionada}
                    onSelecionar={setLabelSelecionada}
                />

                <ActionBar
                    labelSelecionada={labelSelecionada}
                    textoSelecionado={pendingSelection?.texto}
                    onUpdate={handleUpdate}
                    onRemover={handleRemover}
                    onGuardar={guardar}
                    isLoading={isLoading}
                />

                <ArticleViewer
                    noticia={noticia}
                    labelMap={labelMap}
                    fraseAtiva={fraseAtiva}
                    entidadeSelecionada={entidadeSelecionada}
                    onFraseClick={carregarGrafo}
                    onEntidadeClick={handleEntidadeClick}
                    onTextSelect={handleTextSelect}
                />
            </main>

            <GraphPanel
                key={fraseAtiva || 'empty'}
                grafo={grafo}
                grafoRelacionadas={grafoRelacionadas}
                labelMap={labelMap}
                isLoading={grafoLoading}
                isLoadingRelacionadas={isLoadingRelacionadas}
                onPesquisarRelacionadas={pesquisarRelacionadas}
            />
        </div>
    );
}