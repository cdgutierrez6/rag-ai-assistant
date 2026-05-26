# RAG AI Assistant — Retrieval Augmented Generation with Claude API

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Claude API](https://img.shields.io/badge/Claude_API-CC785C?style=flat-square&logo=anthropic&logoColor=white)](https://www.anthropic.com)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://www.langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/pgvector-316192?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)

---

<details open>
<summary><h2>🇺🇸 English</h2></summary>

Production-ready RAG (Retrieval Augmented Generation) system that enables natural language questions over your own documents, using **Claude API** as the LLM and **pgvector** as the vector store. Designed with clean architecture, ready to scale.

---

### What is RAG and why does it matter?

```mermaid
flowchart TB
    subgraph WITHOUT["❌ Without RAG"]
        direction LR
        U1["User Question"] --> LLM1["LLM\nbase knowledge only"]
        LLM1 --> R1["May hallucinate\nor give generic answer"]
    end

    subgraph WITH["✅ With RAG"]
        direction LR
        U2["User Question"] --> DB["Vector DB\nsemantic search"]
        DB --> CTX["Relevant document\nchunks retrieved"]
        CTX --> LLM2["Claude API\nwith context"]
        LLM2 --> R2["Accurate answer\nciting your documents"]
    end
```

---

### Architecture

```mermaid
flowchart LR
    subgraph IDX["📥 Indexing — offline"]
        D["Documents\nPDF · DOCX · TXT"] --> TS["Text Splitter\n500 tokens · overlap 50"]
        TS --> EM1["Embedding Model\nall-MiniLM-L6-v2"]
        EM1 --> PG[("pgvector\nPostgreSQL")]
    end

    subgraph QRY["🔍 Querying — real-time"]
        Q["User Question"] --> EM2["Embedding Model\nall-MiniLM-L6-v2"]
        EM2 --> VS["Vector Search\ncosine distance · top-k"]
        VS --> CA["Context Assembly"]
        CA --> LLM["Claude API\nclaude-opus-4-7"]
        LLM --> ANS["Answer + Sources"]
    end

    PG -- "similar chunks" --> VS
```

---

### Features

- **RAG with Claude API** — uses `claude-opus-4-7` for reasoning, sentence-transformers for semantic search
- **pgvector** — semantic search in PostgreSQL (no need for Pinecone or external services)
- **Multi-format ingestion** — PDF, DOCX, TXT, HTML, Markdown
- **Intelligent chunking** — RecursiveCharacterTextSplitter with configurable overlap
- **REST API** — FastAPI with endpoints for ingestion and queries
- **Conversation history** — contextual memory per session
- **Source citations** — the LLM cites which documents it used to answer
- **Docker ready** — one command to spin up the full stack

---

### Quick Start

```bash
# 1. Clone
git clone https://github.com/cdgutierrez6/rag-ai-assistant.git
cd rag-ai-assistant

# 2. Environment variables
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 3. Start with Docker
docker-compose up -d

# 4. Ingest a document
curl -X POST http://localhost:8000/ingest \
  -F "file=@my_document.pdf"

# 5. Query the system
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the document summary?"}'
```

---

### Project Structure

```
rag-ai-assistant/
├── app/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── api/routes/
│   │   ├── ingest.py            # POST /ingest
│   │   └── query.py             # POST /query, GET /history
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── rag_pipeline.py      # Main RAG pipeline
│   │   └── document_loader.py   # PDF, DOCX, TXT loaders
│   ├── db/
│   │   ├── vector_store.py      # pgvector operations
│   │   ├── session_store.py     # Conversation history
│   │   └── init.sql             # Schema + ivfflat index
│   └── models/
│       ├── request.py
│       └── response.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_ingest.py
│   └── test_query.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

### API Endpoints

#### `POST /ingest`
Ingests a document and indexes it in pgvector.

```json
// Request: multipart/form-data — file: PDF/DOCX/TXT

// Response
{
  "document_id": "uuid",
  "chunks_created": 42,
  "status": "indexed"
}
```

#### `POST /query`
Queries the RAG system.

```json
// Request
{
  "question": "What is the vacation policy?",
  "session_id": "optional-uuid",
  "top_k": 5
}

// Response
{
  "answer": "According to document 'HR-Policy-2024.pdf'...",
  "sources": [
    { "document": "HR-Policy-2024.pdf", "chunk": "...", "similarity": 0.94 }
  ],
  "session_id": "uuid"
}
```

#### `GET /history/{session_id}`
Returns the conversation history for a session.

---

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific module
pytest tests/test_pipeline.py -v
pytest tests/test_ingest.py -v
```

| Test module | Coverage | Strategy |
|---|---|---|
| `test_pipeline.py` | RAG pipeline end-to-end | Claude API + pgvector mocked with `pytest-mock` |
| `test_ingest.py` | Document ingestion & chunking | LangChain loaders mocked, chunking asserted |
| `test_query.py` | Query endpoint + session history | Vector store mocked, response schema validated |

---

### Configuration

```env
# .env.example
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-opus-4-7

DATABASE_URL=postgresql://rag_user:rag_pass@localhost:5432/rag_db
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# Production
MAX_DOCUMENTS_PER_USER=100
MAX_FILE_SIZE_MB=50
```

---

### Use Cases

- **Internal support** — Chatbot that answers questions about company policies and procedures
- **Legal** — Query contracts and regulations
- **Education** — Assistant over academic material
- **Onboarding** — Knowledge base for new employees
- **Telemetry** — Log analysis and technical reports (real case applied at SATRACK)

---

### Technologies

- **Python 3.11** + **FastAPI**
- **Anthropic SDK** (Claude API)
- **LangChain** (document loaders, text splitters)
- **sentence-transformers** (all-MiniLM-L6-v2 embeddings)
- **pgvector** (vector search in PostgreSQL)
- **SQLAlchemy** (ORM)
- **Docker** + **Docker Compose**
- **Pydantic v2** (data validation)
- **pytest** + **pytest-mock** (testing)

---

### Author

**Cristian Daniel Gutiérrez S.** — Solutions Architect | AI Engineer

[LinkedIn](https://www.linkedin.com/in/cristian-daniel-guti%C3%A9rrez-segura) · [Portfolio](https://portafolio-frontend-wheat.vercel.app) · [cdgutierrez6@gmail.com](mailto:cdgutierrez6@gmail.com)

</details>

---

<details>
<summary><h2>🇨🇴 Español</h2></summary>

Sistema RAG (Retrieval Augmented Generation) de producción que permite hacer preguntas en lenguaje natural sobre documentos propios, usando **Claude API** como LLM y **pgvector** como vector store. Diseñado con arquitectura limpia, lista para escalar.

---

### ¿Qué es RAG y por qué importa?

```mermaid
flowchart TB
    subgraph WITHOUT["❌ Sin RAG"]
        direction LR
        U1["Pregunta del usuario"] --> LLM1["LLM\nsolo conocimiento base"]
        LLM1 --> R1["Puede alucinar\no dar respuesta genérica"]
    end

    subgraph WITH["✅ Con RAG"]
        direction LR
        U2["Pregunta del usuario"] --> DB["Vector DB\nbúsqueda semántica"]
        DB --> CTX["Chunks relevantes\nde tus documentos"]
        CTX --> LLM2["Claude API\ncon contexto"]
        LLM2 --> R2["Respuesta precisa\ncitando tus documentos"]
    end
```

---

### Arquitectura

```mermaid
flowchart LR
    subgraph IDX["📥 Indexado — offline"]
        D["Documentos\nPDF · DOCX · TXT"] --> TS["Text Splitter\n500 tokens · overlap 50"]
        TS --> EM1["Embedding Model\nall-MiniLM-L6-v2"]
        EM1 --> PG[("pgvector\nPostgreSQL")]
    end

    subgraph QRY["🔍 Consulta — tiempo real"]
        Q["Pregunta del usuario"] --> EM2["Embedding Model\nall-MiniLM-L6-v2"]
        EM2 --> VS["Vector Search\ndistancia coseno · top-k"]
        VS --> CA["Ensamblado de contexto"]
        CA --> LLM["Claude API\nclaude-opus-4-7"]
        LLM --> ANS["Respuesta + Fuentes"]
    end

    PG -- "chunks similares" --> VS
```

---

### Características

- **RAG con Claude API** — usa `claude-opus-4-7` para razonamiento, sentence-transformers para búsqueda semántica
- **pgvector** — búsqueda semántica en PostgreSQL (sin necesidad de Pinecone u otros servicios externos)
- **Ingesta multi-formato** — PDF, DOCX, TXT, HTML, Markdown
- **Chunking inteligente** — RecursiveCharacterTextSplitter con solapamiento configurable
- **API REST** — FastAPI con endpoints para ingestión y consultas
- **Historial de conversación** — memoria contextual por sesión
- **Citas de fuentes** — el LLM cita los documentos que usó para responder
- **Docker ready** — un comando para levantar todo el stack

---

### Inicio Rápido

```bash
# 1. Clonar
git clone https://github.com/cdgutierrez6/rag-ai-assistant.git
cd rag-ai-assistant

# 2. Variables de entorno
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY

# 3. Levantar con Docker
docker-compose up -d

# 4. Ingestar un documento
curl -X POST http://localhost:8000/ingest \
  -F "file=@mi_documento.pdf"

# 5. Consultar el sistema
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el resumen del documento?"}'
```

---

### Estructura del Proyecto

```
rag-ai-assistant/
├── app/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── api/routes/
│   │   ├── ingest.py            # POST /ingest
│   │   └── query.py             # POST /query, GET /history
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── rag_pipeline.py      # Pipeline principal RAG
│   │   └── document_loader.py   # Carga PDF, DOCX, TXT
│   ├── db/
│   │   ├── vector_store.py      # Operaciones pgvector
│   │   ├── session_store.py     # Historial de conversación
│   │   └── init.sql             # Schema + índice ivfflat
│   └── models/
│       ├── request.py
│       └── response.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_ingest.py
│   └── test_query.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

### API Endpoints

#### `POST /ingest`
Ingesta un documento y lo indexa en pgvector.

```json
// Request: multipart/form-data — file: archivo PDF/DOCX/TXT

// Response
{
  "document_id": "uuid",
  "chunks_created": 42,
  "status": "indexed"
}
```

#### `POST /query`
Consulta el sistema RAG.

```json
// Request
{
  "question": "¿Cuál es la política de vacaciones?",
  "session_id": "optional-uuid",
  "top_k": 5
}

// Response
{
  "answer": "Según el documento 'HR-Policy-2024.pdf'...",
  "sources": [
    { "document": "HR-Policy-2024.pdf", "chunk": "...", "similarity": 0.94 }
  ],
  "session_id": "uuid"
}
```

#### `GET /history/{session_id}`
Historial de conversación de una sesión.

---

### Correr Tests

```bash
# Instalar dependencias
pip install -r requirements.txt

# Correr todos los tests
pytest

# Con output detallado
pytest -v

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Módulo específico
pytest tests/test_pipeline.py -v
pytest tests/test_ingest.py -v
```

| Módulo de test | Cobertura | Estrategia |
|---|---|---|
| `test_pipeline.py` | Pipeline RAG end-to-end | Claude API + pgvector mockeados con `pytest-mock` |
| `test_ingest.py` | Ingesta de documentos y chunking | LangChain loaders mockeados, chunking verificado |
| `test_query.py` | Endpoint de consulta + historial | Vector store mockeado, schema de respuesta validado |

---

### Configuración

```env
# .env.example
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-opus-4-7

DATABASE_URL=postgresql://rag_user:rag_pass@localhost:5432/rag_db
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# Producción
MAX_DOCUMENTS_PER_USER=100
MAX_FILE_SIZE_MB=50
```

---

### Casos de Uso

- **Soporte interno** — Chatbot que responde preguntas sobre políticas y procedimientos de la empresa
- **Legal** — Consultas sobre contratos y normativas
- **Educación** — Asistente sobre material académico
- **Onboarding** — Base de conocimiento para nuevos empleados
- **Telemetría** — Análisis de logs y reportes técnicos (caso real aplicado en SATRACK)

---

### Tecnologías

- **Python 3.11** + **FastAPI**
- **Anthropic SDK** (Claude API)
- **LangChain** (document loaders, text splitters)
- **sentence-transformers** (embeddings all-MiniLM-L6-v2)
- **pgvector** (búsqueda vectorial en PostgreSQL)
- **SQLAlchemy** (ORM)
- **Docker** + **Docker Compose**
- **Pydantic v2** (validación de datos)
- **pytest** + **pytest-mock** (testing)

---

### Autor

**Cristian Daniel Gutiérrez S.** — Solutions Architect | AI Engineer

[LinkedIn](https://www.linkedin.com/in/cristian-daniel-guti%C3%A9rrez-segura) · [Portfolio](https://portafolio-frontend-wheat.vercel.app) · [cdgutierrez6@gmail.com](mailto:cdgutierrez6@gmail.com)

</details>
