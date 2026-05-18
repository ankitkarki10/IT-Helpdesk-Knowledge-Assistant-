"""Vector retrieval using ChromaDB."""

import json
from typing import List, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings, get_logger
from app.rag.embeddings import get_embedding_generator

logger = get_logger(__name__)


class VectorRetriever:
    """Retrieve documents from ChromaDB vector store."""
    
    def __init__(self, collection_name: str = "helpdesk_documents"):
        """
        Initialize vector retriever.
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        logger.info("Initializing ChromaDB client...")
        
        # Use persistent storage
        self.client = chromadb.PersistentClient(path="./chroma_data")
        self.collection_name = collection_name
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaDB collection '{collection_name}' initialized")
    
    def add_documents(self, chunks: List[dict]):
        """
        Add document chunks to vector store.
        
        Args:
            chunks: List of chunk dicts with 'text' and 'metadata'
        """
        if not chunks:
            logger.warning("No chunks to add")
            return
        
        embedding_gen = get_embedding_generator()
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{self.collection.count()}_{i}"
            text = chunk.get("text", "")
            metadata = chunk.get("metadata", {})
            
            # Generate embedding
            embedding = embedding_gen.embed(text)
            
            ids.append(chunk_id)
            embeddings.append(embedding.tolist())
            documents.append(text)
            metadatas.append(metadata)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        logger.info(f"Added {len(chunks)} chunks to vector store")
    
    def retrieve(self, query: str, top_k: int = None) -> List[dict]:
        """
        Retrieve top-k relevant documents.
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of retrieved documents with scores
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        
        embedding_gen = get_embedding_generator()
        query_embedding = embedding_gen.embed(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
        )
        
        retrieved = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                retrieved.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        
        logger.info(f"Retrieved {len(retrieved)} documents for query")
        return retrieved
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the collection."""
        return {
            "count": self.collection.count(),
            "name": self.collection_name,
        }


# Global instance
_vector_retriever = None


def get_vector_retriever(collection_name: str = "helpdesk_documents") -> VectorRetriever:
    """Get or create vector retriever (singleton)."""
    global _vector_retriever
    if _vector_retriever is None:
        _vector_retriever = VectorRetriever(collection_name)
    return _vector_retriever
