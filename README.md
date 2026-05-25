# RAG AI Assistant — Retrieval Augmented Generation con Claude API

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Claude API](https://img.shields.io/badge/Claude_API-CC785C?style=flat-square&logo=anthropic&logoColor=white)](https://www.anthropic.com)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://www.langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/pgvector-316192?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)

Sistema RAG (Retrieval Augmented Generation) de producción que permite hacer preguntas en lenguaje natural sobre documentos propios, usando **Claude API** como LLM y **pgvector** como vector store. Diseñado con arquitectura limpia, lista para escalar.

---

## ¿Qué es RAG y por qué importa?

```
 SIN RAG                              CON RAG
 ─────────────────────────────────    ─────────────────────────────────────────
 Usuario: "¿Cuál es la política       Usuario: "¿Cuál es la política de
           de reembolso?"                        reembolso?"
                                                     │
 LLM: "No tengo esa información"      ┌──────────────▼──────────────────────┐
      (responde con su conocimiento   │  1. Busca en vector DB tus docs    │
       base, puede alucinar)          │  2. Recupera chunks relevantes     │
                                      │  3. Claude responde CON contexto   │
                                      └──────────────┬──────────────────────┘
                                                     │
                                       Claude: "Según el documento X,
                                                 la política de reembolso es..."
```

---

## Arquitectura

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
│  (chunks 500 tokens)        (Claude Embeddings)                 │
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

## Características

- **RAG con Claude API** — usa `claude-opus-4-7` para razonamiento, embeddings propios para búsqueda
- **pgvector** — búsqueda semántica en PostgreSQL (sin necesidad de Pinecone u otros servicios externos)
- **Ingesta multi-formato** — PDF, DOCX, TXT, HTML, Markdown
- **Chunking inteligente** — RecursiveCharacterTextSplitter con solapamiento configurable
- **API REST** — FastAPI con endpoints para ingestión y consultas
- **Historial de conversación** — memoria contextual por sesión
- **Sources en respuesta** — el LLM cita los documentos usados
- **Docker ready** — un comando para levantar todo

---

## Inicio Rápido

```bash
# 1. Clonar
git clone https://github.com/cdgutierrez6/rag-ai-assistant.git
cd rag-ai-assistant

# 2. Variables de entorno
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY

# 3. Levantar con Docker
docker-compose up -d

# 4. Ingestar documentos
curl -X POST http://localhost:8000/ingest \
  -F "file=@mi_documento.pdf"

# 5. Consultar
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el resumen del documento?"}'
```

---

## Estructura del Proyecto

```
rag-ai-assistant/
├── app/
│   ├── main.py                  # FastAPI app
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
│   │   └── embeddings.py        # Wrapper embeddings Claude
│   ├── db/
│   │   ├── vector_store.py      # pgvector operations
│   │   ├── session_store.py     # Historial de conversación
│   │   └── migrations/          # Alembic migrations
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
├── .env.example
└── docs/
    ├── api.md                   # Documentación API
    └── deployment.md            # Guía de despliegue AWS/Azure
```

---

## API Endpoints

### `POST /ingest`
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

### `POST /query`
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

### `GET /history/{session_id}`
Historial de conversación de una sesión.

---

## Configuración

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

## Casos de Uso

- **Soporte interno** — Chatbot que responde preguntas sobre políticas y procedimientos de la empresa
- **Legal** — Consultas sobre contratos y normativas
- **Educación** — Asistente sobre material académico
- **Onboarding** — Base de conocimiento para nuevos empleados
- **Telemetría** — Análisis de logs y reportes técnicos (caso real aplicado en SATRACK)

---

## Tecnologías

- **Python 3.11** + **FastAPI**
- **Anthropic SDK** (Claude API)
- **LangChain** (document loaders, text splitters)
- **pgvector** (búsqueda vectorial en PostgreSQL)
- **SQLAlchemy** + **Alembic** (ORM y migraciones)
- **Docker** + **Docker Compose**
- **Pydantic v2** (validación de datos)
- **pytest** (testing)

---

## Autor

**Cristian Daniel Gutiérrez S.** — Solutions Architect | AI Engineer

[LinkedIn](https://www.linkedin.com/in/cristian-daniel-guti%C3%A9rrez-segura) · [Portfolio](https://portafolio-frontend-wheat.vercel.app) · [cdgutierrez6@gmail.com](mailto:cdgutierrez6@gmail.com)
