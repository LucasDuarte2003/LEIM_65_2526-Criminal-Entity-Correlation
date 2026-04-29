import { useState } from "react";
import { getGrafoFrase, getGrafoRelacionadas, getGrafoFundido } from "../api/client.jsx";

export function useGrafo() {
  const [grafo, setGrafo] = useState(null);
  const [grafoRelacionadas, setGrafoRelacionadas] = useState(null);
  const [fraseAtiva, setFraseAtiva] = useState(null);
  const [fraseFundida, setFraseFundida] = useState(null); // id da segunda frase
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRelacionadas, setIsLoadingRelacionadas] = useState(false);

  const carregarGrafo = async (fraseId) => {
    if (fraseAtiva === fraseId) {
      setGrafo(null);
      setFraseAtiva(null);
      setFraseFundida(null);
      setGrafoRelacionadas(null);
      return;
    }
    setIsLoading(true);
    setGrafoRelacionadas(null);
    setFraseFundida(null);
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

  const fundirFrase = async (fraseId) => {
    if (!fraseAtiva) return;
    // Se clicar na frase já fundida, desfaz a fusão
    if (fraseFundida === fraseId) {
      setFraseFundida(null);
      setGrafoRelacionadas(null);
      const data = await getGrafoFrase(fraseAtiva);
      setGrafo(data);
      return;
    }
    setIsLoading(true);
    setGrafoRelacionadas(null);
    try {
      const data = await getGrafoFundido([fraseAtiva, fraseId]);
      setGrafo(data);
      setFraseFundida(fraseId);
    } catch {
      setGrafo({ nos: [], arestas: [] });
    } finally {
      setIsLoading(false);
    }
  };

  const pesquisarRelacionadas = async (nosVisiveis, ambito = "global") => {
    if (!fraseAtiva || nosVisiveis.length === 0) return;
    setIsLoadingRelacionadas(true);
    try {
      const data = await getGrafoRelacionadas(fraseAtiva, nosVisiveis, ambito);
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
    setFraseFundida(null);
    setGrafoRelacionadas(null);
  };

  const limparRelacionadas = () => {
    setGrafoRelacionadas(null);
  };

  return {
    grafo,
    grafoRelacionadas,
    fraseAtiva,
    fraseFundida,
    isLoading,
    isLoadingRelacionadas,
    carregarGrafo,
    fundirFrase,
    pesquisarRelacionadas,
    limparGrafo,
    limparRelacionadas,
  };
}
