import re
from fastapi import APIRouter, Depends, HTTPException
from app.core import rag_pipeline
from app.core.security import verify_api_key
from app.db import session_store
from app.models.request import QueryRequest
from app.models.response import QueryResponse, HistoryResponse, HistoryMessage

router = APIRouter()

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE
)


@router.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
async def query_documents(request: QueryRequest):
    try:
        return rag_pipeline.query(
            question=request.question,
            session_id=request.session_id,
            top_k=request.top_k,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{session_id}", response_model=HistoryResponse, dependencies=[Depends(verify_api_key)])
async def get_history(session_id: str):
    if not _UUID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    messages = session_store.get_history(session_id, limit=50)
    return HistoryResponse(
        session_id=session_id,
        messages=[HistoryMessage(**m) for m in messages],
    )


@router.delete("/history/{session_id}", dependencies=[Depends(verify_api_key)])
async def clear_history(session_id: str):
    if not _UUID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    from app.db.vector_store import SessionLocal
    from sqlalchemy import text
    with SessionLocal() as db:
        db.execute(
            text("DELETE FROM conversation_history WHERE session_id = :sid"),
            {"sid": session_id},
        )
        db.commit()
    return {"status": "cleared", "session_id": session_id}
