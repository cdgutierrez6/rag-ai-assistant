from pydantic import BaseModel
from typing import List, Optional


class SourceChunk(BaseModel):
    document: str
    chunk: str
    similarity: float
    page: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    session_id: str


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    status: str


class HistoryMessage(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[HistoryMessage]
