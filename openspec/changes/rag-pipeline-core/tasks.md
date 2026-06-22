## 1. Infraestructura y Base de Datos

- [ ] 1.1 Agregar servicio `postgres` con imagen `pgvector/pgvector:pg16` al `docker-compose.yml` con volumen persistente y healthcheck
- [ ] 1.2 Crear script de migration `app/db/migrations/001_create_documents.sql` con `CREATE EXTENSION IF NOT EXISTS vector`, tabla `documents` (id UUID, content TEXT, embedding VECTOR(1536), source VARCHAR, created_at TIMESTAMPTZ), e índice HNSW `USING hnsw (embedding vector_cosine_ops)`
- [ ] 1.3 Implementar `app/db/connection.py` con pool de conexiones usando `asyncpg` y función `get_pool()` para uso desde FastAPI

## 2. Ingesta de Documentos

- [ ] 2.1 Implementar `app/ingest.py` con función `chunk_document(text, source)` usando `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` de LangChain
- [ ] 2.2 Implementar `generate_embeddings(chunks)` que llama al modelo de embeddings configurado y retorna lista de vectores
- [ ] 2.3 Implementar `store_chunks(chunks, embeddings, source)` que inserta en batch en la tabla `documents` usando `asyncpg.executemany`
- [ ] 2.4 Crear router FastAPI `app/routers/ingest.py` con `POST /ingest` que acepta `UploadFile`, extrae texto, llama al pipeline y retorna `{"chunks_stored": N}`
- [ ] 2.5 Agregar validación en startup (`app/main.py` lifespan) que verifica la dimensión del modelo de embedding contra la columna `embedding VECTOR(N)` y lanza error si no coincide

## 3. Retrieval Híbrido

- [ ] 3.1 Implementar `app/retrieval/semantic.py` con función `semantic_search(query_embedding, top_k)` que ejecuta búsqueda coseno en pgvector y retorna lista de `(chunk_id, content, source, score)`
- [ ] 3.2 Implementar `app/retrieval/bm25.py` con función `bm25_search(query, top_k)` usando `to_tsvector`/`to_tsquery` de PostgreSQL y retornando lista de `(chunk_id, content, source, rank)`
- [ ] 3.3 Implementar `app/retrieval/fusion.py` con función `rrf_fusion(semantic_results, bm25_results, k=60, top_k)` que combina y deduplica los resultados con RRF
- [ ] 3.4 Crear `app/retrieval/__init__.py` con función `retrieve(query, top_k)` que orquesta los 3 pasos: embed query → semantic + BM25 → RRF → retorna top-K chunks

## 4. Generación con Claude

- [ ] 4.1 Implementar `app/generation.py` con función `build_prompt(question, chunks)` que formatea el system prompt con instrucción de grounding estricto y los chunks como `[Fuente: <source>]\n<content>`, respetando el límite `RAG_MAX_CONTEXT_CHARS`
- [ ] 4.2 Implementar `generate_answer(question, chunks)` que llama a `anthropic.Anthropic().messages.create()` con el prompt construido y retorna `{"answer": str, "sources": list[str]}`
- [ ] 4.3 Crear router FastAPI `app/routers/query.py` con `POST /query` que recibe `{"question": str}`, llama a `retrieve()` + `generate_answer()` y retorna la respuesta con sources

## 5. Configuración y Variables de Entorno

- [ ] 5.1 Crear `app/config.py` con `Settings` (pydantic-settings): `DATABASE_URL`, `ANTHROPIC_API_KEY`, `EMBEDDING_MODEL`, `RAG_TOP_K` (default 5), `RAG_MAX_CONTEXT_CHARS` (default 8000)
- [ ] 5.2 Crear `.env.example` documentando todas las variables requeridas con valores de ejemplo

## 6. Tests

- [ ] 6.1 Test de integración para `POST /ingest`: ingestar un documento de prueba y verificar que los chunks aparecen en la DB con embeddings no nulos
- [ ] 6.2 Test unitario para `rrf_fusion`: verificar que un chunk en posición alta en BM25 y baja en semántico aparece en el top-5 fusionado
- [ ] 6.3 Test de integración para `POST /query`: consulta con respuesta en los documentos ingestados retorna `answer` no vacío y `sources` con el archivo de prueba
- [ ] 6.4 Test de edge case: `POST /query` con DB vacía retorna el mensaje de "no tengo información suficiente"

## 7. Verificación

- [ ] 7.1 `docker compose up --build` levanta sin errores y el healthcheck de postgres pasa
- [ ] 7.2 `POST /ingest` con un PDF de prueba retorna `{"chunks_stored": N}` con N > 0
- [ ] 7.3 `POST /query` con pregunta respondible desde el PDF retorna respuesta con la fuente citada
