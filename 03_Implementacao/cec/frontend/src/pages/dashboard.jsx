import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
    getProjetos, getProjeto, criarProjeto, atualizarProjeto, eliminarProjeto,
    criarPasta, atualizarPasta, eliminarPasta, getModeloStatus, retreinarModelo, alterarTipoModelo
} from "../js/api/client.jsx";
import { useTheme } from "../js/hooks/useTheme.jsx";
import "../static/css/dashboard.css";

export default function Dashboard() {
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();

    const [projetos, setProjetos] = useState([]);
    const [projetoExpandido, setProjetoExpandido] = useState(null);
    const [projetosCompletos, setProjetosCompletos] = useState({});

    const [modalProjeto, setModalProjeto] = useState(null);
    const [modalPasta, setModalPasta] = useState(null);
    const [inputNome, setInputNome] = useState("");
    const [inputDesc, setInputDesc] = useState("");

    const [modeloStatus, setModeloStatus] = useState(null);

    const carregar = () =>
        getProjetos().then(setProjetos).catch(console.error);

    useEffect(() => {
        carregar();
    }, []);

    const toggleProjeto = async (projetoId) => {
        if (projetoExpandido === projetoId) {
            setProjetoExpandido(null);
            return;
        }
        setProjetoExpandido(projetoId);
        if (!projetosCompletos[projetoId]) {
            const completo = await getProjeto(projetoId);
            setProjetosCompletos((prev) => ({ ...prev, [projetoId]: completo }));
        }
    };

    const recarregarProjeto = async (projetoId) => {
        const completo = await getProjeto(projetoId);
        setProjetosCompletos((prev) => ({ ...prev, [projetoId]: completo }));
        carregar();
    };

    const abrirCriarProjeto = () => {
        setInputNome("");
        setInputDesc("");
        setModalProjeto("criar");
    };

    const abrirEditarProjeto = (proj) => {
        setInputNome(proj.nome);
        setInputDesc(proj.descricao || "");
        setModalProjeto(proj);
    };

    const confirmarProjeto = async () => {
        if (!inputNome.trim()) return;
        if (modalProjeto === "criar") {
            await criarProjeto(inputNome.trim(), inputDesc.trim() || null);
        } else {
            await atualizarProjeto(modalProjeto.id, inputNome.trim(), inputDesc.trim() || null);
            setProjetosCompletos((prev) => {
                const c = { ...prev };
                delete c[modalProjeto.id];
                return c;
            });
        }
        setModalProjeto(null);
        carregar();
    };

    const confirmarEliminarProjeto = async (id) => {
        if (!confirm("Eliminar este projeto? As notícias não serão apagadas.")) return;
        await eliminarProjeto(id);
        if (projetoExpandido === id) setProjetoExpandido(null);
        setProjetosCompletos((prev) => {
            const c = { ...prev };
            delete c[id];
            return c;
        });
        carregar();
    };

    const abrirCriarPasta = (projetoId) => {
        setInputNome("");
        setModalPasta({ tipo: "criar", projetoId });
    };

    const abrirEditarPasta = (projetoId, pasta) => {
        setInputNome(pasta.nome);
        setModalPasta({ tipo: "editar", projetoId, id: pasta.id });
    };

    const confirmarPasta = async () => {
        if (!inputNome.trim()) return;
        if (modalPasta.tipo === "criar") {
            await criarPasta(modalPasta.projetoId, inputNome.trim());
        } else {
            await atualizarPasta(modalPasta.projetoId, modalPasta.id, inputNome.trim());
        }
        const projetoId = modalPasta.projetoId;
        setModalPasta(null);
        recarregarProjeto(projetoId);
    };

    const confirmarEliminarPasta = async (projetoId, pastaId) => {
        if (!confirm("Eliminar esta pasta? As notícias não serão apagadas.")) return;
        await eliminarPasta(projetoId, pastaId);
        recarregarProjeto(projetoId);
    };

    const abrirPasta = (projetoId, pastaId) => {
        navigate(`/projeto/${projetoId}/pasta/${pastaId}`);
    };

    useEffect(() => {
        const carregar = () =>
            getModeloStatus().then(setModeloStatus).catch(console.error);
        carregar();
        const intervalo = setInterval(carregar, 5000);
        return () => clearInterval(intervalo);
    }, []);

    const handleRetreinar = async () => {
        await retreinarModelo();
        alert("Retreino iniciado em background.");
    };

    const [modoExtracao, setModoExtracao] = useState(
        () => localStorage.getItem("modoExtracao") || "ambos"
    );


    const handleAlterarModo = (tipo) => {
        setModoExtracao(tipo);
        localStorage.setItem("modoExtracao", tipo);

        if (tipo !== "ambos") {
            alterarTipoModelo(tipo);
            setModeloStatus((prev) => ({ ...prev, tipo }));
        }
    };

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <h1>Criminal Entity Correlation</h1>

                <div className="dashboard-header-actions">
                    <button className="btn-theme-toggle" onClick={toggleTheme}>
                        {theme === "dark" ? "Modo claro" : "Modo escuro"}
                    </button>

                    <button className="btn-novo-projeto" onClick={abrirCriarProjeto}>
                        + Novo projeto
                    </button>
                </div>
            </header>

            <main className="dashboard-main">
                {projetos.length === 0 && (
                    <p className="dashboard-empty">Nenhum projeto ainda. Cria o primeiro para começar.</p>
                )}

                {projetos.map((proj) => {
                    const pastas = projetosCompletos[proj.id]?.pastas || [];
                    return (
                        <div key={proj.id} className="projeto-card">
                            <div className="projeto-card-header" onClick={() => toggleProjeto(proj.id)}>
                                <div className="projeto-info">
                                    <span className="projeto-nome">{proj.nome}</span>
                                    {proj.descricao && <span className="projeto-desc">{proj.descricao}</span>}
                                </div>
                                <div className="projeto-meta">
                                    <span>{proj.total_pastas} pasta{proj.total_pastas !== 1 ? "s" : ""}</span>
                                    <span>{proj.total_noticias} notícia{proj.total_noticias !== 1 ? "s" : ""}</span>
                                    <button className="btn-icon" onClick={(e) => {
                                        e.stopPropagation();
                                        abrirEditarProjeto(proj);
                                    }} title="Editar">✏️</button>
                                    <button className="btn-icon btn-danger" onClick={(e) => {
                                        e.stopPropagation();
                                        confirmarEliminarProjeto(proj.id);
                                    }} title="Eliminar">🗑</button>
                                    <span className="projeto-chevron">{projetoExpandido === proj.id ? "▲" : "▼"}</span>
                                </div>
                            </div>

                            {projetoExpandido === proj.id && (
                                <div className="projeto-pastas">
                                    {pastas.length === 0 &&
                                        <p className="pastas-empty">Sem pastas. Cria a primeira.</p>}
                                    {pastas.map((pasta) => (
                                        <div key={pasta.id} className="pasta-row">
                                            <button className="pasta-btn" onClick={() => abrirPasta(proj.id, pasta.id)}>
                                                <span className="pasta-icon">📁</span>
                                                <span className="pasta-nome">{pasta.nome}</span>
                                                <span className="pasta-count">
                                                    {pasta.total_noticias} notícia{pasta.total_noticias !== 1 ? "s" : ""}
                                                </span>
                                            </button>
                                            <button className="btn-icon"
                                                    onClick={() => abrirEditarPasta(proj.id, pasta)}
                                                    title="Editar">✏️</button>
                                            <button className="btn-icon btn-danger"
                                                    onClick={() => confirmarEliminarPasta(proj.id, pasta.id)}
                                                    title="Eliminar">🗑</button>
                                        </div>
                                    ))}
                                    <button className="btn-nova-pasta" onClick={() => abrirCriarPasta(proj.id)}>
                                        + Nova pasta
                                    </button>
                                </div>
                            )}
                        </div>
                    );
                })}

                <div className="modelo-painel">
                    <h2>Modelo NER</h2>
                    {modeloStatus ? (
                        <>
                            <div className="modelo-info">
                                <span>Modelo ativo:</span>
                                <strong>{modoExtracao === "ambos" ? "ambos" : modeloStatus.tipo}</strong>
                            </div>
                            <div className="modelo-info">
                                <span>Último treino:</span>
                                <strong>{modeloStatus.ultimo_treino ?? "Nunca"}</strong>
                            </div>
                            <div className="modelo-info">
                                <span>Estado:</span>
                                <strong className={modeloStatus.a_treinar ? "estado-treino" : "estado-ok"}>
                                    {modeloStatus.a_treinar ? "A retreinar..." : "Disponível"}
                                </strong>
                            </div>
                            <div className="modelo-botoes">
                            <select className="select-modelo" value={modoExtracao}
                                onChange={(e) => handleAlterarModo(e.target.value)}
                                disabled={modeloStatus?.a_treinar}>
                              <option value="ambos">Ambos os modelos</option>
                              <option value="xlm-roberta">Só XLM-RoBERTa</option>
                              <option value="gliner">Só GLiNER</option>
                            </select>
                                <button
                                    className="btn-retreinar"
                                    onClick={handleRetreinar}
                                    disabled={modeloStatus?.a_treinar}
                                >
                                    {modeloStatus?.a_treinar ? "A retreinar..." : "Retreinar agora"}
                                </button>
                            </div>
                        </>
                    ) : (
                        <p className="pastas-empty">A carregar estado do modelo...</p>
                    )}
                </div>
            </main>

            {modalProjeto && (
                <div className="modal-overlay" onClick={() => setModalProjeto(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <h2>{modalProjeto === "criar" ? "Novo projeto" : "Editar projeto"}</h2>
                        <label>Nome</label>
                        <input autoFocus value={inputNome} onChange={(e) => setInputNome(e.target.value)}
                               onKeyDown={(e) => e.key === "Enter" && confirmarProjeto()}
                               placeholder="Nome do projeto" />
                        <label>Descrição (opcional)</label>
                        <input value={inputDesc} onChange={(e) => setInputDesc(e.target.value)}
                               placeholder="Descrição" />
                        <div className="modal-actions">
                            <button className="btn-cancelar" onClick={() => setModalProjeto(null)}>Cancelar</button>
                            <button className="btn-confirmar" onClick={confirmarProjeto}>
                                {modalProjeto === "criar" ? "Criar" : "Guardar"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalPasta && (
                <div className="modal-overlay" onClick={() => setModalPasta(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <h2>{modalPasta.tipo === "criar" ? "Nova pasta" : "Editar pasta"}</h2>
                        <label>Nome</label>
                        <input autoFocus value={inputNome} onChange={(e) => setInputNome(e.target.value)}
                               onKeyDown={(e) => e.key === "Enter" && confirmarPasta()}
                               placeholder="Nome da pasta" />
                        <div className="modal-actions">
                            <button className="btn-cancelar" onClick={() => setModalPasta(null)}>Cancelar</button>
                            <button className="btn-confirmar" onClick={confirmarPasta}>
                                {modalPasta.tipo === "criar" ? "Criar" : "Guardar"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
