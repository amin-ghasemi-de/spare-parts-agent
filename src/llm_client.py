from functools import lru_cache

from openai import OpenAI

from src.config import LLM_API_KEY, LLM_BASE_URL


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)