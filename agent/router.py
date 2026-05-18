import re
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.llm import llm_service
from core.logger import get_logger
from rag.retrieve import retrieve_top_k
from db.models import Employee
from tools.calculator import run_calculator
from tools.search import run_file_search

logger = get_logger(__name__)

def extract_math_expression(query: str) -> str:
    # Match basic expressions, convert text like 'x', 'times' if needed
    q_sub = query.replace('x', '*').replace('times', '*').replace('×', '*')
    match = re.search(r'[\d\+\-\*\/\(\)\. ]{3,}', q_sub)
    if match and any(op in match.group(0) for op in ['+', '-', '*', '/']):
        return match.group(0).strip()
    return ""

def classify_query(query: str) -> str:
    """Manually routes queries based on heuristics or scoring approach."""
    q_lower = query.lower()
    
    scores = {"TOOL": 0, "DB": 0, "RAG": 0, "LLM": 0}
    
    # Tool heuristics
    if re.search(r'\d+', q_lower) and any(op in q_lower for op in ['+', '-', '*', '/', 'calculate', 'math', 'times', 'convert', 'x', '×']):
        scores["TOOL"] += 2
        
    # DB heuristics
    db_keywords = ['employee', 'employees', 'user', 'users', 'department', 'role', 'active', 'inactive', 'account', 'paid', 'free', 'expiring', 'expire', 'hr', 'engineering', 'sales', 'product']
    db_matches = sum(1 for kw in db_keywords if kw in q_lower)
    if db_matches > 0:
        scores["DB"] += min(db_matches, 3)
        if any(ph in q_lower for ph in ["how many", "list", "show", "who"]):
            scores["DB"] += 1
            
    # RAG heuristics
    rag_keywords = ['policy', 'handbook', 'document', 'process', 'deploy', 'vpn', 'reset', 'portal', 'password', 'service', 'onboarding']
    rag_matches = sum(1 for kw in rag_keywords if kw in q_lower)
    if rag_matches > 0:
        scores["RAG"] += min(rag_matches, 3)
        
    # Multi heuristic
    if scores["DB"] >= 1 and scores["RAG"] >= 1 and ("and" in q_lower or "what" in q_lower or "how" in q_lower):
        return "MULTI"
        
    max_route = max(scores, key=scores.get)
    if scores[max_route] == 0:
        return "LLM"
        
    return max_route

def execute_db_query(db: Session, query: str) -> dict:
    """Dynamic DB query parsing and execution."""
    q_lower = query.lower()
    
    db_query = db.query(Employee)
    
    if "active" in q_lower and "inactive" not in q_lower:
        db_query = db_query.filter(Employee.status == "active")
    elif "inactive" in q_lower:
        db_query = db_query.filter(Employee.status == "inactive")
        
    if "paid" in q_lower:
        db_query = db_query.filter(Employee.account_type == "paid")
    elif "free" in q_lower:
        db_query = db_query.filter(Employee.account_type == "free")
        
    if "expiring" in q_lower or "expire" in q_lower:
        now = datetime.utcnow()
        next_month = now + timedelta(days=31)
        db_query = db_query.filter(Employee.license_expiration != None)
        db_query = db_query.filter(Employee.license_expiration <= next_month)
        db_query = db_query.filter(Employee.license_expiration >= now)
        
    if "hr" in q_lower:
        db_query = db_query.filter(func.lower(Employee.department) == "hr")
    elif "engineering" in q_lower:
        db_query = db_query.filter(func.lower(Employee.department) == "engineering")
    elif "sales" in q_lower:
        db_query = db_query.filter(func.lower(Employee.department) == "sales")
    elif "product" in q_lower:
        db_query = db_query.filter(func.lower(Employee.department) == "product")
        
    is_count = "how many" in q_lower or "count" in q_lower
    
    if is_count:
        count = db_query.count()
        return {"type": "count", "result": count, "message": f"Found {count} matching records."}
    else:
        results = db_query.all()
        data = [{"name": e.name, "dept": e.department, "role": e.role, "status": e.status, "account": e.account_type, "expires": e.license_expiration.isoformat() if e.license_expiration else None} for e in results]
        return {"type": "list", "result": data, "message": f"Found {len(results)} matching records."}

def process_query(db: Session, query: str) -> dict:
    """Routes and executes the query logic."""
    route = classify_query(query)
    logger.info(f"Routed query '{query}' to {route}")
    
    tools_used = []
    retrieved_docs = []
    db_result = None
    answer = ""
    
    try:
        if route == "RAG":
            retrieved_docs = retrieve_top_k(db, query, k=3)
            context = "\n---\n".join(retrieved_docs)
            prompt = f"Answer the user query based ONLY on the following context.\nContext:\n{context}\n\nQuery: {query}\nAnswer:"
            answer = llm_service.generate_completion(prompt)
            tools_used.append("Vector_Search")
            
        elif route == "DB":
            db_res = execute_db_query(db, query)
            db_result = db_res["result"]
            
            prompt = f"Answer the user query naturally based on this database result.\nDB Result:\n{json.dumps(db_res)}\n\nQuery: {query}\nAnswer:"
            answer = llm_service.generate_completion(prompt)
            tools_used.append("DB_Query")
            
        elif route == "TOOL":
            expr = extract_math_expression(query)
            if expr:
                calc_result = run_calculator(expr)
                tools_used.append("Calculator")
                answer = f"The result of {expr} is {calc_result}."
            else:
                prompt = f"Answer this computation or general request directly: {query}"
                answer = llm_service.generate_completion(prompt)
                tools_used.append("LLM_Direct")
                
        elif route == "MULTI":
            tools_used.append("DB_Query")
            db_res = execute_db_query(db, query)
            db_result = db_res["result"]
            
            tools_used.append("Vector_Search")
            retrieved_docs = retrieve_top_k(db, query, k=2)
            context = "\n---\n".join(retrieved_docs)
            
            prompt = f"Synthesize an answer using BOTH the database results and the documentation context.\nDB Result:\n{json.dumps(db_res)}\n\nContext:\n{context}\n\nQuery: {query}\nAnswer:"
            combined_answer = llm_service.generate_completion(prompt)
            
            answer = f"**Database Result:**\n{json.dumps(db_res['result'], indent=2)}\n\n**Documentation Answer:**\n{combined_answer}"
            
        else: # LLM (GENERAL)
            prompt = f"Answer the following general knowledge question directly:\n\n{query}\nAnswer:"
            answer = llm_service.generate_completion(prompt)
            tools_used.append("LLM_Direct")
            
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        answer = f"An error occurred while processing the request: {e}"
        
    return {
        "routing_decision": route,
        "tools_used": tools_used,
        "retrieved_docs": retrieved_docs,
        "db_result": db_result,
        "answer": answer
    }
