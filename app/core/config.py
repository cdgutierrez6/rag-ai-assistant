from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-opus-4-7"

    # Required: set DATABASE_URL environment variable (see .env.example)
    # Format: postgresql://user:password@host:port/database
    database_url: str

    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    max_file_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
