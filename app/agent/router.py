"""Smart agent router for query classification."""

import json
import re
from typing import List
from app.core.config import settings, get_logger
from app.llm.groq_client import get_groq_client
from app.tools.calculator import calculate

logger = get_logger(__name__)


class AgentRouter:
    """Route queries to appropriate handlers (RAG, DB, TOOL, LLM, MULTI)."""
    
    QUERY_TYPES = {
        "RAG": "Retrieve from internal documents/knowledge base",
        "DB": "Query structured company data",
        "TOOL": "Perform calculations or use tools",
        "LLM": "Answer general knowledge questions",
        "MULTI": "Combine multiple sources",
    }
    
    def __init__(self):
        """Initialize router."""
        self.llm_client = get_groq_client()
        logger.info("AgentRouter initialized")
    
    def classify_query(self, query: str) -> dict:
        """
        Classify query type using LLM.
        
        Args:
            query: User query
            
        Returns:
            Dict with 'type' and 'reason'
        """
        prompt = f"""You are a query router for an IT helpdesk system. Classify the following query into ONE of these types:

- RAG: Retrieve from internal documents/processes/policies
- DB: Query structured company data (employees, departments, etc.)
- TOOL: Perform calculations or tool operations
- LLM: General knowledge question or chitchat
- MULTI: Combines multiple sources

Query: {query}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{"type": "RAG|DB|TOOL|LLM|MULTI", "reason": "Brief explanation"}}"""
        
        try:
            response = self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=256,
            )
            
            response_text = response["response"].strip()
            logger.info(f"Router response: {response_text}")
            
            # Extract JSON from response
            try:
                # Try direct JSON parsing
                classification = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks or other text
                json_match = re.search(r'\{[^{}]*"type"[^{}]*"reason"[^{}]*\}', response_text)
                if json_match:
                    classification = json.loads(json_match.group())
                else:
                    logger.warning(f"Failed to parse router response: {response_text}")
                    # Default to LLM if parsing fails
                    classification = {"type": "LLM", "reason": "Default routing due to parse error"}
            
            # Validate and clean response
            if "type" not in classification:
                classification["type"] = "LLM"
            if "reason" not in classification:
                classification["reason"] = "Auto-generated reason"
            
            # Ensure type is valid
            if classification["type"] not in self.QUERY_TYPES:
                logger.warning(f"Invalid query type: {classification['type']}")
                classification["type"] = "LLM"
            
            logger.info(f"Query classified as: {classification['type']}")
            return classification
        
        except Exception as e:
            logger.error(f"Error classifying query: {str(e)}")
            return {"type": "LLM", "reason": "Error in classification, defaulting to LLM"}
    
    def detect_calculation(self, query: str) -> tuple[bool, str]:
        """
        Detect if query contains a calculation request.
        
        Args:
            query: User query
            
        Returns:
            (is_calculation, expression)
        """
        # Keywords that indicate calculation
        calc_keywords = [
            "calculate", "compute", "what is", "equals", "how much",
            "add", "subtract", "multiply", "divide", "plus", "minus",
            "times", "divided by", "sum", "total", "average",
        ]
        
        query_lower = query.lower()
        
        # Check if query contains calculation keywords
        has_calc_keyword = any(keyword in query_lower for keyword in calc_keywords)
        if not has_calc_keyword:
            return False, ""
        
        # Try to extract mathematical expression
        # Simple heuristic: look for numbers and operators
        math_pattern = r'[\d\s+\-*/().]+'
        matches = re.findall(math_pattern, query)
        
        if matches:
            expression = matches[-1].strip()
            # Validate expression contains operators
            if any(op in expression for op in ['+', '-', '*', '/', '(', ')']):
                return True, expression
        
        return False, ""
    
    def route(self, query: str) -> dict:
        """
        Route query to appropriate handler.
        
        Args:
            query: User query
            
        Returns:
            Routing decision with type, reason, and metadata
        """
        logger.info(f"Routing query: {query[:100]}...")
        
        # Check for explicit calculation
        is_calc, expression = self.detect_calculation(query)
        if is_calc:
            logger.info(f"Detected calculation: {expression}")
            return {
                "type": "TOOL",
                "reason": f"Mathematical calculation detected",
                "tool": "calculator",
                "expression": expression,
            }
        
        # Use LLM to classify
        classification = self.classify_query(query)
        
        return {
            "type": classification["type"],
            "reason": classification["reason"],
        }


def route_query(query: str) -> dict:
    """Convenience function to route a query."""
    router = AgentRouter()
    return router.route(query)
