from dotenv import load_dotenv
from os import getenv
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
import openai

HACK_AI_API_KEY = getenv("HACK_AI_API_KEY")

llm_hack_club = ChatOpenAI(
    model="google/gemini-3.1-flash-lite",
    api_key=HACK_AI_API_KEY,
    base_url="https://ai.hackclub.com/proxy/v1"
)

llm_open_ai = init_chat_model("gpt-5-nano-2025-08-07")

def get_structured_output(query: str, structure, rate_limit_exceeded):
    if not rate_limit_exceeded:
        try:
            response = llm_hack_club.with_structured_output(structure).invoke(query)
        except openai.RateLimitError:
            print("Rate limit exceeded, falling back to the api usage")
            response = llm_open_ai.with_structured_output(structure).invoke(query)
            rate_limit_exceeded = True
    else:
        response = llm_open_ai.with_structured_output(structure).invoke(query)
    
    return [response, rate_limit_exceeded]
