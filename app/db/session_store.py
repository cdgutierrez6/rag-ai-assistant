from typing import List, Dict
from sqlalchemy import text
from app.db.vector_store import SessionLocal


def append_message(session_id: str, role: str, content: str) -> None:
    with SessionLocal() as db:
        db.execute(
            text("""
                INSERT INTO conversation_history (session_id, role, content)
                VALUES (:session_id, :role, :content)
            """),
            {"session_id": session_id, "role": role, "content": content},
        )
        db.commit()


def get_history(session_id: str, limit: int = 10) -> List[Dict[str, str]]:
    with SessionLocal() as db:
        result = db.execute(
            text("""
                SELECT role, content FROM conversation_history
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                LIMIT :limit
            """),
            {"session_id": session_id, "limit": limit},
        )
        return [{"role": row.role, "content": row.content} for row in result]
