import { useState } from "react";
import { getGrafoFrase } from "../api/client";

export function useGrafo() {
  const [grafo, setGrafo] = useState(null);   // { nos: [], arestas: [] }
  const [fraseAtiva, setFraseAtiva] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const carregarGrafo = async (fraseId) => {
    if (fraseAtiva === fraseId) {
      // Clicou na mesma frase — fecha o grafo
      setGrafo(null);
      setFraseAtiva(null);
      return;
    }
    setIsLoading(true);
    try {
      const data = await getGrafoFrase(fraseId);
      setGrafo(data);
      setFraseAtiva(fraseId);
    } catch {
      // Frase sem relações — mostra grafo vazio
      setGrafo({ nos: [], arestas: [] });
      setFraseAtiva(fraseId);
    } finally {
      setIsLoading(false);
    }
  };

  const limparGrafo = () => {
    setGrafo(null);
    setFraseAtiva(null);
  };

  return { grafo, fraseAtiva, isLoading, carregarGrafo, limparGrafo };
}