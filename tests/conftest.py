"""Shared deterministic providers and payload factories."""

from collections import deque
from collections.abc import Iterable
from typing import Any

import pytest

from the_a_team.providers import ReasoningRequest, ReasoningResponse


class ScriptedProvider:
    """Return queued outputs without making network or model calls."""

    def __init__(self, *outputs: dict[str, Any] | Exception, name: str = "scripted") -> None:
        self._name = name
        self._outputs = deque(outputs)
        self.requests: list[ReasoningRequest] = []

    @property
    def name(self) -> str:
        return self._name

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        self.requests.append(request)
        if not self._outputs:
            raise AssertionError(f"Provider '{self.name}' has no scripted output left.")
        output = self._outputs.popleft()
        if isinstance(output, Exception):
            raise output
        return ReasoningResponse(structured_output=output)


@pytest.fixture
def plan_payload() -> dict[str, Any]:
    return {
        "task_type": "software_engineering",
        "execution_mode": "execute",
        "requirements": ["Return a tested implementation"],
        "constraints": ["Do not call external services"],
        "steps": [
            {
                "id": "implement",
                "description": "Build the requested artifact",
                "assigned_agent": "engineer",
            }
        ],
    }


def artifact_payload(version: int) -> dict[str, Any]:
    return {
        "title": f"Implementation v{version}",
        "summary": f"Artifact revision {version}",
        "content": f"result-{version}",
        "metadata": {"version": version},
    }


def review_payload(
    *,
    passed: bool,
    instructions: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.5,
        "satisfied_requirements": ["Return a tested implementation"] if passed else [],
        "missing_requirements": [] if passed else ["Return a tested implementation"],
        "issues": [] if passed else ["Coverage is incomplete"],
        "revision_instructions": list(instructions),
        "severity": "none" if passed else "major",
    }
