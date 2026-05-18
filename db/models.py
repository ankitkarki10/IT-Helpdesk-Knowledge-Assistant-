import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from db.session import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # stored as JSON string of floats
    created_at = Column(DateTime, default=datetime.utcnow)

class QueryLog(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, index=True)
    input_query = Column(Text, nullable=False)
    output_response = Column(Text)
    routing_decision = Column(String)
    tools_used = Column(Text, default="[]")
    latency_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department = Column(String)
    role = Column(String)
    status = Column(String, default="active")
    account_type = Column(String, default="free")
    license_expiration = Column(DateTime, nullable=True)
