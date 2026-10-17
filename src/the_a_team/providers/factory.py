"""Construct reasoning providers from application settings."""

from the_a_team.config import Settings
from the_a_team.providers.base import (
    ProviderError,
    ReasoningProvider,
    UnconfiguredProvider,
)
from the_a_team.providers.openai import OpenAIProvider
from the_a_team.schemas import AgentRole


def build_provider(
    name: str,
    *,
    settings: Settings | None = None,
) -> ReasoningProvider:
    """Create the requested provider using application settings."""

    settings = settings or Settings()
    provider_name = name.strip().lower()

    if provider_name == "unconfigured":
        return UnconfiguredProvider()

    if provider_name == "openai":
        api_key = (
            settings.openai_api_key.get_secret_value()
            if settings.openai_api_key is not None
            else None
        )
        return OpenAIProvider(
            model=settings.openai_model,
            api_key=api_key,
        )

    raise ProviderError(f"Unknown reasoning provider '{name}'.")


def build_providers(
    *,
    settings: Settings | None = None,
) -> dict[AgentRole, ReasoningProvider]:
    """Build one configured provider for each agent role."""

    settings = settings or Settings()
    return {
        role: build_provider(settings.provider_name_for(role), settings=settings)
        for role in AgentRole
    }
