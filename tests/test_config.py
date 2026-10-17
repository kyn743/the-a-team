"""Configuration tests."""

from the_a_team.config import Settings
from the_a_team.schemas import AgentRole


def test_settings_load_prefixed_environment(monkeypatch) -> None:
    monkeypatch.setenv("ATEAM_MAX_RETRIES", "4")
    monkeypatch.setenv("ATEAM_ENGINEER_PROVIDER", "local-test-provider")

    settings = Settings(_env_file=None)

    assert settings.max_retries == 4
    assert settings.provider_name_for(AgentRole.ENGINEER) == "local-test-provider"


def test_settings_load_openai_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-key")
    monkeypatch.setenv("ATEAM_OPENAI_MODEL", "test-model")

    settings = Settings(_env_file=None)

    assert settings.openai_model == "test-model"
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "test-secret-key"
    assert "test-secret-key" not in repr(settings)
