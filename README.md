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

```
 WITHOUT RAG                               WITH RAG
 ──────────────────────────────────────    ──────────────────────────────────────────
 User: "What is the refund policy?"        User: "What is the refund policy?"
                                                        │
 LLM: "I don't have that information"     ┌─────────────▼───────────────────────────┐
      (answers from base knowledge,        │  1. Search vector DB for your docs     │
       may hallucinate)                    │  2. Retrieve relevant chunks           │
                                           │  3. Claude responds WITH context       │
                                           └─────────────┬───────────────────────────┘
                                                         │
                                            Claude: "According to document X,
                                                      the refund policy is..."
```

---

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                            │
│                                                                 │
│  INDEXING (offline)          QUERYING (online)                  │
│  ──────────────────          ──────────────────                 │
│                                                                 │
│  Documents                   User Question                      │
│      │                            │                            │
│      ▼                            ▼                            │
│  Text Splitter              Embedding Model                     │
│  (chunks 500 tokens)        (sentence-transformers)             │
│      │                            │                            │
│      ▼                            ▼                            │
│  Embedding Model            pgvector Search                     │
│  (vectorization)            (top-k similar chunks)             │
│      │                            │                            │
│      ▼                            ▼                            │
│  pgvector Store  ──────────► Context Assembly                   │
│  (PostgreSQL)                     │                            │
│                                   ▼                            │
│                            Claude API (claude-opus-4-7)        │
│                                   │                            │
│                                   ▼                            │
│                            Answer + Sources                     │
└─────────────────────────────────────────────────────────────────┘
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
│   ├── api/
│   │   ├── routes/
│   │   │   ├── ingest.py        # POST /ingest
│   │   │   └── query.py         # POST /query, GET /history
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── rag_pipeline.py      # Main RAG pipeline
│   │   ├── document_loader.py   # PDF, DOCX, TXT loaders
│   │   ├── text_splitter.py     # Chunking with overlap
│   │   └── embeddings.py        # Embeddings wrapper
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
// Request: multipart/form-data
// file: PDF/DOCX/TXT file

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
    {
      "document": "HR-Policy-2024.pdf",
      "chunk": "Employees are entitled to...",
      "similarity": 0.94
    }
  ],
  "session_id": "uuid"
}
```

#### `GET /history/{session_id}`
Returns the conversation history for a session.

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

# Production settings
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
- **pytest** (testing)

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

```
 SIN RAG                                   CON RAG
 ──────────────────────────────────────    ──────────────────────────────────────────
 Usuario: "¿Cuál es la política de         Usuario: "¿Cuál es la política de
           reembolso?"                                reembolso?"
                                                           │
 LLM: "No tengo esa información"          ┌────────────────▼────────────────────────┐
      (responde con su conocimiento base,  │  1. Busca en vector DB tus docs        │
       puede alucinar)                     │  2. Recupera chunks relevantes         │
                                           │  3. Claude responde CON contexto       │
                                           └────────────────┬────────────────────────┘
                                                            │
                                            Claude: "Según el documento X,
                                                      la política de reembolso es..."
```

---

### Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                            │
│                                                                 │
│  INDEXING (offline)          QUERYING (online)                  │
│  ──────────────────          ──────────────────                 │
│                                                                 │
│  Documents                   User Question                      │
│      │                            │                            │
│      ▼                            ▼                            │
│  Text Splitter              Embedding Model                     │
│  (chunks 500 tokens)        (sentence-transformers)             │
│      │                            │                            │
│      ▼                            ▼                            │
│  Embedding Model            pgvector Search                     │
│  (vectorización)            (top-k chunks similares)           │
│      │                            │                            │
│      ▼                            ▼                            │
│  pgvector Store  ──────────► Context Assembly                   │
│  (PostgreSQL)                     │                            │
│                                   ▼                            │
│                            Claude API (claude-opus-4-7)        │
│                                   │                            │
│                                   ▼                            │
│                            Respuesta + Fuentes                  │
└─────────────────────────────────────────────────────────────────┘
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
│   ├── api/
│   │   ├── routes/
│   │   │   ├── ingest.py        # POST /ingest
│   │   │   └── query.py         # POST /query, GET /history
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── rag_pipeline.py      # Pipeline principal RAG
│   │   ├── document_loader.py   # Carga PDF, DOCX, TXT
│   │   ├── text_splitter.py     # Chunking con solapamiento
│   │   └── embeddings.py        # Wrapper embeddings
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
// Request: multipart/form-data
// file: archivo PDF/DOCX/TXT

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
    {
      "document": "HR-Policy-2024.pdf",
      "chunk": "Los empleados tienen derecho a...",
      "similarity": 0.94
    }
  ],
  "session_id": "uuid"
}
```

#### `GET /history/{session_id}`
Historial de conversación de una sesión.

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

# Para producción
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
- **pytest** (testing)

---

### Autor

**Cristian Daniel Gutiérrez S.** — Solutions Architect | AI Engineer

[LinkedIn](https://www.linkedin.com/in/cristian-daniel-guti%C3%A9rrez-segura) · [Portfolio](https://portafolio-frontend-wheat.vercel.app) · [cdgutierrez6@gmail.com](mailto:cdgutierrez6@gmail.com)

</details>
