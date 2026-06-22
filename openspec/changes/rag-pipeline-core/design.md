## Context

El asistente RAG resuelve el problema de los LLMs respondiendo desde su conocimiento de entrenamiento en lugar del corpus privado del usuario. El sistema necesita: (1) ingestar y vectorizar documentos, (2) recuperar los fragmentos más relevantes ante una consulta, y (3) generar una respuesta citando esas fuentes con Claude. FastAPI sirve como gateway HTTP; PostgreSQL con pgvector es el único almacén de datos (sin dependencias de vector DBs externas como Pinecone o Weaviate).

## Goals / Non-Goals

**Goals:**
- Pipeline end-to-end funcional: ingest → embed → store → retrieve → generate
- Retrieval híbrido (semántico + léxico) con fusión RRF para mayor recall
- Respuestas ancladas al contexto recuperado — Claude no debe inventar fuera de las fuentes
- Stack minimalista: solo PostgreSQL + pgvector, sin servicios adicionales

**Non-Goals:**
- UI de chat (solo API REST)
- Gestión de usuarios o autenticación (fuera de scope de esta iteración)
- Fine-tuning del modelo de embeddings
- Re-indexación automática ante cambios de documentos

## Decisions

### D1 — pgvector sobre Pinecone/Weaviate

**Decisión**: PostgreSQL + pgvector como único vector store.

**Alternativas consideradas**:
- _Pinecone_: managed, sin ops, pero dependencia de servicio externo de pago con límites en el free tier.
- _Weaviate_: open-source potente, pero requiere otro container y su propio SDK — complejidad innecesaria para el scope actual.

**Rationale**: pgvector en el mismo PostgreSQL del proyecto elimina una dependencia de infraestructura. El índice HNSW soporta millones de vectores con latencia sub-100ms. Si escala a cientos de millones, migrar a un vector DB dedicado es una decisión futura bien definida.

---

### D2 — Chunking recursivo sobre fixed-size o sentence splitting

**Decisión**: `RecursiveCharacterTextSplitter` de LangChain con `chunk_size=1000`, `chunk_overlap=200`.

**Alternativas consideradas**:
- _Fixed-size_: ignora la estructura del texto — parte oraciones a la mitad, perjudicando la coherencia semántica del chunk.
- _Sentence splitting_: chunks de tamaño variable dificultan la gestión del contexto máximo del LLM.

**Rationale**: el split recursivo respeta separadores naturales (párrafos → frases → palabras) antes de cortar por tamaño. El overlap del 20% preserva contexto entre chunks adyacentes sin duplicar demasiado.

---

### D3 — Retrieval híbrido con RRF sobre solo semántico

**Decisión**: combinar búsqueda semántica (cosine similarity en pgvector) + BM25 (pg_trgm o búsqueda full-text PostgreSQL), fusionados con Reciprocal Rank Fusion.

**Alternativas consideradas**:
- _Solo semántico_: falla en queries con términos técnicos exactos (nombres propios, códigos, acrónimos) donde el embedding puede no capturar la especificidad léxica.
- _Solo BM25_: falla en queries conceptuales o parafraseadas que no comparten vocabulario con el documento.

**Rationale**: RRF es rank-agnostic — combina listas ordenadas sin calibrar scores, robusto ante distribuciones distintas entre modelos de embedding y BM25. Recall típicamente +15-20% sobre solo semántico en benchmarks BEIR.

---

### D4 — Prompt con instrucción explícita de grounding

**Decisión**: el system prompt incluye: _"Responde ÚNICAMENTE basándote en los fragmentos de contexto proporcionados. Si la respuesta no está en el contexto, responde: 'No tengo información suficiente en los documentos proporcionados'."_

**Rationale**: Claude tiene conocimiento de entrenamiento extenso. Sin la instrucción explícita, puede mezclar conocimiento propio con el contexto recuperado, haciendo imposible auditar las fuentes. El grounding estricto es el contrato de confianza del sistema RAG.

## Risks / Trade-offs

| Riesgo | Mitigation |
|--------|-----------|
| Chunks irrelevantes degradan la respuesta | Top-K configurable (default 5); reranker cross-encoder filtra antes de pasar a Claude |
| Dimensión de embedding no coincide con el índice pgvector | Validación en startup: la dimensión del modelo se compara contra `vector(N)` de la columna |
| Latencia alta por retrieval + LLM call en secuencia | Cache de embeddings de queries repetidas en Redis (fase 2); por ahora aceptable para PoC |
| Documentos grandes consumen demasiados tokens en el prompt | Límite configurable de caracteres totales de contexto antes de la llamada a Claude |

## Migration Plan

1. Habilitar extensión pgvector: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Ejecutar migration de tabla `documents` con índice HNSW
3. Correr `POST /ingest` con documentos de prueba
4. Verificar con `POST /query` que las respuestas citan los documentos ingestados
5. Deploy via `docker compose up --build`

**Rollback**: la API es stateless — basta con bajar el container. Los datos en pgvector se preservan en el volumen.

## Open Questions

- ¿Modelo de embeddings final? (Voyage AI `voyage-3-lite` vs. `text-embedding-3-small` de OpenAI — depende de costos)
- ¿Top-K óptimo para el reranker? (probar 3, 5, 10 contra el corpus de evaluación)
