from fastapi import APIRouter, HTTPException
from app.core import rag_pipeline
from app.db import session_store
from app.models.request import QueryRequest
from app.models.response import QueryResponse, HistoryResponse, HistoryMessage

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        return rag_pipeline.query(
            question=request.question,
            session_id=request.session_id,
            top_k=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    messages = session_store.get_history(session_id, limit=50)
    return HistoryResponse(
        session_id=session_id,
        messages=[HistoryMessage(**m) for m in messages],
    )


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    from app.db.vector_store import SessionLocal
    from sqlalchemy import text
    with SessionLocal() as db:
        db.execute(
            text("DELETE FROM conversation_history WHERE session_id = :sid"),
            {"sid": session_id},
        )
        db.commit()
    return {"status": "cleared", "session_id": session_id}
