"""Unit tests for the OpenAI reasoning provider."""

import json
from types import SimpleNamespace
from typing import Any

import pytest

from the_a_team.providers import ProviderError, ReasoningRequest
from the_a_team.providers.openai import OpenAIProvider
from the_a_team.schemas import AgentRole, Artifact, OrchestrationPlan


class FakeResponses:
    """Record API inputs and return a prepared structured result."""

    def __init__(self, output: OrchestrationPlan) -> None:
        self.output = output
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_parsed=self.output,
            output_text="structured response",
        )


class FakeClient:
    """Small substitute for the OpenAI client used by this unit test."""

    def __init__(self, responses: Any) -> None:
        self.responses = responses


def test_generate_maps_orchestrator_request_to_structured_output() -> None:
    plan = OrchestrationPlan.model_validate(
        {
            "task_type": "software_engineering",
            "execution_mode": "execute",
            "requirements": ["Return tested code"],
            "constraints": [],
            "steps": [
                {
                    "id": "implement",
                    "description": "Build the feature",
                    "assigned_agent": "engineer",
                }
            ],
        }
    )
    responses = FakeResponses(plan)
    provider = OpenAIProvider(
        model="test-model",
        client=FakeClient(responses),
    )

    result = provider.generate(
        ReasoningRequest(
            role=AgentRole.ORCHESTRATOR,
            objective="Plan the requested work.",
            context={"user_request": "Build a tested feature"},
        )
    )

    assert provider.name == "openai"
    assert result.content == "structured response"
    assert result.structured_output == plan.model_dump(mode="json")

    api_call = responses.calls[0]
    assert api_call["model"] == "test-model"
    assert api_call["text_format"] is OrchestrationPlan

    user_input = json.loads(api_call["input"][1]["content"])
    assert user_input["objective"] == "Plan the requested work."
    assert user_input["context"]["user_request"] == "Build a tested feature"


class RaisingResponses:
    """Simulate an SDK or network failure."""

    def parse(self, **_kwargs: Any) -> None:
        raise RuntimeError("network unavailable")


def test_generate_wraps_openai_client_errors() -> None:
    provider = OpenAIProvider(
        model="test-model",
        client=FakeClient(RaisingResponses()),
    )
    request = ReasoningRequest(
        role=AgentRole.ORCHESTRATOR,
        objective="Plan the requested work.",
        context={"user_request": "Build a tested feature"},
    )

    with pytest.raises(ProviderError, match="OpenAI request failed") as error_info:
        provider.generate(request)

    assert isinstance(error_info.value.__cause__, RuntimeError)


class EmptyResponses:
    """Simulate a completed response without structured output."""

    def parse(self, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            output_parsed=None,
            output_text="",
        )


def test_generate_rejects_missing_structured_output() -> None:
    provider = OpenAIProvider(
        model="test-model",
        client=FakeClient(EmptyResponses()),
    )
    request = ReasoningRequest(
        role=AgentRole.REVIEWER,
        objective="Review the artifact.",
        context={"artifact": {"content": "example"}},
    )

    with pytest.raises(ProviderError, match="returned no structured output"):
        provider.generate(request)


class SchemaDrivenResponses:
    """Build a fake response from the schema requested by the provider."""

    def __init__(self) -> None:
        self.output_model: Any = None

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.output_model = kwargs["text_format"]
        output = self.output_model(
            title="Implementation",
            summary="Completed artifact",
            content="Tested result",
        )
        return SimpleNamespace(
            output_parsed=output,
            output_text="structured response",
        )


def test_engineer_uses_strict_output_compatible_with_artifact() -> None:
    responses = SchemaDrivenResponses()
    provider = OpenAIProvider(
        model="test-model",
        client=FakeClient(responses),
    )

    result = provider.generate(
        ReasoningRequest(
            role=AgentRole.ENGINEER,
            objective="Build the requested artifact.",
            context={"requirements": ["Return tested code"]},
        )
    )

    artifact = Artifact.model_validate(result.structured_output)
    assert artifact.metadata == {}

    schema = responses.output_model.model_json_schema()
    assert schema["additionalProperties"] is False
    assert "metadata" not in schema["properties"]


def test_constructor_passes_api_key_to_openai_client(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    class FakeOpenAI:
        def __init__(self, *, api_key: str | None = None) -> None:
            captured["api_key"] = api_key

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    provider = OpenAIProvider(
        model="test-model",
        api_key="test-secret-key",
    )

    assert provider.name == "openai"
    assert captured["api_key"] == "test-secret-key"
