## Why

Los LLMs responden con conocimiento de entrenamiento genérico y sin acceso a documentos propios del usuario, produciendo respuestas desactualizadas o incorrectas en dominios especializados. El sistema RAG ancla cada respuesta al corpus privado del usuario, citando los fragmentos recuperados como fuente de verdad y eliminando las alucinaciones sobre contenido no visto durante el entrenamiento.

## What Changes

- Ingesta de documentos con chunking recursivo configurable (tamaño y overlap por colección)
- Generación de embeddings vía modelo configurado (Voyage AI o compatible) y almacenamiento en pgvector (PostgreSQL)
- Retrieval híbrido: búsqueda semántica por similitud coseno + BM25 keyword search, resultados fusionados por RRF
- Reranking de candidatos con cross-encoder antes de pasar el contexto a Claude
- Endpoint FastAPI `POST /query` que recibe pregunta y retorna respuesta con sources citados
- Prompt engineering que instruye a Claude a responder solo con el contexto recuperado o decir "no sé"

## Capabilities

### New Capabilities

- `document-ingestion`: Carga, chunking recursivo y almacenamiento de documentos en pgvector con metadata (fuente, timestamp, colección)
- `hybrid-retrieval`: Recuperación de fragmentos relevantes combinando búsqueda semántica (pgvector cosine) y léxica (BM25), fusionada con RRF
- `answer-generation`: Construcción del prompt con contexto recuperado y llamada a Claude API para generar respuesta anclada con citas de sources

### Modified Capabilities

_(ninguna — implementación inicial del pipeline RAG completo)_

## Impact

- **`app/`**: módulos `ingest.py`, `retrieval.py`, `generation.py`, router FastAPI `query.py`
- **PostgreSQL**: extensión `pgvector` habilitada, tabla `documents` con columna `embedding vector(1536)`, índice HNSW
- **Dependencias**: `anthropic`, `langchain`, `langchain-community`, `langchain-anthropic`, `pgvector`, `psycopg2-binary`, `fastapi`, `uvicorn`
- **docker-compose.yml**: servicio `postgres` con imagen `pgvector/pgvector:pg16`, volumen persistente
