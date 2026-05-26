from unittest.mock import patch, MagicMock
from app.core.document_loader import split_documents
from langchain.schema import Document


def test_split_documents_basic():
    docs = [Document(page_content="Hello world. " * 100, metadata={})]
    chunks = split_documents(docs)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 600  # chunk_size + some tolerance


def test_split_documents_empty():
    docs = [Document(page_content="   ", metadata={})]
    chunks = split_documents(docs)
    assert chunks == []


def test_split_documents_short():
    docs = [Document(page_content="Short text.", metadata={})]
    chunks = split_documents(docs)
    assert len(chunks) == 1
    assert chunks[0] == "Short text."


@patch("app.core.rag_pipeline._get_embedding_model")
def test_embed_chunks(mock_model):
    import numpy as np
    mock_instance = MagicMock()
    mock_instance.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
    mock_model.return_value = mock_instance

    from app.core.rag_pipeline import embed_chunks
    result = embed_chunks(["chunk one", "chunk two"])

    assert len(result) == 2
    assert result[0][0] == "chunk one"
    assert len(result[0][1]) == 384


@patch("app.core.rag_pipeline.vector_store.similarity_search")
@patch("app.core.rag_pipeline.session_store.get_history")
@patch("app.core.rag_pipeline.session_store.append_message")
@patch("app.core.rag_pipeline._client")
@patch("app.core.rag_pipeline.embed_text")
def test_query_returns_response(
    mock_embed, mock_client, mock_append, mock_history, mock_search
):
    mock_embed.return_value = [0.1] * 384
    mock_history.return_value = []
    mock_search.return_value = [
        {"document": "doc.pdf", "chunk": "relevant content", "similarity": 0.92}
    ]
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="La respuesta es X.")]
    mock_client.messages.create.return_value = mock_message

    from app.core.rag_pipeline import query
    response = query("¿Cuál es la respuesta?", "session-123", top_k=5)

    assert response.answer == "La respuesta es X."
    assert len(response.sources) == 1
    assert response.sources[0].document == "doc.pdf"
    assert response.session_id == "session-123"
