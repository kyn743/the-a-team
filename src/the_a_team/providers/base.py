"""Vendor-neutral model provider contracts."""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from the_a_team.schemas import AgentRole


class ReasoningRequest(BaseModel):
    """A provider-neutral request produced by an agent."""

    model_config = ConfigDict(extra="forbid")

    role: AgentRole
    objective: str = Field(min_length=1)
    context: dict[str, Any]


class ReasoningResponse(BaseModel):
    """A provider response carrying structured data for agent validation."""

    model_config = ConfigDict(extra="forbid")

    content: str = ""
    structured_output: dict[str, Any]


class ProviderError(RuntimeError):
    """Raised when a reasoning provider cannot fulfill a request."""


@runtime_checkable
class ReasoningProvider(Protocol):
    """Contract implemented by any model or deterministic test provider."""

    @property
    def name(self) -> str:
        """Return a stable provider identifier for logs and configuration."""

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        """Generate a structured response for an agent."""


class UnconfiguredProvider:
    """Explicit placeholder used until a real provider is wired in."""

    def __init__(self, name: str = "unconfigured") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        raise ProviderError(
            f"No implementation is configured for provider '{self.name}' "
            f"used by the {request.role.value} agent."
        )
