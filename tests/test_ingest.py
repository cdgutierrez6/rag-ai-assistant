import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import io


@pytest.fixture
def client():
    with patch("app.main._init_db"):
        from app.main import app
        return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_unsupported_extension(client):
    file = io.BytesIO(b"content")
    response = client.post(
        "/ingest",
        files={"file": ("document.xyz", file, "application/octet-stream")},
    )
    assert response.status_code == 415


@patch("app.api.routes.ingest.load_from_bytes")
@patch("app.api.routes.ingest.split_documents")
@patch("app.api.routes.ingest.embed_chunks")
@patch("app.api.routes.ingest.vector_store.store_chunks")
def test_ingest_txt_success(mock_store, mock_embed, mock_split, mock_load, client):
    from langchain.schema import Document
    mock_load.return_value = [Document(page_content="sample text", metadata={})]
    mock_split.return_value = ["chunk one", "chunk two"]
    mock_embed.return_value = [("chunk one", [0.1] * 384), ("chunk two", [0.2] * 384)]
    mock_store.return_value = 2

    file = io.BytesIO(b"sample text content")
    response = client.post(
        "/ingest",
        files={"file": ("test.txt", file, "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["chunks_created"] == 2
    assert body["filename"] == "test.txt"
    assert body["status"] == "indexed"
