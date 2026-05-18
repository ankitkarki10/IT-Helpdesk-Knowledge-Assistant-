TEST_QUERIES = [
    # General knowledge
    "What is the capital of France?",
    "REST vs GraphQL",
    
    # RAG / Docs
    "What is the company policy on remote work?",
    "How do I reset my IT portal password?",
    "VPN reset process",
    "deploy backend service",
    
    # Database / Structured Data
    "How many active users?",
    "List paid accounts expiring this month",
    "Show inactive employees",
    "How many HR employees exist?",
    "Which employees are in the Engineering department?",
    "What is the role of Jane Doe?",
    
    # Tool / Computation
    "Calculate 15 * 45",
    "What is 250 / 5?",
    "83 users * $12",
    
    # Multi / Complex
    "How many active users and what is onboarding process?",
    "List employees and explain VPN reset process",
    "How many engineers are active and how do I deploy backend service?",
    
    # Edge Cases
    "Tell me a joke.",
    "Calculate 10 + 20 - 5 * 2"
]

SAMPLE_DOCS = [
    {
        "text": "The company policy states that remote work is allowed up to 3 days a week. All employees must be online between 10 AM and 3 PM EST.",
        "metadata": {"source": "HR_Handbook"}
    },
    {
        "text": "To reset your IT portal password, please navigate to myportal.company.com and click 'Forgot Password'. You will receive an SMS with an OTP.",
        "metadata": {"source": "IT_Wiki"}
    },
    {
        "text": "VPN reset process: First log out of the VPN client. Then visit the IT self-service portal, navigate to Network Access -> Reset VPN, and authenticate using Okta. Wait 5 minutes before reconnecting.",
        "metadata": {"source": "IT_Wiki"}
    },
    {
        "text": "To deploy backend service: Push your code to the 'main' branch. GitHub Actions will automatically run the CI pipeline, build the Docker image, and deploy it to the staging Kubernetes cluster. Wait for approval before promoting to production.",
        "metadata": {"source": "Engineering_Docs"}
    },
    {
        "text": "Employee Onboarding Process: New hires must complete the IT security training within the first week. Then they will receive their laptop and initial software licenses.",
        "metadata": {"source": "HR_Handbook"}
    }
]

from datetime import datetime, timedelta
now = datetime.utcnow()

SAMPLE_EMPLOYEES = [
    {"name": "John Smith", "department": "Engineering", "role": "Backend Developer", "status": "active", "account_type": "paid", "license_expiration": now + timedelta(days=15)},
    {"name": "Jane Doe", "department": "Product", "role": "Product Manager", "status": "active", "account_type": "free", "license_expiration": None},
    {"name": "Alice Johnson", "department": "Engineering", "role": "Frontend Developer", "status": "inactive", "account_type": "paid", "license_expiration": now - timedelta(days=10)},
    {"name": "Bob Williams", "department": "HR", "role": "Recruiter", "status": "active", "account_type": "free", "license_expiration": None},
    {"name": "Charlie Brown", "department": "Sales", "role": "Account Executive", "status": "active", "account_type": "paid", "license_expiration": now + timedelta(days=5)}
]
