"""Database setup and models."""

import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings, get_logger

logger = get_logger(__name__)

# Create engine with SQLite
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Document(Base):
    """Document model for storing ingested documents."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryLog(Base):
    """Query log model for tracking all queries."""
    
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)  # RAG, DB, TOOL, LLM, MULTI
    routing_reason = Column(Text, nullable=True)
    response = Column(Text, nullable=False)
    retrieved_documents = Column(JSON, default=[])
    tool_used = Column(String(100), nullable=True)
    latency_ms = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
