from sqlalchemy.orm import Session
from core.llm import llm_service
from db.chroma import collection
from core.logger import get_logger

logger = get_logger(__name__)

def retrieve_top_k(db: Session, query: str, k: int = 3) -> list[str]:
    logger.info(f"Retrieving top {k} chunks for query: '{query}'")
    
    # We pass the query directly to Chroma if we use its default embedding func, 
    # but we are using our custom embedding model via llm_service.
    query_embedding = llm_service.generate_embeddings([query])[0]
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )
    
    if not results or not results['documents'] or not results['documents'][0]:
        return []
        
    top_chunks = results['documents'][0]
    logger.info(f"Retrieved {len(top_chunks)} chunks from ChromaDB")
    return top_chunks
