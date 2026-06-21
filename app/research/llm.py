from dotenv import load_dotenv
from os import getenv
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
import openai
import app.config as config

HACK_AI_API_KEY = getenv("HACK_AI_API_KEY")

llm_hack_club_base = ChatOpenAI(
    model=config.hack_club_ai_model_base,
    api_key=HACK_AI_API_KEY,
    base_url="https://ai.hackclub.com/proxy/v1",
    max_retries=3
)

llm_hack_club_smart = ChatOpenAI(
    model=config.hack_club_ai_model_smart,
    api_key=HACK_AI_API_KEY,
    base_url="https://ai.hackclub.com/proxy/v1",
    max_retries=3,
    max_completion_tokens=20000
)

llm_open_ai = init_chat_model(config.openai_ai_model, max_retries=10)

def get_structured_output(query: str, structure, rate_limit_exceeded, smart_model: bool = False):
    if not rate_limit_exceeded:
        try:
            llm = llm_hack_club_smart if smart_model else llm_hack_club_base
            response = llm.with_structured_output(structure).invoke(query)
        except Exception as e:
            print(f"Hack Club AI failed, falling back to OpenAI: {type(e).__name__}: {e}")
            response = llm_open_ai.with_structured_output(structure).invoke(query)
            rate_limit_exceeded = True
    else:
        response = llm_open_ai.with_structured_output(structure).invoke(query)
    
    return [response, rate_limit_exceeded]
