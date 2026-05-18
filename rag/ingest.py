import json
import uuid
from sqlalchemy.orm import Session
from core.llm import llm_service
from db.models import Document, Chunk
from db.chroma import collection
from core.logger import get_logger

logger = get_logger(__name__)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def ingest_document(db: Session, text: str, metadata: dict) -> tuple[int, int]:
    logger.info(f"Ingesting document with metadata: {metadata}")
    
    doc = Document(content=text, metadata_json=json.dumps(metadata))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    text_chunks = chunk_text(text)
    if not text_chunks:
        return doc.id, 0
        
    embeddings = llm_service.generate_embeddings(text_chunks)
    
    chunk_ids = [str(uuid.uuid4()) for _ in text_chunks]
    # Filter metadata so it doesn't contain non-string/int/float types, which Chroma doesn't like
    safe_metadata = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float))}
    metadatas = [{"document_id": doc.id, **safe_metadata} for _ in text_chunks]
    
    collection.add(
        documents=text_chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=chunk_ids
    )
    
    # Keep SQLite storage for fallback/consistency
    db_chunks = []
    for cid, chunk, emb in zip(chunk_ids, text_chunks, embeddings):
        db_chunk = Chunk(
            document_id=doc.id,
            content=chunk,
            embedding=json.dumps(emb)
        )
        db_chunks.append(db_chunk)
        
    db.add_all(db_chunks)
    db.commit()
    
    logger.info(f"Ingested {len(text_chunks)} chunks for document {doc.id} into ChromaDB")
    return doc.id, len(text_chunks)
