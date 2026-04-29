import { useState, useEffect } from "react";
import {
  getPasta, getNoticia, predictNoticia,
  guardarNoticia, apagarNoticia as apagarNoticiaApi,
} from "../api/client.jsx";

export function useNoticias(pastaId) {
  const [lista, setLista] = useState([]);
  const [noticia, setNoticia] = useState(null);
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
      // Adiciona à lista mas NÃO guarda no Neo4j ainda
      // O utilizador revê e clica em Guardar
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
      // Passa o pastaId para o backend ligar a notícia à pasta ao guardar
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
    selecionar, adicionarNoticia, guardar,
    apagarNoticia, atualizarFrase, removerDaLista,
  };
}