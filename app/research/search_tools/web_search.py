from dotenv import load_dotenv
from os import getenv
from exa_py import Exa
import re

load_dotenv()
EXA_API_KEY = getenv("EXA_API_KEY")

exa = Exa(api_key=EXA_API_KEY)

class WebSearchResult:
    def __init__(self, url: str, text: str):
        self.url = url
        self.text = text

def sanitize_search_query(query: str) -> str:
    query = re.sub(r'\bsite:\S+', '', query, flags=re.IGNORECASE)
    query = re.sub(r'\b(?:includeDomains|include_domains):\S+', '', query, flags=re.IGNORECASE)
    query = re.sub(r'https?://\S+', '', query)
    query = re.sub(r'\b(?:www\.)?(?:[a-z0-9-]{2,}\.)+[a-z]{2,}\b', '', query, flags=re.IGNORECASE)
    query = re.sub(r'\s+', ' ', query).strip()
    return query

def search_the_web(query: str) -> list[WebSearchResult]:
    safe_query = sanitize_search_query(query) or query

    try:
        search_result = exa.search(
            safe_query,
            type="neural",
            num_results=2,
            contents={"text": True}
        )
    except ValueError as error:
        print(f"Exa search failed for query {safe_query!r}: {error}")
        return []

    results = []

    for result in search_result.results:
        results.append(WebSearchResult(url=result.url, text=result.text))

    return results
