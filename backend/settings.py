"""Settings and configuration management using Pydantic."""
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    GOOGLE_API_KEY: str = ""
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    SUPPORT_DOCS_DIR: Path = ASSETS_DIR / "support_docs"
    FAISS_INDEX_DIR: Path = BASE_DIR / "faiss_index"
    
    # FAISS Settings
    FAISS_INDEX_NAME: str = "qa_knowledge_base"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    
    # LLM Settings
    LLM_MODEL: str = "models/gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_OUTPUT_TOKENS: int = 4096
    
    # Text Splitting
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    
    # RAG Settings
    RAG_TOP_K: int = 5
    
    # FastAPI Settings
    API_TITLE: str = "Autonomous QA Agent API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.ASSETS_DIR.mkdir(exist_ok=True)
settings.SUPPORT_DOCS_DIR.mkdir(exist_ok=True)
settings.FAISS_INDEX_DIR.mkdir(exist_ok=True)
