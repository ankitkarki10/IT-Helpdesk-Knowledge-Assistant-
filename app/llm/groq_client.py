"""Groq LLM client wrapper."""

import time
from groq import Groq
from app.core.config import settings, get_logger

logger = get_logger(__name__)


class GroqClient:
    """Wrapper for Groq API."""
    
    def __init__(self):
        """Initialize Groq client."""
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.llm_model
        logger.info(f"Groq client initialized with model: {self.model}")
    
    def generate(
        self,
        messages: list,
        temperature: float = None,
        max_tokens: int = None,
    ) -> dict:
        """
        Generate response from Groq LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with 'response', 'tokens', 'latency_ms'
        """
        if temperature is None:
            temperature = settings.llm_temperature
        if max_tokens is None:
            max_tokens = settings.llm_max_tokens
        
        try:
            start_time = time.time()
            
            logger.info(f"Calling Groq API with {len(messages)} messages")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response.usage.total_tokens if response.usage else None
            
            logger.info(
                f"Groq response received. "
                f"Latency: {latency_ms:.2f}ms, Tokens: {tokens_used}"
            )
            
            return {
                "response": response.choices[0].message.content,
                "tokens": tokens_used,
                "latency_ms": latency_ms,
            }
        
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise


# Global client instance
_groq_client = None


def get_groq_client() -> GroqClient:
    """Get or create Groq client (singleton)."""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
