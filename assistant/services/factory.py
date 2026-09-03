from functools import lru_cache

from django.conf import settings

from .base import BaseAIProvider
from .dummy import DummyProvider

# Later: from .gemini import GeminiProvider


@lru_cache(maxsize=1)
def get_ai_provider() -> BaseAIProvider:
    """
    Factory — single place to swap provider.
    Reads settings.AI_PROVIDER (from .env). UI never imports DummyProvider directly.
    Cached so we don't re-instantiate on every request.
    """
    provider = getattr(settings, "AI_PROVIDER", "dummy").lower()

    # if provider == "gemini":
    #     return GeminiProvider()
    # if provider == "openai":
    #     from .openai_provider import OpenAIProvider
    #     return OpenAIProvider()

    return DummyProvider()
