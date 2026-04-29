# Criminal Entity Correlation (CEC)

Plataforma web para processamento e análise de notícias criminais. O sistema recebe artigos em texto, extrai
automaticamente entidades nomeadas (pessoas, locais, organizações, crimes, etc.) usando um modelo treinado em português,
armazena as relações numa base de dados de grafos (Neo4j) e permite a exploração visual dessas relações.

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

O CEC é composto por três componentes principais:

* **Modelo NER:** Reconhecimento de entidades nomeadas baseado em `xlm-roberta-base`, treinado especificamente para
  notícias criminais em português. Identifica 11 tipos de entidades (PESSOA, LOCAL, ORGANIZACAO, CRIME, etc.).
* **Base de Dados (Neo4j):** Armazena as notícias, as frases e as entidades detetadas. As relações (co-ocorrências) são
  calculadas ao nível da frase para garantir que existe uma ligação contextual real.
* **Interface Web:** Aplicação que permite carregar ficheiros de texto, validar as entidades destacadas, editar
  correções manualmente e visualizar um grafo interativo das relações em cada frase.

---

## 2. Arquitetura e Fluxo de Dados

O sistema funciona em três camadas principais: o **Frontend** (React), o **Backend** (FastAPI) e a **Base de Dados** (
Neo4j). O frontend comunica exclusivamente com o backend via pedidos HTTP/JSON, e o backend encarrega-se de interagir
com o modelo de inteligência artificial e com o Neo4j.

**Como a informação flui no sistema:**

* **Consultar uma notícia:** A interface pede os dados ao backend, que recolhe o texto e as anotações do Neo4j. O texto
  é apresentado no ecrã com as palavras destacadas.
* **Adicionar uma nova notícia:** Ao fazer upload de um `.txt`, o texto é enviado para o backend. O modelo NER analisa o
  texto e identifica as entidades. Em seguida, o texto é dividido em frases, as relações são calculadas e tudo é
  guardado no Neo4j.
* **Editar entidades:** Qualquer adição ou remoção de entidades feita na interface só é consolidada ao clicar em "
  Guardar". Nesse momento, o backend atualiza as ligações dessa notícia no Neo4j.
* **Explorar o Grafo:** Ao selecionar uma frase específica, a interface pede ao backend as ligações (arestas) das
  entidades (nós) contidas nessa frase, desenhando um grafo interativo no ecrã.

---

## 3. Estrutura do Projeto

```text
 cec/
├── backend/
│ ├── main.py ← Entry point FastAPI, regista routers
│ ├── requirements.txt ← Dependências Python
│ ├── .env ← Credenciais Neo4j (não vai ao git)
│ ├── seed.py ← Popula Neo4j a partir do dataset_anotado.json
│ │
│ ├── api/ ← Rotas HTTP (só definem endpoints)
│ │ ├── noticias.py
│ │ ├── labels.py
│ │ └── grafo.py
│ │
│ ├── services/ ← Lógica
│ │ ├── neo4j_service.py ← Todas as queries ao Neo4j
│ │ ├── ner_service.py ← Wrapper do modelo NER
│ │ ├── sentence_splitter.py ← Divide texto em frases
│ │ └── graph_builder.py ← Calcula co-ocorrências por frase
│ │
│ ├── models/
│ │ └── schemas.py ← Tipos Pydantic (validação de dados)
│ │
│ └── ner_model/ ← Modelo NER treinado
│ ├── saved_model/ ← Pesos do modelo (não vão ao git)
│ ├── predict.py
│ ├── train.py
│ └── data/
│ ├── labels.py
│ └── dataset_anotado.json
│
└── frontend/
├── vite.config.js ← Proxy /api → localhost:8000
└── src/
├── api/
│ └── client.js ← Todas as chamadas fetch centralizadas
├── hooks/
│ ├── useNoticias.js ← Estado e lógica de notícias
│ ├── useLabels.js ← Estado e lógica de labels/cores
│ └── useGrafo.js ← Estado e lógica do grafo
└── components/
├── newsList.jsx ← Sidebar com lista de notícias
├── articleViewer.jsx← Texto com entidades destacadas
├── labelBar.jsx ← Chips de labels com cores da BD
├── actionBar.jsx ← Botões de ação
└── graphPanel.jsx ← Grafo interativo de relações
``` 

---

## 4. Pré-requisitos

Antes de instalar, é necessário garantir que as seguintes ferramentas estão instaladas no sistema:

* **Python (3.10+)**
* **Node.js (18+)**
* **Neo4j Desktop (2.x)**
* **Git**

---

## 5. Instalação e Configuração

### 5.1. Clonar o repositório

```bash
git clone [https://github.com/utilizador/repositorio.git](https://github.com/utilizador/repositorio.git)
cd repositorio/cec
```

### 5.2. Configurar o Neo4j

1. Abrir o **Neo4j Desktop**.
2. Criar uma nova instância local com o nome `cec-db` e definir uma palavra-passe.
3. Iniciar a instância (Start).
4. Criar uma base de dados com o nome `cec`.

### 5.3. Configurar o Backend

Aceder à pasta do backend e criar um ambiente virtual:

```bash
cd backend
python -m venv .venv

# No Windows:
.venv\Scripts\activate
# No macOS/Linux:
source .venv/bin/activate

# Instalar as dependências:
pip install -r requirements.txt
```

Criar um ficheiro `.env` na raiz da pasta `backend/` com as credenciais do Neo4j (este ficheiro não deve ser partilhado
ou enviado para o repositório):

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=a_palavra_passe_criada_no_passo_5_2
```

### 5.4. Adicionar o Modelo NER

Copiar a pasta `saved_model/` para dentro de `backend/ner_model/saved_model/`. É aqui que se
encontram os pesos do modelo (como o ficheiro `model.safetensors`).

### 5.5. Popular a Base de Dados

Com o Neo4j a correr e o ambiente virtual ativo, é necessário injetar os dados iniciais. **Só é preciso correr uma vez
** (ou sempre que o dataset base for alterado):

```bash
python seed.py
```

*Aguardar pela mensagem de sucesso a indicar que a base de dados foi populada.*

### 5.6. Configurar o Frontend

```bash
cd ../frontend
npm install
```

---

## 6. Correr o Projeto

Para utilizar a aplicação, é necessário ter os **três serviços a correr em simultâneo**:

1. **Neo4j Desktop:** A instância `cec-db` deve estar ativa (RUNNING).
2. **Backend:** No terminal, dentro da pasta `backend/` e com o ambiente virtual ativo:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
3. **Frontend:** Num novo terminal, dentro da pasta `frontend/`:
   ```bash
   npm run dev
   ```

A aplicação ficará disponível no navegador em: `http://localhost:5173`

*(A documentação da API pode ser consultada em `http://localhost:8000/docs`)*

---

## 7. Utilização da Interface

* **Navegar entre notícias:** Clicar em qualquer notícia na lista lateral para visualizar o texto com as entidades
  destacadas no centro do ecrã.
* **Adicionar Entidade:** Clicar no tipo de entidade desejado na barra superior (ex: PESSOA), selecionar a palavra no
  texto e clicar no botão "Adicionar entidade".
* **Remover Entidade:** Clicar na entidade destacada no texto (ficará selecionada) e pressionar "Remover entidade".
* **Guardar:** Clicar em "Guardar" para que as edições não se percam ao mudar de artigo.
* **Visualizar o Grafo:** Clicar no botão circular (◉) junto a cada frase para renderizar o grafo de relações no painel
  direito. É possível remover nós individualmente para analisar como a rede se adapta.
* **Nova Notícia:** Utilizar o botão "+ Adicionar notícia" para importar ficheiros `.txt`. O sistema fará a extração
  automática imediata.
* **Procurar Relações:** Utilizar o botão "Procurar relações noutras noticías" para renderizar um novo grafo onde é possivel observar as relações entre as entidades selecionadas e entidades que se relacionem com as mesmas noutras noticias.

---

## 8. Estrutura do Grafo no Neo4j

Para explorar a base de dados diretamente no Neo4j, a estrutura de nós e ligações funciona da seguinte
forma:

**Nós existentes:**

* `Noticia` (id, titulo)
* `Frase` (id, texto, ordem, noticia_id)
* `Entidade` (nome, tipo)
* `Label` (nome, cor)

**Relações (Arestas):**

* `TEM_FRASE`: Liga a notícia às suas frases.
* `MENCIONADA_EM`: Liga a entidade à frase onde foi encontrada.
* `CO_OCORRE_COM`: Liga duas entidades diferentes que aparecem na mesma frase.