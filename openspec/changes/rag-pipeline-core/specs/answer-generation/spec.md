## ADDED Requirements

### Requirement: Prompt con grounding estricto
El sistema SHALL construir el prompt para Claude incluyendo: (1) instrucción de system de responder ÚNICAMENTE con el contexto recuperado, (2) los chunks recuperados formateados como `[Fuente: <source>]\n<content>`, (3) la pregunta del usuario. Claude SHALL responder "No tengo información suficiente en los documentos proporcionados" si la respuesta no está en el contexto.

#### Scenario: Respuesta anclada al contexto
- **WHEN** el contexto recuperado contiene la respuesta a la pregunta del usuario
- **THEN** Claude genera una respuesta que cita explícitamente la fuente (`source`) del chunk usado

#### Scenario: Respuesta fuera del contexto
- **WHEN** la pregunta no tiene respuesta en los chunks recuperados
- **THEN** Claude retorna "No tengo información suficiente en los documentos proporcionados" sin inventar información

---

### Requirement: Endpoint POST /query
El sistema SHALL exponer `POST /query` que acepta `{"question": "string"}` y retorna `{"answer": "string", "sources": ["source1", "source2"]}` con la respuesta de Claude y la lista de fuentes únicas de los chunks usados.

#### Scenario: Query exitosa con sources
- **WHEN** el cliente envía `POST /query` con una pregunta que tiene respuesta en los documentos
- **THEN** el endpoint retorna HTTP 200 con `answer` y `sources` no vacíos en menos de 10 segundos

#### Scenario: Query sin documentos ingestados
- **WHEN** la tabla `documents` está vacía y el cliente envía `POST /query`
- **THEN** el endpoint retorna `{"answer": "No tengo información suficiente en los documentos proporcionados", "sources": []}`

---

### Requirement: Límite de contexto por llamada a Claude
El total de caracteres de los chunks en el prompt SHALL ser limitado a un máximo configurable (`RAG_MAX_CONTEXT_CHARS`, default `8000`) para evitar superar el context window del modelo.

#### Scenario: Contexto truncado al límite
- **WHEN** los top-K chunks sumados superan `RAG_MAX_CONTEXT_CHARS`
- **THEN** el sistema incluye solo los primeros chunks hasta el límite, en orden de relevancia RRF
