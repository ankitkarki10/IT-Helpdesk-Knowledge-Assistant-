"""Query service - main orchestration logic."""

import time
import json
from typing import List
from sqlalchemy.orm import Session
from app.core.config import settings, get_logger
from app.db.database import Document, QueryLog
from app.llm.groq_client import get_groq_client
from app.rag.chunker import chunk_document
from app.rag.retriever import get_vector_retriever
from app.agent.router import AgentRouter
from app.tools.calculator import calculate
from app.schemas.request import QueryResponse, ChunkInfo

logger = get_logger(__name__)


class QueryService:
    """Main service for processing queries."""
    
    def __init__(self, db: Session):
        """
        Initialize query service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.llm_client = get_groq_client()
        self.router = AgentRouter()
        self.retriever = get_vector_retriever()
    
    def ingest_document(self, content: str, source: str = None, metadata: dict = None) -> int:
        """
        Ingest a document into the system.
        
        Args:
            content: Document content
            source: Document source/filename
            metadata: Additional metadata
            
        Returns:
            Number of chunks created
        """
        logger.info(f"Ingesting document from {source or 'unknown source'}")
        
        if metadata is None:
            metadata = {}
        if source:
            metadata["source"] = source
        
        # Chunk document
        chunks = chunk_document(content, metadata)
        
        if not chunks:
            logger.warning("No chunks created from document")
            return 0
        
        # Store document in database
        doc = Document(
            content=content,
            source=source,
            meta_data=metadata,
        )
        self.db.add(doc)
        self.db.commit()
        logger.info(f"Stored document in database with ID {doc.id}")
        
        # Add chunks to vector store
        self.retriever.add_documents(chunks)
        
        logger.info(f"Ingested document with {len(chunks)} chunks")
        return len(chunks)
    
    def _retrieve_rag_context(self, query: str, top_k: int = None) -> tuple[str, List[dict]]:
        """
        Retrieve context from RAG pipeline.
        
        Args:
            query: Query text
            top_k: Number of results to retrieve
            
        Returns:
            (context_text, retrieved_docs)
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        
        retrieved = self.retriever.retrieve(query, top_k)
        
        if not retrieved:
            return "", []
        
        # Build context from retrieved documents
        context_parts = []
        for doc in retrieved:
            context_parts.append(doc["text"])
        
        context = "\n\n---\n\n".join(context_parts)
        return context, retrieved
    
    def _generate_rag_response(self, query: str, context: str) -> str:
        """
        Generate response using RAG context.
        
        Args:
            query: Original query
            context: Retrieved context
            
        Returns:
            Generated response
        """
        prompt = f"""You are an IT Helpdesk Assistant. Answer the following question using the provided context.

Context from internal documents:
{context}

Question: {query}

Provide a helpful, accurate answer based on the context. If the context doesn't contain relevant information, say so clearly."""
        
        response = self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        
        return response["response"]
    
    def _handle_tool_query(self, routing_info: dict) -> str:
        """
        Handle tool-based query (calculation).
        
        Args:
            routing_info: Routing information from router
            
        Returns:
            Tool execution result
        """
        if routing_info.get("tool") == "calculator":
            expression = routing_info.get("expression", "")
            try:
                result = calculate(expression)
                return f"Result of {expression} = {result}"
            except Exception as e:
                logger.error(f"Calculator error: {str(e)}")
                return f"Error calculating: {str(e)}"
        
        return "Unknown tool"
    
    def _generate_llm_response(self, query: str) -> str:
        """
        Generate response using LLM only (general knowledge).
        
        Args:
            query: User query
            
        Returns:
            Generated response
        """
        prompt = f"""You are an IT Helpdesk Assistant. Answer the following question helpfully and accurately.

Question: {query}

Provide a clear, concise answer."""
        
        response = self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        
        return response["response"]
    
    def _generate_multi_response(self, query: str, context: str = "") -> str:
        """
        Generate response using multiple sources.
        
        Args:
            query: User query
            context: Optional RAG context
            
        Returns:
            Generated response
        """
        prompt_parts = [
            "You are an IT Helpdesk Assistant. Answer the following question using all available information.",
            ""
        ]
        
        if context:
            prompt_parts.append("Available context from internal documents:")
            prompt_parts.append(context)
            prompt_parts.append("")
        
        prompt_parts.extend([
            f"Question: {query}",
            "",
            "Provide a comprehensive answer combining all relevant information."
        ])
        
        prompt = "\n".join(prompt_parts)
        
        response = self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        
        return response["response"]
    
    def process_query(self, query: str) -> QueryResponse:
        """
        Process a user query end-to-end.
        
        Args:
            query: User query
            
        Returns:
            QueryResponse with answer and metadata
        """
        start_time = time.time()
        retrieved_docs = []
        tool_used = None
        error = None
        tokens_used = None
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Route query
            routing_info = self.router.route(query)
            query_type = routing_info.get("type", "LLM")
            reason = routing_info.get("reason", "")
            
            logger.info(f"Query routed to: {query_type}")
            
            # Process based on type
            answer = ""
            
            if query_type == "RAG":
                context, retrieved_docs = self._retrieve_rag_context(query)
                answer = self._generate_rag_response(query, context)
            
            elif query_type == "TOOL":
                tool_used = routing_info.get("tool", "unknown")
                answer = self._handle_tool_query(routing_info)
            
            elif query_type == "DB":
                # For now, generate a response indicating DB query
                answer = self._generate_llm_response(
                    f"{query} [DB Query - would fetch from company database]"
                )
            
            elif query_type == "MULTI":
                context, retrieved_docs = self._retrieve_rag_context(query)
                answer = self._generate_multi_response(query, context)
            
            else:  # LLM
                answer = self._generate_llm_response(query)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Log query to database
            query_log = QueryLog(
                query=query,
                query_type=query_type,
                routing_reason=reason,
                response=answer,
                retrieved_documents=[
                    {"text": doc["text"], "metadata": doc["metadata"]}
                    for doc in retrieved_docs
                ],
                tool_used=tool_used,
                latency_ms=latency_ms,
            )
            self.db.add(query_log)
            self.db.commit()
            
            logger.info(f"Query processed in {latency_ms:.2f}ms")
            
            return QueryResponse(
                query=query,
                answer=answer,
                query_type=query_type,
                routing_reason=reason,
                retrieved_documents=[
                    ChunkInfo(
                        text=doc["text"],
                        metadata=doc["metadata"],
                        distance=doc.get("distance"),
                    )
                    for doc in retrieved_docs
                ],
                tool_used=tool_used,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
            )
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            error = str(e)
            
            # Log error
            query_log = QueryLog(
                query=query,
                query_type="ERROR",
                routing_reason="Error occurred",
                response="",
                error=error,
                latency_ms=(time.time() - start_time) * 1000,
            )
            self.db.add(query_log)
            self.db.commit()
            
            raise


def get_query_service(db: Session) -> QueryService:
    """Get a query service instance."""
    return QueryService(db)
