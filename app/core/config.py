"""Configuration settings for the application."""

import logging
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings."""
    
    # App Configuration
    app_name: str = "IT Helpdesk & Knowledge Assistant"
    debug: bool = False
    
    # Database Configuration
    database_url: str = "sqlite:///./helpdesk.db"
    
    # Groq API Configuration
    groq_api_key: str = ""
    
    # RAG Configuration
    chunk_size: int = 600
    chunk_overlap: int = 100
    top_k_retrieval: int = 5
    
    # LLM Configuration
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept common deployment-style strings for debug mode."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"false", "0", "no", "off", "release", "prod", "production"}:
                return False
        return value
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings
settings = Settings()


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
