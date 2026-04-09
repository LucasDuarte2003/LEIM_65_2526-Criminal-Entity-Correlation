import { useState, useEffect } from "react";
import { getNoticias, getNoticia, predictNoticia, guardarNoticia } from "../api/client";

export function useNoticias() {
  const [lista, setLista] = useState([]);
  const [noticia, setNoticia] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    getNoticias()
      .then(setLista)
      .catch((e) => setErro(e.message));
  }, []);

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

  const adicionarNoticia = async (texto) => {
    setIsLoading(true);
    try {
      const nova = await predictNoticia(texto);
      setLista((prev) => [...prev, { id: nova.id, titulo: nova.titulo }]);
      setNoticia(nova);
    } catch (e) {
      setErro(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const guardar = async () => {
    if (!noticia) return;
    setIsLoading(true);
    try {
      await guardarNoticia(noticia);
      alert("Notícia guardada com sucesso!");
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

  return {
    lista,
    noticia,
    isLoading,
    erro,
    selecionar,
    adicionarNoticia,
    guardar,
    atualizarFrase,
  };
}