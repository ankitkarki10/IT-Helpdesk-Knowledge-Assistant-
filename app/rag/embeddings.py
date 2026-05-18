"""Embedding generation using sentence-transformers."""

import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings, get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding model.
        
        Args:
            model_name: Name of sentence-transformers model
        """
        self.model_name = model_name or settings.embedding_model
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info(f"Embedding model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: list) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of embeddings
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return np.array([])
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings


# Global instance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create embedding generator (singleton)."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator


def embed_text(text: str) -> np.ndarray:
    """Convenience function to embed text."""
    return get_embedding_generator().embed(text)


def embed_texts(texts: list) -> np.ndarray:
    """Convenience function to embed multiple texts."""
    return get_embedding_generator().embed_batch(texts)
