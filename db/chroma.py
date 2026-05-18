import chromadb
from core.logger import get_logger

logger = get_logger(__name__)

logger.info("Initializing ChromaDB persistent client...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="helpdesk_docs")
logger.info("ChromaDB initialized.")
