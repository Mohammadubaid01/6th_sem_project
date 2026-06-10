from tavily import TavilyClient
from src.config import TAVILY_API_KEY

# Initialising client safely
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


def search_web(query):
    # Safety fallback
    if not tavily:
        return ""

    try:
        response = tavily.search(query=query, max_results=3)

        results = []
        for r in response["results"]:
            results.append(r.get("content", ""))

        return "\n\n".join(results)

    except Exception as e:
        print("Web search error:", e)
        return ""