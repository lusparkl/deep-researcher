from dotenv import load_dotenv
from os import getenv
from exa_py import Exa

load_dotenv()
EXA_API_KEY = getenv("EXA_API_KEY")

exa = Exa(api_key=EXA_API_KEY)

class WebSearchResult:
    def __init__(self, url: str, text: str):
        self.url = url
        self.text = text

    

def search_the_web(query: str) -> list[WebSearchResult]:
    search_result = exa.search(
        query,
        type="auto",
        num_results=2,
        contents={"text": True}
    )

    results = []

    for result in search_result.results:
        results.append(WebSearchResult(url=result.url, text=result.text))

    return results