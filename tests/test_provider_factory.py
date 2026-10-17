"""Unit tests for provider construction from application settings."""

import pytest

from the_a_team.config import Settings
from the_a_team.providers import ProviderError, UnconfiguredProvider
from the_a_team.providers.factory import build_provider, build_providers
from the_a_team.schemas import AgentRole


def test_build_provider_returns_unconfigured_placeholder() -> None:
    settings = Settings(_env_file=None)

    provider = build_provider("unconfigured", settings=settings)

    assert isinstance(provider, UnconfiguredProvider)
    assert provider.name == "unconfigured"


def test_build_provider_creates_openai_with_configured_credentials(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    class FakeOpenAIProvider:
        def __init__(self, *, model: str, api_key: str | None = None) -> None:
            captured["model"] = model
            captured["api_key"] = api_key

    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-key")
    monkeypatch.setenv("ATEAM_OPENAI_MODEL", "test-model")
    monkeypatch.setattr(
        "the_a_team.providers.factory.OpenAIProvider",
        FakeOpenAIProvider,
    )

    provider = build_provider("openai", settings=Settings(_env_file=None))

    assert isinstance(provider, FakeOpenAIProvider)
    assert captured == {
        "model": "test-model",
        "api_key": "test-secret-key",
    }


def test_build_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderError, match="Unknown reasoning provider"):
        build_provider("unknown", settings=Settings(_env_file=None))


def test_build_providers_selects_provider_for_each_role(monkeypatch) -> None:
    class FakeOpenAIProvider:
        name = "openai"

        def __init__(self, *, model: str, api_key: str | None = None) -> None:
            self.model = model
            self.api_key = api_key

    monkeypatch.setenv("ATEAM_ORCHESTRATOR_PROVIDER", "openai")
    monkeypatch.setenv("ATEAM_ENGINEER_PROVIDER", "unconfigured")
    monkeypatch.setenv("ATEAM_REVIEWER_PROVIDER", "openai")
    monkeypatch.setattr(
        "the_a_team.providers.factory.OpenAIProvider",
        FakeOpenAIProvider,
    )

    providers = build_providers(settings=Settings(_env_file=None))

    assert providers[AgentRole.ORCHESTRATOR].name == "openai"
    assert providers[AgentRole.ENGINEER].name == "unconfigured"
    assert providers[AgentRole.REVIEWER].name == "openai"
