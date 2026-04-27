import { useState, useEffect } from "react";
import {
  getPasta, getNoticia, predictNoticia,
  guardarNoticia, apagarNoticia as apagarNoticiaApi,
} from "../api/client";

export function useNoticias(pastaId) {
  const [lista, setLista] = useState([]);
  const [noticia, setNoticia] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [erro, setErro] = useState(null);

  // Carrega notícias da pasta ao montar ou quando pastaId muda
  useEffect(() => {
    if (!pastaId) return;
    getPasta("_", pastaId)
      .then((pasta) => setLista(pasta.noticias || []))
      .catch((e) => setErro(e.message));
  }, [pastaId]);

  const selecionar = async (id) => {
    setIsLoading(true);
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
    try {
      const nova = await predictNoticia(texto, pastaIdDestino);
      setLista((prev) => [...prev, { id: nova.id, titulo: nova.titulo }]);
      setNoticia(nova);
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
      await guardarNoticia(noticia);
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

  const removerDaLista = (id) => {
    setLista((prev) => prev.filter((n) => n.id !== id));
    if (noticia?.id === id) setNoticia(null);
  };

  return {
    lista, noticia, isLoading, erro,
    selecionar, adicionarNoticia, guardar, apagarNoticia, atualizarFrase,
  };
}
