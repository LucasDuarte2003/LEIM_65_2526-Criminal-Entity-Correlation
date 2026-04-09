# Criminal Entity Correlation (CEC)

Plataforma web para processamento e análise de notícias criminais. O sistema recebe artigos em texto, extrai automaticamente entidades nomeadas (pessoas, locais, organizações, crimes, etc.) usando um modelo de NER treinado em português, armazena as relações entre entidades numa base de dados de grafos Neo4j e permite a exploração visual dessas relações.

---

## Índice

1. [O que é este protótipo](#1-o-que-é-este-protótipo)
2. [Arquitetura do sistema](#2-arquitetura-do-sistema)
3. [Fluxo de dados](#3-fluxo-de-dados)
4. [Estrutura do projeto](#4-estrutura-do-projeto)
5. [Pré-requisitos](#5-pré-requisitos)
6. [Instalação e configuração](#6-instalação-e-configuração)
7. [Correr o projeto](#7-correr-o-projeto)
8. [Utilização da interface](#8-utilização-da-interface)
9. [API — referência de rotas](#9-api--referência-de-rotas)
10. [Modelo Neo4j — estrutura do grafo](#10-modelo-neo4j--estrutura-do-grafo)

---

## 1. O que é este protótipo

O CEC é composto por três componentes integrados:

**Protótipo NER** — Modelo de reconhecimento de entidades nomeadas baseado em `xlm-roberta-base`, treinado em artigos de notícias criminais em português. Reconhece 11 tipos de entidades: `PESSOA`, `LOCAL`, `ORGANIZACAO`, `CRIME`, `DATA`, `VIATURA`, `MATRICULA`, `TELEMOVEL`, `EMAIL`, `CRIPTO` e `MONTANTE`.

**Protótipo Neo4j** — Base de dados de grafos que armazena notícias, frases e entidades como nós, e as relações entre eles como arestas. As co-ocorrências são calculadas ao nível da frase, o que garante relações semânticamente relevantes.

**Protótipo Web** — Interface estilo Label Studio que permite carregar notícias, visualizar as entidades extraídas com destaque por cor, editar anotações manualmente e explorar o grafo de relações de cada frase.

---

## 2. Arquitetura do sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    React  (porta 5173)                           │
│                                                                  │
│   NewsList   ArticleViewer   LabelBar   ActionBar   GraphPanel  │
│       │             │            │           │           │       │
│       └─────────────┴────────────┴───────────┴───────────┘       │
│                              │                                   │
│                        api/client.js                             │
│                    (todas as chamadas HTTP)                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │  HTTP/JSON  (proxy Vite → :8000)
┌──────────────────────────────▼──────────────────────────────────┐
│                          BACKEND                                 │
│                   FastAPI  (porta 8000)                          │
│                                                                  │
│   api/noticias.py    api/labels.py    api/grafo.py              │
│          │                 │                │                    │
│          └─────────────────┴────────────────┘                    │
│                            │                                     │
│              services/                                           │
│   ┌──────────────┬─────────────────┬──────────────────┐         │
│   │ neo4j_service│   ner_service   │sentence_splitter │         │
│   │              │                 │  graph_builder   │         │
│   └──────┬───────┴────────┬────────┴──────────────────┘         │
└──────────┼────────────────┼────────────────────────────────────┘
           │                │
           │  Bolt (:7687)  │  Modelo carregado em memória
           │                │
┌──────────▼──────┐  ┌──────▼──────────────────────────────────┐
│   Neo4j (BD)    │  │          NER Model                       │
│   base de dados │  │   ner_model/saved_model/                 │
│   de grafos     │  │   xlm-roberta-base fine-tuned            │
└─────────────────┘  └─────────────────────────────────────────┘
```

### Comunicação entre camadas

| De | Para | Protocolo | O que é transmitido |
|---|---|---|---|
| Frontend | Backend | HTTP/JSON via proxy Vite | Pedidos REST (GET, POST, PUT) |
| Backend | Neo4j | Bolt (driver oficial Python) | Queries Cypher |
| Backend | NER Model | Chamada Python direta | Texto → lista de entidades |

O frontend nunca comunica diretamente com o Neo4j. Toda a lógica de acesso à base de dados está encapsulada em `services/neo4j_service.py`. O modelo NER é carregado uma vez em memória quando o backend arranca e é reutilizado em cada pedido de predição.

---

## 3. Fluxo de dados

### Carregar uma notícia existente

```
Utilizador clica numa notícia
        │
        ▼
Frontend: GET /api/noticias/{id}
        │
        ▼
Backend (api/noticias.py → neo4j_service.get_noticia)
        │
        ▼
Neo4j: MATCH (n:Noticia)-[:TEM_FRASE]->(f:Frase)
       MATCH (e:Entidade)-[:MENCIONADA_EM]->(f)
        │
        ▼
Backend devolve JSON com frases e entidades
        │
        ▼
Frontend: ArticleViewer renderiza texto com entidades destacadas por cor
```

### Adicionar uma nova notícia

```
Utilizador carrega ficheiro .txt
        │
        ▼
Frontend lê o ficheiro e envia: POST /api/noticias/predict { texto }
        │
        ▼
Backend (ner_service.run_ner)
  → modelo xlm-roberta processa o texto
  → devolve entidades com offsets de caracteres
        │
        ▼
Backend (sentence_splitter.split_sentences)
  → divide o texto em frases por . ! ?
  → cada frase tem id único, texto, ordem e offsets
        │
        ▼
Backend (graph_builder.assign_entities_to_sentences)
  → distribui cada entidade pela frase onde está contida
  → calcula co-ocorrências por frase (só entre tipos diferentes)
        │
        ▼
Backend (neo4j_service.save_noticia)
  → cria nó Noticia
  → cria nós Frase ligados por TEM_FRASE
  → cria/reutiliza nós Entidade ligados por MENCIONADA_EM
  → cria relações CO_OCORRE_COM entre entidades da mesma frase
        │
        ▼
Backend devolve a notícia criada
        │
        ▼
Frontend adiciona à lista e abre automaticamente
```

### Guardar edições manuais

```
Utilizador adiciona/remove entidades e clica Guardar
        │
        ▼
Frontend: PUT /api/noticias/{id} com o estado atual da notícia
        │
        ▼
Backend apaga as frases antigas dessa notícia no Neo4j
Backend recria as frases com as entidades editadas
        │
        ▼
Neo4j atualizado com as anotações corrigidas
```

### Ver o grafo de uma frase

```
Utilizador clica em ◉ numa frase
        │
        ▼
Frontend: GET /api/grafo/frase/{frase_id}
        │
        ▼
Neo4j: MATCH (a:Entidade)-[:CO_OCORRE_COM {frase_id}]->(b:Entidade)
        │
        ▼
Backend devolve { nos: [...], arestas: [...] }
        │
        ▼
Frontend: GraphPanel renderiza grafo interativo com react-force-graph-2d
Utilizador pode clicar num nó para o remover e ver as restantes relações
```

---

## 4. Estrutura do projeto

```
cec/
├── backend/
│   ├── main.py                  ← Entry point FastAPI, regista routers
│   ├── requirements.txt         ← Dependências Python
│   ├── .env                     ← Credenciais Neo4j (não vai ao git)
│   ├── seed.py                  ← Popula Neo4j a partir do dataset_anotado.json
│   │
│   ├── api/                     ← Rotas HTTP (só definem endpoints)
│   │   ├── noticias.py
│   │   ├── labels.py
│   │   └── grafo.py
│   │
│   ├── services/                ← Lógica de negócio
│   │   ├── neo4j_service.py     ← Todas as queries ao Neo4j
│   │   ├── ner_service.py       ← Wrapper do modelo NER
│   │   ├── sentence_splitter.py ← Divide texto em frases
│   │   └── graph_builder.py     ← Calcula co-ocorrências por frase
│   │
│   ├── models/
│   │   └── schemas.py           ← Tipos Pydantic (validação de dados)
│   │
│   └── ner_model/               ← Modelo NER treinado
│       ├── saved_model/         ← Pesos do modelo (não vão ao git)
│       ├── predict.py
│       ├── train.py
│       └── data/
│           ├── labels.py
│           └── dataset_anotado.json
│
└── frontend/
    ├── vite.config.js           ← Proxy /api → localhost:8000
    └── src/
        ├── api/
        │   └── client.js        ← Todas as chamadas fetch centralizadas
        ├── hooks/
        │   ├── useNoticias.js   ← Estado e lógica de notícias
        │   ├── useLabels.js     ← Estado e lógica de labels/cores
        │   └── useGrafo.js      ← Estado e lógica do grafo
        └── components/
            ├── NewsList.jsx     ← Sidebar com lista de notícias
            ├── ArticleViewer.jsx← Texto com entidades destacadas
            ├── LabelBar.jsx     ← Chips de labels com cores da BD
            ├── ActionBar.jsx    ← Botões de ação
            └── GraphPanel.jsx   ← Grafo interativo de relações
```

---

## 5. Pré-requisitos

Antes de instalar, certifica-te de que tens o seguinte:

| Ferramenta | Versão mínima | Para quê |
|---|---|---|
| Python | 3.10+ | Backend e modelo NER |
| Node.js | 18+ | Frontend React |
| Neo4j Desktop | 2.x | Base de dados de grafos |
| Git | qualquer | Clonar o repositório |

---

## 6. Instalação e configuração

### 6.1 Clonar o repositório

```bash
git clone https://github.com/<utilizador>/<repositorio>.git
cd <repositorio>/01_Analise/Protótipos/cec
```

### 6.2 Configurar o Neo4j

1. Abre o **Neo4j Desktop**
2. Clica em **Local instances** → **Create instance**
3. Dá o nome `cec-db`, define uma password e clica em **Create**
4. Clica em **Start** para arrancar a instância
5. Clica em **Create database** → dá o nome `cec`

### 6.3 Configurar o backend

```bash
cd backend

# Criar e ativar ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

Cria o ficheiro `.env` dentro de `backend/` com as credenciais do Neo4j:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<a_tua_password>
```

> ⚠️ O ficheiro `.env` nunca deve ser enviado para o repositório. Cada pessoa cria o seu próprio com as suas credenciais locais.

### 6.4 Copiar o modelo NER

O modelo treinado não está no repositório (ficheiros demasiado grandes). Copia a pasta `saved_model/` de quem te forneceu o projeto para `backend/ner_model/saved_model/`.

A estrutura deve ficar assim:

```
backend/ner_model/saved_model/
├── config.json
├── model.safetensors
├── tokenizer.json
└── tokenizer_config.json
```

### 6.5 Popular a base de dados

Com o Neo4j a correr e o venv ativo:

```bash
cd backend
python seed.py
```

Este script lê o `dataset_anotado.json`, processa cada notícia, divide em frases, distribui entidades e popula o Neo4j. Só precisas de correr uma vez — ou sempre que o dataset mudar.

Output esperado:

```
Grafo limpo.
Labels inicializadas.
  ✓ 15-2026 — 47 frases, 127 entidades
  ✓ 12-919  — 31 frases, 47 entidades
  ...
Base de dados populada com sucesso!
```

### 6.6 Configurar o frontend

```bash
cd ../frontend
npm install
```

---

## 7. Correr o projeto

É necessário ter **três serviços a correr em simultâneo**:

### Ordem de arranque (importante)

```
1. Neo4j Desktop  →  instância cec-db no estado RUNNING
2. Backend        →  uvicorn
3. Frontend       →  vite
```

### Terminal 1 — Backend

```bash
cd backend
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

uvicorn main:app --reload --port 8000
```

Quando estiver pronto:
```
CEC API pronta.
INFO: Uvicorn running on http://127.0.0.1:8000
```

Podes verificar as rotas disponíveis em: `http://localhost:8000/docs`

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

Quando estiver pronto:
```
VITE ready in Xms
➜ Local: http://localhost:5173/
```

Abre o browser em `http://localhost:5173`.

---

## 8. Utilização da interface

### Navegar entre notícias
Clica em qualquer notícia na barra lateral esquerda. O texto aparece no painel central com as entidades destacadas por cor.

### Perceber as cores
Cada tipo de entidade tem uma cor própria que vem da base de dados. Passa o rato por cima de uma entidade destacada para ver o seu tipo.

### Adicionar uma entidade manualmente
1. Clica no tipo de entidade que queres na barra de labels (ex: `PESSOA`)
2. Seleciona o texto na notícia com o rato
3. Clica em **Adicionar entidade**

### Remover uma entidade
1. Clica sobre a entidade destacada no texto — fica selecionada
2. Clica em **Remover entidade**

### Guardar alterações
Clica em **Guardar**. As edições são enviadas ao backend e guardadas no Neo4j. Sem clicar Guardar, as alterações existem apenas em memória e perdem-se ao mudar de notícia.

### Ver o grafo de relações
Clica no botão **◉** que aparece antes de cada frase. O painel direito mostra as entidades dessa frase como nós ligados entre si. Clica num nó para o remover e ver como as restantes relações se reorganizam. Clica em **Repor** para restaurar todos os nós.

### Adicionar uma nova notícia
Clica em **+ Adicionar notícia** na sidebar, seleciona um ficheiro `.txt` com o texto da notícia. O modelo NER processa automaticamente o texto e a notícia aparece na lista com as entidades extraídas.

---

## 9. API — referência de rotas

Base URL: `http://localhost:8000`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/noticias/` | Lista todas as notícias (id + título) |
| GET | `/api/noticias/{id}` | Notícia completa com frases e entidades |
| POST | `/api/noticias/predict` | Processa texto com NER e guarda na BD |
| PUT | `/api/noticias/{id}` | Guarda edições manuais de uma notícia |
| GET | `/api/labels/` | Lista de labels com cores |
| GET | `/api/grafo/frase/{id}` | Nós e arestas de uma frase para o grafo |

A documentação interativa completa (Swagger UI) está disponível em `http://localhost:8000/docs`.

---

## 10. Modelo Neo4j — estrutura do grafo

```
(:Noticia {id, titulo})
       │
       [:TEM_FRASE {ordem}]
       ▼
(:Frase {id, texto, ordem, noticia_id})
       │
       [:MENCIONADA_EM {inicio, fim}]
       ▼
(:Entidade {nome, tipo})
       │
       [:CO_OCORRE_COM {frase_id}]
       │
(:Entidade)

(:Label {nome, cor})
```

### Nós

| Label | Propriedades | Descrição |
|---|---|---|
| `Noticia` | `id`, `titulo` | Artigo de notícia |
| `Frase` | `id`, `texto`, `ordem`, `noticia_id` | Frase dentro de uma notícia |
| `Entidade` | `nome`, `tipo` | Entidade nomeada (pessoa, local, etc.) |
| `Label` | `nome`, `cor` | Tipo de entidade com cor associada |

### Relações

| Relação | De → Para | Propriedades | Significado |
|---|---|---|---|
| `TEM_FRASE` | Noticia → Frase | — | Notícia contém esta frase |
| `MENCIONADA_EM` | Entidade → Frase | `inicio`, `fim` | Entidade aparece nesta frase com estes offsets |
| `CO_OCORRE_COM` | Entidade → Entidade | `frase_id` | Duas entidades de tipos diferentes na mesma frase |

### Queries úteis para exploração

```cypher
-- Resumo geral da BD
MATCH (n) RETURN labels(n) AS tipo, count(n) AS total

-- Entidades de uma notícia específica
MATCH (e:Entidade)-[:MENCIONADA_EM]->(f:Frase)-[:TEM_FRASE]-(n:Noticia {id: "15-2026"})
RETURN DISTINCT e.nome, e.tipo

-- Pessoas que aparecem em mais de uma notícia
MATCH (p:Entidade {tipo: "PESSOA"})-[:MENCIONADA_EM]->(f:Frase)
WITH p, count(DISTINCT f.noticia_id) AS noticias
WHERE noticias > 1
RETURN p.nome, noticias ORDER BY noticias DESC

-- Grafo de co-ocorrências de uma pessoa
MATCH (p:Entidade {nome: "João Silva"})-[:CO_OCORRE_COM]-(outro)
RETURN p, outro LIMIT 30
```