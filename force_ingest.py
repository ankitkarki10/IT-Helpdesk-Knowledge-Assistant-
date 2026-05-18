from db.session import SessionLocal
from tests.sample_data import SAMPLE_DOCS
from rag.ingest import ingest_document

def main():
    db = SessionLocal()
    print("Force ingesting sample documents into ChromaDB...")
    try:
        for doc_data in SAMPLE_DOCS:
            ingest_document(db, doc_data["text"], doc_data["metadata"])
        print("Ingestion complete.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
