import time
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import QueryLog
from api.schemas import (
    IngestRequest, IngestResponse,
    QueryRequest, QueryResponse,
    EvalRequest, EvalResponse
)
from rag.ingest import ingest_document
from agent.router import process_query
from tests.sample_data import TEST_QUERIES

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
def api_ingest(request: IngestRequest, db: Session = Depends(get_db)):
    try:
        doc_id, num_chunks = ingest_document(db, request.text, request.metadata)
        return IngestResponse(
            status="success",
            document_id=doc_id,
            chunks_created=num_chunks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
def api_query(request: QueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    # Process the query using agent router
    result = process_query(db, request.query)
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Log query to DB
    try:
        q_log = QueryLog(
            input_query=request.query,
            output_response=result["answer"],
            routing_decision=result["routing_decision"],
            tools_used=json.dumps(result["tools_used"]),
            latency_ms=latency_ms
        )
        db.add(q_log)
        db.commit()
    except Exception as e:
        # We don't want DB logging failure to fail the entire request, but we should log it
        import logging
        logging.error(f"Failed to log query to DB: {e}")
        
    return QueryResponse(
        query=request.query,
        routing_decision=result["routing_decision"],
        tools_used=result["tools_used"],
        retrieved_docs=result["retrieved_docs"],
        db_result=result["db_result"],
        answer=result["answer"],
        latency_ms=latency_ms
    )

@router.post("/eval", response_model=EvalResponse)
def api_eval(request: EvalRequest, db: Session = Depends(get_db)):
    queries = request.queries if request.queries else TEST_QUERIES
    
    results = []
    total_latency = 0
    route_distribution = {}
    successful_queries = 0
    
    for q in queries:
        req = QueryRequest(query=q)
        resp = api_query(req, db)
        
        # Determine success heuristically
        resp.success = "error occurred" not in resp.answer.lower() and resp.answer.strip() != ""
        if resp.success:
            successful_queries += 1
            
        # Track distribution
        route = resp.routing_decision
        route_distribution[route] = route_distribution.get(route, 0) + 1
        
        results.append(resp)
        total_latency += resp.latency_ms
        
    avg_latency = total_latency / len(queries) if queries else 0
    
    return EvalResponse(
        results=results,
        summary={
            "total_queries": len(queries),
            "successful_queries": successful_queries,
            "success_rate_percentage": (successful_queries / len(queries) * 100) if queries else 0,
            "average_latency_ms": round(avg_latency, 2),
            "route_distribution": route_distribution
        }
    )
