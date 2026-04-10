import { useState } from "react";
import { getGrafoFrase, getGrafoRelacionadas } from "../api/client";

export function useGrafo() {
  const [grafo, setGrafo] = useState(null);
  const [grafoRelacionadas, setGrafoRelacionadas] = useState(null);
  const [fraseAtiva, setFraseAtiva] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRelacionadas, setIsLoadingRelacionadas] = useState(false);

  const carregarGrafo = async (fraseId) => {
    if (fraseAtiva === fraseId) {
      setGrafo(null);
      setFraseAtiva(null);
      setGrafoRelacionadas(null);
      return;
    }
    setIsLoading(true);
    setGrafoRelacionadas(null);
    try {
      const data = await getGrafoFrase(fraseId);
      setGrafo(data);
      setFraseAtiva(fraseId);
    } catch {
      setGrafo({ nos: [], arestas: [] });
      setFraseAtiva(fraseId);
    } finally {
      setIsLoading(false);
    }
  };

  const pesquisarRelacionadas = async (nosVisiveis) => {
    if (!fraseAtiva || nosVisiveis.length === 0) return;
    setIsLoadingRelacionadas(true);
    try {
      const data = await getGrafoRelacionadas(fraseAtiva, nosVisiveis);
      setGrafoRelacionadas(data);
    } catch {
      setGrafoRelacionadas({ nos: [], arestas: [], tem_resultados: false });
    } finally {
      setIsLoadingRelacionadas(false);
    }
  };

  const limparGrafo = () => {
    setGrafo(null);
    setFraseAtiva(null);
    setGrafoRelacionadas(null);
  };

  return {
    grafo,
    grafoRelacionadas,
    fraseAtiva,
    isLoading,
    isLoadingRelacionadas,
    carregarGrafo,
    pesquisarRelacionadas,
    limparGrafo,
  };
}