"""AI provider abstraction — optional cloud/local LLMs (v1.1 prep, no API calls yet)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class AIProviderKind(str, Enum):
    heuristic = "heuristic"
    openai = "openai"
    claude = "claude"
    gemini = "gemini"
    ollama = "ollama"
    lm_studio = "lm_studio"


@dataclass
class AIProviderConfig:
    kind: AIProviderKind = AIProviderKind.heuristic
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


@dataclass
class SQLGenerationResult:
    sql: str
    explanation: str
    provider: str


class AIProvider(ABC):
    kind: AIProviderKind

    @abstractmethod
    async def generate_sql(
        self,
        question: str,
        columns: list[dict[str, Any]],
        dataset_name: str,
    ) -> SQLGenerationResult:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


class UnconfiguredCloudProvider(AIProvider):
    """Placeholder for future OpenAI/Claude/Gemini integrations."""

    def __init__(self, kind: AIProviderKind):
        self.kind = kind

    def is_available(self) -> bool:
        return False

    async def generate_sql(
        self,
        question: str,
        columns: list[dict[str, Any]],
        dataset_name: str,
    ) -> SQLGenerationResult:
        raise NotImplementedError(
            f"{self.kind.value} provider is not configured. Use heuristic provider or set API credentials."
        )


def get_provider(config: AIProviderConfig | None = None) -> AIProvider:
    from app.ai_providers.heuristic import HeuristicAIProvider

    cfg = config or AIProviderConfig()
    if cfg.kind == AIProviderKind.heuristic:
        return HeuristicAIProvider()
    return UnconfiguredCloudProvider(cfg.kind)
