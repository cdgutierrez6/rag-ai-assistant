## ADDED Requirements

### Requirement: Búsqueda semántica por similitud coseno
El sistema SHALL vectorizar la query del usuario con el mismo modelo de embeddings usado en la ingesta y recuperar los top-K chunks más similares usando similitud coseno sobre el índice HNSW de pgvector.

#### Scenario: Retrieval semántico exitoso
- **WHEN** el usuario consulta "¿cómo configuro el timeout?"
- **THEN** el sistema retorna los top-K chunks cuyo contenido es semánticamente más próximo a la query, ordenados por similitud descendente

#### Scenario: Sin resultados con similitud suficiente
- **WHEN** la query no tiene relación semántica con ningún documento ingestado (similitud < umbral configurable)
- **THEN** el retriever retorna lista vacía; la capa de generación responde con el mensaje de "no tengo información suficiente"

---

### Requirement: Búsqueda léxica BM25
El sistema SHALL ejecutar una búsqueda full-text BM25 sobre la columna `content` de la tabla `documents` usando las capacidades de full-text search de PostgreSQL (`to_tsvector` / `to_tsquery`) en paralelo con la búsqueda semántica.

#### Scenario: BM25 captura términos técnicos exactos
- **WHEN** el usuario consulta un acrónimo o nombre propio exacto (ej: "RFC 7519")
- **THEN** la búsqueda BM25 recupera chunks que contienen ese término, incluso si el embedding semántico no lo captura

---

### Requirement: Fusión de resultados con RRF
El sistema SHALL combinar los resultados de la búsqueda semántica y BM25 usando Reciprocal Rank Fusion (RRF) con `k=60` y retornar los top-K chunks fusionados como contexto final para la generación.

#### Scenario: RRF mejora recall sobre solo semántico
- **WHEN** un chunk relevante aparece en posición 8 en el ranking semántico pero en posición 1 en BM25
- **THEN** RRF lo eleva en el ranking combinado y aparece en el top-5 final

#### Scenario: Deduplicación de chunks
- **WHEN** el mismo chunk aparece en ambos rankings (semántico y BM25)
- **THEN** RRF lo cuenta una sola vez con el score combinado; no aparece duplicado en el contexto

---

### Requirement: Top-K configurable
El número de chunks a recuperar SHALL ser configurable vía variable de entorno `RAG_TOP_K` con valor default `5`.

#### Scenario: Top-K aplicado correctamente
- **WHEN** `RAG_TOP_K=3` y hay 20 chunks en la DB
- **THEN** el retriever retorna exactamente 3 chunks fusionados por RRF
