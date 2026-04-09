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
  return res.json();
}

// --- Notícias ---

export const getNoticias = () =>
  request("/noticias/");

export const getNoticia = (id) =>
  request(`/noticias/${id}`);

export const predictNoticia = (texto) =>
  request("/noticias/predict", {
    method: "POST",
    body: JSON.stringify({ texto }),
  });

export const guardarNoticia = (noticia) =>
  request(`/noticias/${noticia.id}`, {
    method: "PUT",
    body: JSON.stringify(noticia),
  });

// --- Labels ---

export const getLabels = () =>
  request("/labels/");

// --- Grafo ---

export const getGrafoFrase = (fraseId) =>
  request(`/grafo/frase/${fraseId}`);