"""Main FastAPI application."""

import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings, get_logger
from app.db.database import init_db, get_db, QueryLog
from app.schemas.request import (
    IngestRequest, QueryRequest, EvalRequest,
    IngestResponse, QueryResponse, EvalResponse, HealthResponse
)
from app.services.query_service import get_query_service

logger = get_logger(__name__)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Internal IT Helpdesk & Knowledge Assistant with RAG + Agent system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoint

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Check system health."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        db_connected = False
    
    # ChromaDB is initialized on first use, assume connected for now
    chroma_initialized = True
    
    return HealthResponse(
        status="healthy" if (db_connected and chroma_initialized) else "degraded",
        message="System is operational",
        database_connected=db_connected,
        chroma_initialized=chroma_initialized,
    )


# Document Ingestion Endpoint

@app.post("/ingest", response_model=IngestResponse, tags=["Documents"])
def ingest_document(
    request: IngestRequest,
    db: Session = Depends(get_db),
):
    """Ingest a document into the knowledge base."""
    try:
        logger.info(f"Ingesting document from {request.source or 'unknown'}")
        
        service = get_query_service(db)
        chunks_created = service.ingest_document(
            content=request.content,
            source=request.source,
            metadata=request.metadata,
        )
        
        return IngestResponse(
            success=True,
            chunks_created=chunks_created,
            message=f"Document ingested successfully with {chunks_created} chunks",
        )
    
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting document: {str(e)}"
        )


# Query Endpoint

@app.post("/query", response_model=QueryResponse, tags=["Queries"])
def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """Process an intelligent query using RAG + Agent system."""
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        service = get_query_service(db)
        result = service.process_query(request.query)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


# Batch Evaluation Endpoint

@app.post("/eval", response_model=EvalResponse, tags=["Evaluation"])
def evaluate_queries(
    request: EvalRequest,
    db: Session = Depends(get_db),
):
    """Run batch evaluation on multiple queries."""
    try:
        logger.info(f"Evaluating {len(request.queries)} queries")
        
        service = get_query_service(db)
        results = []
        
        for query in request.queries:
            try:
                result = service.process_query(query)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating query '{query}': {str(e)}")
                # Still add to results but with error
                results.append(
                    QueryResponse(
                        query=query,
                        answer=f"Error: {str(e)}",
                        query_type="ERROR",
                        routing_reason="Error occurred",
                    )
                )
        
        return EvalResponse(
            total_queries=len(request.queries),
            results=results,
        )
    
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch evaluation: {str(e)}"
        )


# Query Logs Endpoint (for debugging)

@app.get("/logs", tags=["Debug"])
def get_query_logs(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get recent query logs (debug endpoint)."""
    try:
        logs = db.query(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit).all()
        
        return {
            "total": len(logs),
            "logs": [
                {
                    "id": log.id,
                    "query": log.query,
                    "type": log.query_type,
                    "latency_ms": log.latency_ms,
                    "error": log.error,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching logs")


# Root endpoint

@app.get("/", tags=["Info"])
def root():
    """Welcome endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "ingest": "POST /ingest",
            "query": "POST /query",
            "eval": "POST /eval",
            "logs": "GET /logs",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
