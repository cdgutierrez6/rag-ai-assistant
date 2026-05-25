from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.routes import ingest, query
from app.db.vector_store import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


def _init_db():
    import os
    sql_path = os.path.join(os.path.dirname(__file__), "db", "init.sql")
    with open(sql_path) as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


app = FastAPI(
    title="RAG AI Assistant",
    description="Retrieval Augmented Generation con Claude API y pgvector",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(query.router, tags=["Query"])


@app.get("/health")
async def health():
    return {"status": "ok"}
