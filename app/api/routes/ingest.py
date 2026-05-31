import uuid
import re
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.core.config import settings
from app.core.document_loader import load_from_bytes, split_documents
from app.core.rag_pipeline import embed_chunks
from app.core.security import verify_api_key
from app.db import vector_store
from app.models.response import IngestResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md"}
SAFE_FILENAME_RE = re.compile(r'^[\w\-. ]+$')


@router.post("/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def ingest_document(file: UploadFile = File(...)):
    _validate_file(file)

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum size limit")

    docs = load_from_bytes(content, file.filename)
    chunks = split_documents(docs)

    if not chunks:
        raise HTTPException(status_code=422, detail="No text could be extracted from the document")

    document_id = str(uuid.uuid4())
    embedded = embed_chunks(chunks)
    stored = vector_store.store_chunks(document_id, file.filename, embedded)

    return IngestResponse(
        document_id=document_id,
        filename=file.filename,
        chunks_created=stored,
        status="indexed",
    )


def _validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not SAFE_FILENAME_RE.match(file.filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
