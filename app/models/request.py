from pydantic import BaseModel, Field
from typing import Optional
import uuid


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    top_k: int = Field(default=5, ge=1, le=20)
