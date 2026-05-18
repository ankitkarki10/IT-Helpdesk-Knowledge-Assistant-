import json
from dotenv import load_dotenv
load_dotenv()
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_queries():
    queries = [
        {"desc": "1. RAG (Documentation/Process)", "q": "How do I connect to the company VPN?"},
        {"desc": "2. DB (Structured Data)", "q": "How many active employees do we have?"},
        {"desc": "3. Computation (Tool)", "q": "What is 1500 * 4.5?"},
        {"desc": "4. Multi-source (Agent)", "q": "Who are the engineering employees and what is the onboarding process for them?"},
        {"desc": "5. General Knowledge (LLM)", "q": "What is the capital of France?"}
    ]
    
    print("--- STARTING API TESTS ---")
    for item in queries:
        print(f"\n[TEST] {item['desc']}")
        print(f"Query: {item['q']}")
        response = client.post("/api/v1/query", json={"query": item['q']})
        
        if response.status_code == 200:
            data = response.json()
            print(f"-> Route taken: {data.get('routing_decision')}")
            print(f"-> Tools used: {data.get('tools_used')}")
            print(f"-> Answer:\n{data.get('answer')}")
        else:
            print(f"-> FAILED ({response.status_code})")
            print(response.text)

if __name__ == "__main__":
    test_queries()
