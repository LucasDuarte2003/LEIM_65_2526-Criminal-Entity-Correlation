import "./App.css";
import {useMemo, useRef, useState, useEffect} from "react";

function App() {
    const [newsList, setNewsList] = useState([]);
    const [selectedNewsId, setSelectedNewsId] = useState(null);
    const [selectedLabel, setSelectedLabel] = useState(null);
    const [selectedEntityIndex, setSelectedEntityIndex] = useState(null);
    const [pendingSelection, setPendingSelection] = useState(null);
    const [allLabels, setAllLabels] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const articleRef = useRef(null);

    // ─── Carrega notícias do backend ao iniciar ───────────────────────────────
    useEffect(() => {
        fetch("/api/noticias")
            .then((r) => r.json())
            .then((data) => {
                setNewsList(data);
                setSelectedNewsId(data[0]?.id || null);
                const labels = [...new Set(data.flatMap((n) => n.entities.map((e) => e.label)))];
                setAllLabels(labels);
            })
            .catch(() => console.error("Não foi possível ligar ao backend."));
    }, []);

    const selectedNews = useMemo(
        () => newsList.find((item) => item.id === selectedNewsId),
        [newsList, selectedNewsId]
    );

    // ─── Preview da sidebar ───────────────────────────────────────────────────
    const getPreview = (text) => text.split(" ").slice(0, 5).join(" ") + "...";

    // ─── Upload de .txt → backend → adiciona à lista ─────────────────────────
    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (event) => {
            const text = event.target.result;
            setIsLoading(true);

            try {
                const response = await fetch("/api/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({text}),
                });

                if (!response.ok) throw new Error("Erro no servidor");

                const noticia = await response.json();

                setNewsList((prev) => {
                    const updated = [...prev, noticia];
                    const labels = [...new Set(updated.flatMap((n) => n.entities.map((e) => e.label)))];
                    setAllLabels(labels);
                    return updated;
                });

                setSelectedNewsId(noticia.id);
            } catch (err) {
                alert("Erro ao processar a notícia. O backend está a correr?");
            } finally {
                setIsLoading(false);
                e.target.value = "";
            }
        };
        reader.readAsText(file, "utf-8");
    };

    // ─── Cálculo de offsets da seleção de texto ───────────────────────────────
    const getSelectionOffsets = () => {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return null;

        const range = selection.getRangeAt(0);
        if (range.collapsed) return null;
        if (!articleRef.current?.contains(range.commonAncestorContainer)) return null;

        const rawSelectedText = selection.toString();
        if (!rawSelectedText.trim()) return null;

        const preRange = range.cloneRange();
        preRange.selectNodeContents(articleRef.current);
        preRange.setEnd(range.startContainer, range.startOffset);

        const start = preRange.toString().length;
        const trimmedText = rawSelectedText.trim();
        const leadingSpaces = rawSelectedText.length - rawSelectedText.trimStart().length;
        const trailingSpaces = rawSelectedText.length - rawSelectedText.trimEnd().length;

        return {
            start: start + leadingSpaces,
            end: start + rawSelectedText.length - trailingSpaces,
            text: trimmedText,
        };
    };

    const handleTextMouseUp = () => setPendingSelection(getSelectionOffsets());

    // ─── Verificar sobreposição de entidades ──────────────────────────────────
    const hasOverlap = (newStart, newEnd, entities) =>
        entities.some((e) => newStart < e.end && newEnd > e.start);

    // ─── Adicionar entidade manualmente ──────────────────────────────────────
    const handleUpdate = () => {
        if (!selectedLabel) return alert("Seleciona um tipo de entidade primeiro.");
        if (!pendingSelection) return alert("Seleciona texto na notícia primeiro.");

        const {start, end, text} = pendingSelection;

        if (hasOverlap(start, end, selectedNews.entities))
            return alert("A seleção sobrepõe-se a uma entidade existente.");

        const newEntity = {start, end, text, label: selectedLabel};

        setNewsList((prev) =>
            prev.map((n) =>
                n.id !== selectedNews.id ? n : {
                    ...n,
                    entities: [...n.entities, newEntity].sort((a, b) => a.start - b.start),
                }
            )
        );

        setPendingSelection(null);
        setSelectedEntityIndex(null);
        window.getSelection()?.removeAllRanges();
    };

    // ─── Remover entidade selecionada ─────────────────────────────────────────
    const handleRemoveSelectedEntity = () => {
        if (selectedEntityIndex === null || !selectedNews) return;

        setNewsList((prev) =>
            prev.map((n) =>
                n.id !== selectedNews.id ? n : {
                    ...n,
                    entities: n.entities.filter((_, i) => i !== selectedEntityIndex),
                }
            )
        );
        setSelectedEntityIndex(null);
    };

    // ─── Renderizar texto com entidades destacadas ────────────────────────────
    const renderHighlightedText = (text, entities) => {
        const parts = [];
        let currentIndex = 0;
        const sorted = [...entities].sort((a, b) => a.start - b.start);

        sorted.forEach((entity, index) => {
            const entityText = entity.text?.trim();
            if (!entityText) return;

            const foundIndex = text.indexOf(entityText, currentIndex);
            if (foundIndex === -1) return;

            if (currentIndex < foundIndex)
                parts.push(<span key={`t-${index}`}>{text.slice(currentIndex, foundIndex)}</span>);

            parts.push(
                <span
                    key={`e-${index}`}
                    className={`highlight ${entity.label.toLowerCase()} ${
                        selectedEntityIndex === index ? "selected-entity" : ""
                    }`}
                    title={entity.label}
                    onClick={() => {
                        setSelectedLabel(entity.label);
                        setSelectedEntityIndex(index);
                    }}
                >
          {entityText}
        </span>
            );

            currentIndex = foundIndex + entityText.length;
        });

        if (currentIndex < text.length)
            parts.push(<span key="t-final">{text.slice(currentIndex)}</span>);

        return parts;
    };
    const handleSave = async () => {
        if (!selectedNews) return;

        try {
            const response = await fetch("/api/guardar", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    id: selectedNews.id,
                    text: selectedNews.text,
                    entities: selectedNews.entities,
                }),
            });

            if (!response.ok) throw new Error();
            alert("Notícia guardada com sucesso!");
        } catch {
            alert("Erro ao guardar. O backend está a correr?");
        }
    };
    // ─── Render ───────────────────────────────────────────────────────────────
    return (
        <div className="app">

            {/* Sidebar esquerda — lista de notícias */}
            <aside className="sidebar">
                <h2>Notícias</h2>

                <label className={`upload-btn ${isLoading ? "loading" : ""}`}>
                    {isLoading ? "A analisar..." : "+ Adicionar notícia"}
                    <input
                        type="file"
                        accept=".txt"
                        style={{display: "none"}}
                        onChange={handleFileUpload}
                        disabled={isLoading}
                    />
                </label>

                <div className="news-list">
                    {newsList.map((item) => (
                        <button
                            key={item.id}
                            className={`news-item ${selectedNews?.id === item.id ? "active" : ""}`}
                            onClick={() => {
                                setSelectedNewsId(item.id);
                                setPendingSelection(null);
                                setSelectedEntityIndex(null);
                            }}
                        >
                            {getPreview(item.text)}
                        </button>
                    ))}
                </div>
            </aside>

            {/* Painel central — texto anotado */}
            <main className="main-content">
                <h1>Criminal Entity Correlation</h1>

                {/* Barra de labels */}
                <div className="labels-bar">
                    {allLabels.map((label) => (
                        <button
                            key={label}
                            className={`label-chip ${label.toLowerCase()} ${
                                selectedLabel === label ? "active-chip" : ""
                            }`}
                            onClick={() => setSelectedLabel(label)}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {/* Barra de ações */}
                <div className="action-bar">
                    <p><strong>Tipo selecionado:</strong> {selectedLabel || "nenhum"}</p>
                    <p><strong>Texto selecionado:</strong> {pendingSelection ? `"${pendingSelection.text}"` : "nenhum"}
                    </p>
                    <button onClick={handleUpdate}>UPDATE</button>
                    <button onClick={handleRemoveSelectedEntity}>REMOVER ENTIDADE</button>
                    <button onClick={handleSave}>GUARDAR</button>
                    {/* ← novo */}
                </div>

                {/* Texto da notícia com highlights */}
                <div
                    className="news-full"
                    ref={articleRef}
                    onMouseUp={handleTextMouseUp}
                >
                    {selectedNews ? (
                        <p>{renderHighlightedText(selectedNews.text, selectedNews.entities)}</p>
                    ) : (
                        <p className="placeholder">Seleciona uma notícia ou adiciona uma nova.</p>
                    )}
                </div>
            </main>

            {/* Painel direito — Neo4j (reservado) */}
            <aside className="right-panel">
                <h2>Neo4j</h2>
                <div className="neo4j-placeholder">
                    Área reservada para o grafo e correlações.
                </div>
            </aside>

        </div>
    );
}

export default App;