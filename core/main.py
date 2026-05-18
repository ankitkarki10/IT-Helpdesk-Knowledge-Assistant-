import uvicorn
from fastapi import FastAPI
from core.config import settings
from core.logger import get_logger
from api.routes import router
from db.session import engine, Base, SessionLocal
from db.models import Employee
from tests.sample_data import SAMPLE_DOCS, SAMPLE_EMPLOYEES
from rag.ingest import ingest_document

logger = get_logger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    logger.info("Starting up API...")
    
    # Seed DB with sample data if empty
    db = SessionLocal()
    try:
        # Check employees
        if db.query(Employee).count() == 0:
            logger.info("Seeding DB with sample employees...")
            for emp_data in SAMPLE_EMPLOYEES:
                db.add(Employee(**emp_data))
            db.commit()
            
            logger.info("Seeding DB with sample documents...")
            for doc_data in SAMPLE_DOCS:
                ingest_document(db, doc_data["text"], doc_data["metadata"])
    except Exception as e:
        logger.error(f"Error during startup data seeding: {e}")
    finally:
        db.close()

app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.app_name}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
