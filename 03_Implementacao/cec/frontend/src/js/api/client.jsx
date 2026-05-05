const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erro ${res.status}`);
  }
  // 204 No Content não tem body
  if (res.status === 204) return null;
  return res.json();
}

// ── Notícias ────────────────────────────────────────────────────

export const getNoticias = () =>
  request("/noticias/");

export const getNoticia = (id) =>
  request(`/noticias/${id}`);

export const predictNoticia = (texto, pastaId, modo = "xlm-roberta") =>
  request("/noticias/predict", {
    method: "POST",
    body: JSON.stringify({ texto, pasta_id: pastaId, modo }),
  });

export const guardarNoticia = (noticia) =>
  request(`/noticias/${noticia.id}`, {
    method: "PUT",
    body: JSON.stringify(noticia),
  });

export const apagarNoticia = (id) =>
  request(`/noticias/${id}`, { method: "DELETE" });

// ── Labels ──────────────────────────────────────────────────────

export const getLabels = () =>
  request("/labels/");

// ── Grafo ───────────────────────────────────────────────────────

export const getGrafoFrase = (fraseId) =>
  request(`/grafo/frase/${fraseId}`);

export const getGrafoRelacionadas = (fraseId, nos, ambito = "global") =>
  request(`/grafo/frase/${fraseId}/relacionadas`, {
    method: "POST",
    body: JSON.stringify({ nos, ambito }),
  });

// ── Projetos ────────────────────────────────────────────────────

export const getProjetos = () =>
  request("/projetos/");

export const getProjeto = (id) =>
  request(`/projetos/${id}`);

export const criarProjeto = (nome, descricao) =>
  request("/projetos/", {
    method: "POST",
    body: JSON.stringify({ nome, descricao }),
  });

export const atualizarProjeto = (id, nome, descricao) =>
  request(`/projetos/${id}`, {
    method: "PUT",
    body: JSON.stringify({ nome, descricao }),
  });

export const eliminarProjeto = (id) =>
  request(`/projetos/${id}`, { method: "DELETE" });

// ── Pastas ──────────────────────────────────────────────────────

export const getPasta = (projetoId, pastaId) =>
  request(`/projetos/${projetoId}/pastas/${pastaId}`);

export const criarPasta = (projetoId, nome) =>
  request(`/projetos/${projetoId}/pastas`, {
    method: "POST",
    body: JSON.stringify({ nome, projeto_id: projetoId }),
  });

export const atualizarPasta = (projetoId, pastaId, nome) =>
  request(`/projetos/${projetoId}/pastas/${pastaId}`, {
    method: "PUT",
    body: JSON.stringify({ nome }),
  });

export const eliminarPasta = (projetoId, pastaId) =>
  request(`/projetos/${projetoId}/pastas/${pastaId}`, { method: "DELETE" });


export const getTodasAsPastas = () =>
  request("/projetos/todas-as-pastas");

export const moverNoticia = (noticiaId, pastaIdDestino) =>
  request(`/noticias/${noticiaId}/mover`, {
    method: "PUT",
    body: JSON.stringify({ pasta_id_destino: pastaIdDestino }),
  });

export const getGrafoFundido = (fraseIds) =>
  request("/grafo/frases/fundir", {
    method: "POST",
    body: JSON.stringify({ frase_ids: fraseIds }),
  });

// ── Modelo ──────────────────────────────────────────────────────

export const getModeloStatus = () =>
  request("/modelo/status");

export const retreinarModelo = () =>
  request("/modelo/retreinar", { method: "POST" });

export const alterarTipoModelo = (tipo) =>
  request("/modelo/tipo", {
    method: "POST",
    body: JSON.stringify({ tipo }),
  });

export const getNoticias_semelhantes = (noticiaId) =>
  request(`/noticias/${noticiaId}/semelhantes`);
