from core.logger import get_logger
import os

logger = get_logger(__name__)

def run_file_search(query: str, directory: str = ".") -> str:
    """Mock implementation of a file search tool."""
    logger.info(f"Tool execution: search on '{query}'")
    try:
        results = []
        for root, dirs, files in os.walk(directory):
            if '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
        if not results:
            return "No matching files found."
        return f"Found {len(results)} files: " + ", ".join(results[:5])
    except Exception as e:
        logger.error(f"Search failed for {query}: {e}")
        return f"Error searching: {e}"
