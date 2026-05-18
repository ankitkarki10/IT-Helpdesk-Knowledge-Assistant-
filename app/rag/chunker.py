"""Document chunking utilities."""

import re
from typing import List
from app.core.config import settings, get_logger

logger = get_logger(__name__)


class DocumentChunker:
    """Split documents into chunks with overlap."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Size of each chunk in tokens (approximate)
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        logger.info(
            f"DocumentChunker initialized with "
            f"chunk_size={self.chunk_size}, overlap={self.chunk_overlap}"
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (1 token ≈ 4 characters)."""
        return len(text) // 4
    
    def chunk(self, text: str, metadata: dict = None) -> List[dict]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to chunker")
            return []
        
        # Split by sentences/paragraphs
        sentences = re.split(r'(?<=[.!?])\s+|\n\n+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = self._estimate_tokens(sentence)
            
            # If adding this sentence exceeds chunk size
            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata or {},
                    "size": self._estimate_tokens(chunk_text),
                })
                
                # Start new chunk with overlap
                overlap_text = " ".join(current_chunk[-(self.chunk_overlap // 50):])
                current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                current_size = self._estimate_tokens(" ".join(current_chunk))
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": metadata or {},
                "size": self._estimate_tokens(chunk_text),
            })
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks


def chunk_document(text: str, metadata: dict = None) -> List[dict]:
    """Convenience function to chunk a document."""
    chunker = DocumentChunker()
    return chunker.chunk(text, metadata)
