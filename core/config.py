import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "IT Helpdesk & Knowledge Assistant"
    database_url: str = "sqlite:///./helpdesk.db"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    embedding_dim: int = 768  # Kept 768 for mock embeddings

settings = Settings()
