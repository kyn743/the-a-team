"""Tests for runtime wiring from settings through the configured workflow."""

from conftest import ScriptedProvider, artifact_payload, review_payload

from the_a_team.config import Settings
from the_a_team.runtime import run_configured_workflow
from the_a_team.schemas import AgentRole, WorkflowStatus


def test_run_configured_workflow_uses_role_providers_and_retry_setting(
    monkeypatch,
    plan_payload,
) -> None:
    orchestrator = ScriptedProvider(plan_payload, name="orchestrator-test")
    engineer = ScriptedProvider(artifact_payload(1), name="engineer-test")
    reviewer = ScriptedProvider(review_payload(passed=True), name="reviewer-test")
    providers = {
        AgentRole.ORCHESTRATOR: orchestrator,
        AgentRole.ENGINEER: engineer,
        AgentRole.REVIEWER: reviewer,
    }
    monkeypatch.setattr(
        "the_a_team.runtime.build_providers",
        lambda *, settings: providers,
    )
    settings = Settings(_env_file=None, max_retries=1)

    result = run_configured_workflow("Create a small tested feature", settings=settings)

    assert result["status"] == WorkflowStatus.COMPLETED
    assert result["max_retries"] == 1
    assert [request.role for request in orchestrator.requests] == [AgentRole.ORCHESTRATOR]
    assert [request.role for request in engineer.requests] == [AgentRole.ENGINEER]
    assert [request.role for request in reviewer.requests] == [AgentRole.REVIEWER]
