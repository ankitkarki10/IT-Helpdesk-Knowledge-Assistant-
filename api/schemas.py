from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class IngestRequest(BaseModel):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestResponse(BaseModel):
    status: str
    document_id: int
    chunks_created: int

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    routing_decision: str
    tools_used: List[str]
    retrieved_docs: List[str]
    db_result: Optional[Any] = None
    answer: str
    latency_ms: float
    success: bool = True

class EvalRequest(BaseModel):
    queries: Optional[List[str]] = None

class EvalResponse(BaseModel):
    results: List[QueryResponse]
    summary: Dict[str, Any]
