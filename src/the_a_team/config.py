"""Environment-backed application configuration."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from the_a_team.schemas import AgentRole


class Settings(BaseSettings):
    """Runtime settings loaded from ``.env`` and ``ATEAM_*`` variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ATEAM_",
        extra="ignore",
        case_sensitive=False,
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    max_retries: int = Field(default=2, ge=0, le=20)
    orchestrator_provider: str = "unconfigured"
    engineer_provider: str = "unconfigured"
    reviewer_provider: str = "unconfigured"

    def provider_name_for(self, role: AgentRole) -> str:
        """Return the configured provider name for a reasoning role."""

        names = {
            AgentRole.ORCHESTRATOR: self.orchestrator_provider,
            AgentRole.ENGINEER: self.engineer_provider,
            AgentRole.REVIEWER: self.reviewer_provider,
        }
        return names[role]

