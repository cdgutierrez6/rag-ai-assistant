"""
Tests for POST /query, GET /history/{session_id}, DELETE /history/{session_id}
Covers: happy path, validation errors, pipeline exceptions, empty history, session isolation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    with patch("app.main._init_db"):
        from app.main import app
        return TestClient(app)


def _mock_query_response(answer="Test answer.", document="doc.pdf", similarity=0.91):
    """Build a minimal QueryResponse-like mock."""
    from app.models.response import QueryResponse, SourceChunk
    return QueryResponse(
        answer=answer,
        sources=[SourceChunk(document=document, chunk="relevant content", similarity=similarity)],
        session_id="session-abc",
    )


# ── POST /query — happy path ──────────────────────────────────────────────────

class TestQueryEndpointHappyPath:

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_returns_answer_and_sources(self, mock_pipeline, client):
        mock_pipeline.return_value = _mock_query_response()

        resp = client.post("/query", json={
            "question": "What is the refund policy?",
            "session_id": "session-abc",
            "top_k": 5,
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "Test answer."
        assert len(body["sources"]) == 1
        assert body["sources"][0]["document"] == "doc.pdf"
        assert body["session_id"] == "session-abc"

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_generates_session_id_when_omitted(self, mock_pipeline, client):
        mock_pipeline.return_value = _mock_query_response()

        resp = client.post("/query", json={"question": "Hello world?"})

        assert resp.status_code == 200
        # session_id auto-generated — must be present and non-empty
        assert resp.json()["session_id"]

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_passes_top_k_to_pipeline(self, mock_pipeline, client):
        mock_pipeline.return_value = _mock_query_response()

        client.post("/query", json={"question": "Some question here?", "top_k": 3})

        _, kwargs = mock_pipeline.call_args
        assert kwargs.get("top_k") == 3 or mock_pipeline.call_args[0][2] == 3

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_with_max_top_k(self, mock_pipeline, client):
        mock_pipeline.return_value = _mock_query_response()

        resp = client.post("/query", json={"question": "Big question here?", "top_k": 20})

        assert resp.status_code == 200

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_response_has_correct_similarity_score(self, mock_pipeline, client):
        mock_pipeline.return_value = _mock_query_response(similarity=0.98)

        resp = client.post("/query", json={"question": "High similarity query?"})

        assert resp.status_code == 200
        assert resp.json()["sources"][0]["similarity"] == pytest.approx(0.98, abs=1e-3)


# ── POST /query — validation errors (422) ────────────────────────────────────

class TestQueryEndpointValidation:

    def test_query_rejects_empty_question(self, client):
        resp = client.post("/query", json={"question": ""})
        assert resp.status_code == 422

    def test_query_rejects_question_too_short(self, client):
        # min_length=3 → "ab" should fail
        resp = client.post("/query", json={"question": "ab"})
        assert resp.status_code == 422

    def test_query_rejects_question_too_long(self, client):
        resp = client.post("/query", json={"question": "A" * 2001})
        assert resp.status_code == 422

    def test_query_rejects_top_k_zero(self, client):
        resp = client.post("/query", json={"question": "Valid question?", "top_k": 0})
        assert resp.status_code == 422

    def test_query_rejects_top_k_negative(self, client):
        resp = client.post("/query", json={"question": "Valid question?", "top_k": -1})
        assert resp.status_code == 422

    def test_query_rejects_top_k_above_max(self, client):
        resp = client.post("/query", json={"question": "Valid question?", "top_k": 21})
        assert resp.status_code == 422

    def test_query_rejects_missing_question_field(self, client):
        resp = client.post("/query", json={"top_k": 5})
        assert resp.status_code == 422

    def test_query_rejects_null_question(self, client):
        resp = client.post("/query", json={"question": None})
        assert resp.status_code == 422


# ── POST /query — error paths ─────────────────────────────────────────────────

class TestQueryEndpointErrors:

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_returns_500_when_pipeline_raises(self, mock_pipeline, client):
        mock_pipeline.side_effect = RuntimeError("pgvector connection lost")

        resp = client.post("/query", json={"question": "This will fail internally"})

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Internal server error"

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_returns_500_when_llm_raises(self, mock_pipeline, client):
        mock_pipeline.side_effect = Exception("Anthropic API rate limit exceeded")

        resp = client.post("/query", json={"question": "Rate limited query here"})

        assert resp.status_code == 500

    @patch("app.api.routes.query.rag_pipeline.query")
    def test_query_handles_empty_sources_list(self, mock_pipeline, client):
        from app.models.response import QueryResponse
        mock_pipeline.return_value = QueryResponse(
            answer="No documents found.",
            sources=[],
            session_id="no-docs-session",
        )

        resp = client.post("/query", json={"question": "Question with no matches?"})

        assert resp.status_code == 200
        assert resp.json()["sources"] == []


# ── GET /history/{session_id} ─────────────────────────────────────────────────

class TestGetHistory:

    @patch("app.api.routes.query.session_store.get_history")
    def test_get_history_returns_messages(self, mock_history, client):
        mock_history.return_value = [
            {"role": "user",      "content": "Hello?",     "created_at": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!",  "created_at": "2024-01-01T00:00:01"},
        ]

        resp = client.get("/history/session-xyz")

        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == "session-xyz"
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][1]["role"] == "assistant"

    @patch("app.api.routes.query.session_store.get_history")
    def test_get_history_returns_empty_list_for_new_session(self, mock_history, client):
        mock_history.return_value = []

        resp = client.get("/history/brand-new-session")

        assert resp.status_code == 200
        assert resp.json()["messages"] == []

    @patch("app.api.routes.query.session_store.get_history")
    def test_get_history_passes_correct_session_id(self, mock_history, client):
        mock_history.return_value = []
        target_session = "my-specific-session-001"

        client.get(f"/history/{target_session}")

        mock_history.assert_called_once_with(target_session, limit=50)

    @patch("app.api.routes.query.session_store.get_history")
    def test_get_history_sessions_are_isolated(self, mock_history, client):
        """Different sessions should never bleed into each other."""
        def side_effect(session_id, limit):
            if session_id == "session-A":
                return [{"role": "user", "content": "From A", "created_at": "2024-01-01T00:00:00"}]
            return []

        mock_history.side_effect = side_effect

        resp_a = client.get("/history/session-A")
        resp_b = client.get("/history/session-B")

        assert len(resp_a.json()["messages"]) == 1
        assert len(resp_b.json()["messages"]) == 0


# ── DELETE /history/{session_id} ─────────────────────────────────────────────

class TestDeleteHistory:

    @patch("app.api.routes.query.SessionLocal")
    def test_delete_history_returns_cleared_status(self, mock_session_local, client):
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session_local.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.delete("/history/session-to-delete")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "cleared"
        assert body["session_id"] == "session-to-delete"

    @patch("app.api.routes.query.SessionLocal")
    def test_delete_history_executes_delete_query(self, mock_session_local, client):
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session_local.return_value.__exit__ = MagicMock(return_value=False)

        client.delete("/history/session-to-delete")

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
