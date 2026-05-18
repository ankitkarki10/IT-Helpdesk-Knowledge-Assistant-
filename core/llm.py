import os
from typing import List
from groq import Groq
from sentence_transformers import SentenceTransformer
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        
        logger.info("Loading sentence-transformers model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully.")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"Generating embeddings for {len(texts)} texts.")
        embeddings = self.embedding_model.encode(texts)
        return embeddings.tolist()

    def generate_completion(self, prompt: str, max_tokens: int = 1024) -> str:
        if not self.client:
            logger.info("Using mock completion. No GROQ_API_KEY provided.")
            return f"[Mock Response for]: {prompt[:50]}..."

        try:
            logger.info("Calling Groq API...")
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                max_completion_tokens=max_tokens,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return "Error generating response."

llm_service = LLMService()
