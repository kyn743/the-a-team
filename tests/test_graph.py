"""Unit tests for graph routing and terminal states."""

from typing import Any

from conftest import ScriptedProvider, artifact_payload, review_payload

from the_a_team.graph import build_graph, run_workflow
from the_a_team.schemas import AgentRole, WorkflowStatus


def make_graph(
    plan_payload: dict[str, Any],
    engineer: ScriptedProvider,
    reviewer: ScriptedProvider,
):
    orchestrator = ScriptedProvider(plan_payload, name="orchestrator-test")
    graph = build_graph(
        orchestrator_provider=orchestrator,
        engineer_provider=engineer,
        reviewer_provider=reviewer,
    )
    return graph, orchestrator


def test_happy_path_reaches_completed_state(plan_payload) -> None:
    engineer = ScriptedProvider(artifact_payload(1), name="engineer-test")
    reviewer = ScriptedProvider(review_payload(passed=True), name="reviewer-test")
    graph, orchestrator = make_graph(plan_payload, engineer, reviewer)

    result = run_workflow(graph, "Build a small tested feature", task_id="task-001")

    assert result["status"] == WorkflowStatus.COMPLETED
    assert result["final_output"] == result["artifact"]
    assert result["retry_count"] == 0
    assert result["errors"] == []
    assert [request.role for request in orchestrator.requests] == [AgentRole.ORCHESTRATOR]
    assert [request.role for request in engineer.requests] == [AgentRole.ENGINEER]
    assert [request.role for request in reviewer.requests] == [AgentRole.REVIEWER]


def test_failed_review_loops_to_engineer_then_passes(plan_payload) -> None:
    engineer = ScriptedProvider(
        artifact_payload(1),
        artifact_payload(2),
        name="engineer-test",
    )
    reviewer = ScriptedProvider(
        review_payload(passed=False, instructions=["Add the missing tests"]),
        review_payload(passed=True),
        name="reviewer-test",
    )
    graph, _ = make_graph(plan_payload, engineer, reviewer)

    result = run_workflow(graph, "Build and review a feature", max_retries=2)

    assert result["status"] == WorkflowStatus.COMPLETED
    assert result["retry_count"] == 1
    assert result["artifact"].metadata["version"] == 2
    assert len(engineer.requests) == 2
    assert engineer.requests[1].context["revision_instructions"] == ["Add the missing tests"]
    assert len(reviewer.requests) == 2


def test_retry_limit_stops_for_human_intervention(plan_payload) -> None:
    engineer = ScriptedProvider(
        artifact_payload(1),
        artifact_payload(2),
        name="engineer-test",
    )
    reviewer = ScriptedProvider(
        review_payload(passed=False, instructions=["First revision"]),
        review_payload(passed=False, instructions=["Still incomplete"]),
        name="reviewer-test",
    )
    graph, _ = make_graph(plan_payload, engineer, reviewer)

    result = run_workflow(graph, "Build a difficult feature", max_retries=1)

    assert result["status"] == WorkflowStatus.HUMAN_INTERVENTION_REQUIRED
    assert result["retry_count"] == 1
    assert result["requires_human_approval"] is True
    assert result["final_output"] is None
    assert len(engineer.requests) == 2
    assert len(reviewer.requests) == 2


def test_provider_failure_is_preserved_in_state(plan_payload) -> None:
    engineer = ScriptedProvider(RuntimeError("provider unavailable"), name="engineer-test")
    reviewer = ScriptedProvider(name="reviewer-test")
    graph, _ = make_graph(plan_payload, engineer, reviewer)

    result = run_workflow(graph, "Build a feature")

    assert result["status"] == WorkflowStatus.FAILED
    assert result["current_agent"] == AgentRole.ENGINEER
    assert len(result["errors"]) == 1
    assert result["errors"][0].error_type == "RuntimeError"
    assert result["errors"][0].message == "provider unavailable"
    assert reviewer.requests == []


def test_malformed_reviewer_output_fails_closed(plan_payload) -> None:
    engineer = ScriptedProvider(artifact_payload(1), name="engineer-test")
    reviewer = ScriptedProvider({"passed": True}, name="reviewer-test")
    graph, _ = make_graph(plan_payload, engineer, reviewer)

    result = run_workflow(graph, "Build a feature")

    assert result["status"] == WorkflowStatus.FAILED
    assert result["current_agent"] == AgentRole.REVIEWER
    assert result["final_output"] is None
    assert result["errors"][0].error_type == "ValidationError"
