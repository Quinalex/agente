"""
LLM client factory - selects and manages LLM providers.
"""

import logging
from typing import Dict, List, Optional

from app.core.config import settings
from app.llm.provider import LLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client factory for provider selection."""

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = settings.DEFAULT_LLM_PROVIDER
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize available LLM providers."""
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
            )
            logger.info("OpenAI provider initialized")

        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL,
            )
            logger.info("Anthropic provider initialized")

        if not self.providers:
            logger.warning("No LLM providers configured")

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """Get LLM provider."""
        name = provider_name or self.default_provider

        if name not in self.providers:
            raise ValueError(
                f"Provider {name} not available. "
                f"Available: {list(self.providers.keys())}"
            )

        return self.providers[name]

    async def complete(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Get completion from LLM."""
        llm_provider = self.get_provider(provider)
        return await llm_provider.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """Stream completion from LLM."""
        llm_provider = self.get_provider(provider)
        async for chunk in llm_provider.stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    def list_providers(self) -> List[str]:
        """List available providers."""
        return list(self.providers.keys())


# Global LLM client instance
llm_client = LLMClient()
