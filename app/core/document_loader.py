import io
from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings


def load_from_bytes(content: bytes, filename: str) -> List[Document]:
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        return _load_pdf(content, filename)
    elif ext in ("docx", "doc"):
        return _load_docx(content, filename)
    elif ext in ("txt", "md"):
        return _load_text(content, filename)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def _load_pdf(content: bytes, filename: str) -> List[Document]:
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        loader = PyPDFLoader(tmp_path)
        return loader.load()
    finally:
        os.unlink(tmp_path)


def _load_docx(content: bytes, filename: str) -> List[Document]:
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        loader = Docx2txtLoader(tmp_path)
        return loader.load()
    finally:
        os.unlink(tmp_path)


def _load_text(content: bytes, filename: str) -> List[Document]:
    text = content.decode("utf-8", errors="replace")
    return [Document(page_content=text, metadata={"source": filename})]


def split_documents(docs: List[Document]) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    return [chunk.page_content for chunk in chunks if chunk.page_content.strip()]
