from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-opus-4-7"

    database_url: str = "postgresql://rag_user:rag_pass@localhost:5432/rag_db"

    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    max_file_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
