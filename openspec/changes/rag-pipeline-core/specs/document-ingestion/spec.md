## ADDED Requirements

### Requirement: Document upload and chunking
El sistema SHALL aceptar documentos de texto (TXT, PDF, Markdown) vía `POST /ingest`, dividirlos en chunks con `RecursiveCharacterTextSplitter` (chunk_size=1000, chunk_overlap=200) y persistir cada chunk con su embedding en la tabla `documents` de PostgreSQL.

#### Scenario: Ingesta exitosa de documento
- **WHEN** el cliente envía `POST /ingest` con un archivo de texto válido
- **THEN** el sistema retorna `{"chunks_stored": N}` donde N es el número de chunks generados, y cada chunk existe en la tabla `documents` con su vector de embedding y la metadata de la fuente

#### Scenario: Documento vacío
- **WHEN** el cliente envía `POST /ingest` con un archivo de 0 bytes o sin contenido extraíble
- **THEN** el sistema retorna HTTP 400 con `{"error": "El documento no contiene texto procesable"}`

---

### Requirement: Embedding storage con pgvector
El sistema SHALL almacenar cada chunk como una fila en la tabla `documents` con columnas: `id` (UUID), `content` (TEXT), `embedding` (VECTOR(N)), `source` (VARCHAR), `created_at` (TIMESTAMPTZ). El índice HNSW SHALL estar creado sobre la columna `embedding` para búsqueda eficiente.

#### Scenario: Chunk almacenado con embedding correcto
- **WHEN** se completa la ingesta de un chunk
- **THEN** la fila en `documents` contiene el texto original en `content`, el vector de dimensión N en `embedding`, y el nombre del archivo en `source`

#### Scenario: Dimensión de embedding validada en startup
- **WHEN** el servicio arranca
- **THEN** valida que la dimensión del modelo de embedding coincide con `N` en la columna `embedding VECTOR(N)`; si no coincide, lanza error y detiene el arranque

---

### Requirement: Metadata de fuente por chunk
El sistema SHALL preservar el nombre del archivo original como `source` en cada chunk para que las respuestas puedan citar la fuente específica del fragmento recuperado.

#### Scenario: Source preservado en cada chunk
- **WHEN** se ingesta `manual_tecnico.pdf` y genera 15 chunks
- **THEN** todos los 15 chunks tienen `source = "manual_tecnico.pdf"` en la tabla `documents`
