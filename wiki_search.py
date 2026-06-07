from wikipediaapi import Wikipedia, SearchWhat, ExtractFormat

wiki = Wikipedia(user_agent="DeepResearch (flypyfl@gmail.com)", language="en", extract_format=ExtractFormat.WIKI)

def search_the_wikipedia(query: str):
    result = wiki.search(query, limit=1, what=SearchWhat.TEXT)
    if result.pages:
        page_name = result.pages.keys()[0]
        return wiki.page(page_name).text
    else:
        return None
