import os
from duckduckgo_search import DDGS
import requests
import logging
from livekit.agents import function_tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

@function_tool
def search_tool(query: str) -> str:
    """
    Fallback search using DuckDuckGo (free, no API key needed).
    """
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3)
        if results:
            summary = "\n".join([f"{r['title']}: {r['body']}" for r in results])
            return f"Internet search results for '{query}':\n{summary}"
        else:
            return "No relevant results found online."
    except Exception as e:
        logging.error(f"Search tool error: {e}")
        return f"Search failed: {e}"

@function_tool
def search_internet(query: str) -> str:
    """
    Primary search using Google Custom Search API.
    Requires GOOGLE_SEARCH_API_KEY and SEARCH_ENGINE_ID in .env.
    """
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")
    
    if not api_key or not search_engine_id:
        logging.error("Google API key or search engine ID missing. Falling back to DuckDuckGo.")
        return search_tool(query)  # Fallback
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": 3,  # Limit to 3 results
    }

    logging.info(f"🔍 Searching Google for: {query}")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("items", [])
        if not results:
            logging.warning("No Google search results found. Falling back to DuckDuckGo.")
            return search_tool(query)

        # Extract and summarize top results
        summary = "\n".join([f"{item['title']}: {item.get('snippet', 'No description')}" for item in results[:3]])
        logging.info(f"✅ Google search successful for '{query}'")
        return f"Google search results for '{query}':\n{summary}"

    except requests.exceptions.RequestException as e:
        logging.error(f"Google search network error: {e}. Falling back to DuckDuckGo.")
        return search_tool(query)
    except Exception as e:
        logging.error(f"Google search unexpected error: {e}. Falling back to DuckDuckGo.")
        return search_tool(query)