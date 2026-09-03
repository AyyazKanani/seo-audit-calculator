from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Abstract provider. UI depends only on this interface.
    Swap Gemini/OpenAI/Ollama by returning a different subclass
    from factory.get_ai_provider() — no view/template changes.
    """

    @abstractmethod
    def get_response(self, prompt: str, history: list[dict] | None = None) -> str:
        """
        Return assistant reply for prompt.
        history is optional list of {"role": "user"|"assistant", "content": str}
        """
        raise NotImplementedError
