from functools import lru_cache

from openai import OpenAI
from pydantic import BaseModel

from src.config import LLM_API_KEY, LLM_BASE_URL


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, max_retries=8, timeout=120)


class Usage(BaseModel):
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0

    def add(self, response) -> None:
        self.llm_calls += 1
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        self.prompt_tokens += usage.prompt_tokens or 0
        self.completion_tokens += usage.completion_tokens or 0
        details = getattr(usage, "prompt_tokens_details", None)
        self.cached_tokens += getattr(details, "cached_tokens", 0) or 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens