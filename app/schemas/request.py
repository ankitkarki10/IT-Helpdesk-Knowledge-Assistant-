"""Request/Response schemas."""

from typing import List, Optional
from pydantic import BaseModel


# Request Schemas

class IngestRequest(BaseModel):
    """Request to ingest a document."""
    
    content: str
    source: Optional[str] = None
    metadata: Optional[dict] = None


class QueryRequest(BaseModel):
    """Request for intelligent query processing."""
    
    query: str
    include_reasoning: bool = False


class EvalRequest(BaseModel):
    """Request for batch evaluation."""
    
    queries: List[str]


# Response Schemas

class ChunkInfo(BaseModel):
    """Information about a retrieved chunk."""
    
    text: str
    metadata: dict
    distance: Optional[float] = None


class RoutingInfo(BaseModel):
    """Query routing information."""
    
    type: str
    reason: str
    tool: Optional[str] = None


class QueryResponse(BaseModel):
    """Response to a query."""
    
    query: str
    answer: str
    query_type: str
    routing_reason: str
    retrieved_documents: List[ChunkInfo] = []
    tool_used: Optional[str] = None
    latency_ms: Optional[float] = None
    tokens_used: Optional[int] = None


class IngestResponse(BaseModel):
    """Response to document ingestion."""
    
    success: bool
    chunks_created: int
    message: str


class EvalResponse(BaseModel):
    """Response to evaluation request."""
    
    total_queries: int
    results: List[QueryResponse]


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    message: str
    database_connected: bool
    chroma_initialized: bool
