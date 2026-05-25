import uuid
from typing import List, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def store_chunks(document_id: str, filename: str, chunks: List[Tuple[str, List[float]]]) -> int:
    with SessionLocal() as db:
        for content, embedding in chunks:
            db.execute(
                text("""
                    INSERT INTO document_chunks (id, document_id, filename, content, embedding)
                    VALUES (:id, :document_id, :filename, :content, :embedding)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "filename": filename,
                    "content": content,
                    "embedding": embedding,
                },
            )
        db.commit()
    return len(chunks)


def similarity_search(query_embedding: List[float], top_k: int) -> List[dict]:
    with SessionLocal() as db:
        result = db.execute(
            text("""
                SELECT filename, content, 1 - (embedding <=> :embedding::vector) AS similarity
                FROM document_chunks
                ORDER BY embedding <=> :embedding::vector
                LIMIT :top_k
            """),
            {"embedding": query_embedding, "top_k": top_k},
        )
        return [
            {"document": row.filename, "chunk": row.content, "similarity": float(row.similarity)}
            for row in result
        ]
