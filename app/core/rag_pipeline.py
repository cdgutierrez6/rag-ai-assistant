from typing import List, Tuple
import anthropic
from app.core.config import settings
from app.db import vector_store, session_store
from app.models.response import SourceChunk, QueryResponse


_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def embed_text(text: str) -> List[float]:
    # Claude doesn't expose a standalone embeddings endpoint yet;
    # use a local sentence-transformers model as the embedding layer.
    # This keeps the LLM (Claude) separate from the retrieval layer.
    from sentence_transformers import SentenceTransformer
    _model = _get_embedding_model()
    return _model.encode(text).tolist()


_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embedding_model


def embed_chunks(chunks: List[str]) -> List[Tuple[str, List[float]]]:
    model = _get_embedding_model()
    embeddings = model.encode(chunks, batch_size=32, show_progress_bar=False)
    return list(zip(chunks, [e.tolist() for e in embeddings]))


def query(question: str, session_id: str, top_k: int) -> QueryResponse:
    query_embedding = embed_text(question)
    raw_sources = vector_store.similarity_search(query_embedding, top_k)

    sources = [
        SourceChunk(
            document=s["document"],
            chunk=s["chunk"],
            similarity=s["similarity"],
        )
        for s in raw_sources
    ]

    context = "\n\n".join(
        f"[Fuente: {s.document}]\n{s.chunk}" for s in sources
    )

    history = session_store.get_history(session_id)
    messages = _build_messages(history, question, context)

    response = _client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=_system_prompt(),
        messages=messages,
    )

    answer = response.content[0].text

    session_store.append_message(session_id, "user", question)
    session_store.append_message(session_id, "assistant", answer)

    return QueryResponse(answer=answer, sources=sources, session_id=session_id)


def _system_prompt() -> str:
    return (
        "Eres un asistente experto que responde preguntas basándose ÚNICAMENTE "
        "en el contexto de documentos proporcionados. "
        "Si la respuesta no está en el contexto, dilo explícitamente. "
        "Cita siempre el documento fuente al final de tu respuesta. "
        "Responde en el mismo idioma de la pregunta."
    )


def _build_messages(history: List[dict], question: str, context: str) -> List[dict]:
    messages = []

    for msg in history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = (
        f"Contexto de los documentos:\n\n{context}\n\n"
        f"Pregunta: {question}"
    )
    messages.append({"role": "user", "content": user_content})

    return messages
