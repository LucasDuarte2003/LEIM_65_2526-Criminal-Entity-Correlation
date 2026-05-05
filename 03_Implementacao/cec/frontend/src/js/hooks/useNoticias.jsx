import { useState, useEffect } from "react";
import {
  getPasta, getNoticia, predictNoticia,
  guardarNoticia, apagarNoticia as apagarNoticiaApi,
} from "../api/client.jsx";

export function useNoticias(pastaId) {
  const [lista, setLista] = useState([]);
  const [noticia, setNoticia] = useState(null);
  const [frasesGliner, setFrasesGliner] = useState(null); // só preenchido no modo "ambos"
  const [isLoading, setIsLoading] = useState(false);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    if (!pastaId) return;
    getPasta("_", pastaId)
      .then((pasta) => setLista(pasta.noticias || []))
      .catch((e) => setErro(e.message));
  }, [pastaId]);

  const selecionar = async (id) => {
    setIsLoading(true);
    setFrasesGliner(null);
    try {
      const data = await getNoticia(id);
      setNoticia(data);
    } catch (e) {
      setErro(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const adicionarNoticia = async (texto, pastaIdDestino) => {
    setIsLoading(true);
    setFrasesGliner(null);
    const modo = localStorage.getItem("modoExtracao") || "xlm-roberta";
    try {
      const nova = await predictNoticia(texto, pastaIdDestino, modo);
      if (nova.modo === "ambos") {
        // Notícia base usa frases do xlm, guardamos gliner separado
        const noticiaBase = { id: nova.id, titulo: nova.titulo, frases: nova.frases };
        setFrasesGliner(nova.frases_gliner);
        setLista((prev) => [...prev, { id: nova.id, titulo: nova.titulo }]);
        setNoticia(noticiaBase);
      } else {
        setLista((prev) => [...prev, { id: nova.id, titulo: nova.titulo }]);
        setNoticia(nova);
      }
    } catch (e) {
      setErro(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const guardar = async (onSucesso) => {
    if (!noticia) return;
    setIsLoading(true);
    try {
      await guardarNoticia({ ...noticia, pasta_id: pastaId });
      alert("Notícia guardada com sucesso!");
      if (onSucesso) onSucesso();
    } catch (e) {
      setErro(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const apagarNoticia = async (id) => {
    setIsLoading(true);
    try {
      await apagarNoticiaApi(id);
      setLista((prev) => prev.filter((n) => n.id !== id));
      setNoticia(null);
      setFrasesGliner(null);
    } catch (e) {
      setErro(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const atualizarFrase = (fraseId, novasEntidades) => {
    setNoticia((prev) => ({
      ...prev,
      frases: prev.frases.map((f) =>
        f.id === fraseId ? { ...f, entidades: novasEntidades } : f
      ),
    }));
  };

  const atualizarFraseGliner = (fraseId, novasEntidades) => {
    setFrasesGliner((prev) =>
      prev.map((f) => f.id === fraseId ? { ...f, entidades: novasEntidades } : f)
    );
  };

  const removerDaLista = (id) => {
    setLista((prev) => prev.filter((n) => n.id !== id));
    if (noticia?.id === id) { setNoticia(null); setFrasesGliner(null); }
  };

  // Muda as frases da notícia para as do modelo selecionado
  const mudarParaModelo = (modelo) => {
    if (!noticia || !frasesGliner) return;
    if (modelo === "gliner") {
      setNoticia((prev) => ({ ...prev, frases: frasesGliner }));
      setFrasesGliner(noticia.frases);
    }
    // "xlm-roberta" já está em noticia.frases — não é preciso fazer nada
  };

  return {
    lista, noticia, frasesGliner, isLoading, erro,
    selecionar, adicionarNoticia, guardar,
    apagarNoticia, atualizarFrase, atualizarFraseGliner,
    removerDaLista, mudarParaModelo,
  };
}