"""Shared LangGraph state and initialization helpers."""

import operator
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from the_a_team.schemas import (
    AgentError,
    AgentRole,
    Artifact,
    ExecutionMode,
    ExecutionStep,
    ReviewResult,
    TaskType,
    WorkflowInput,
    WorkflowStatus,
)


class ATeamState(TypedDict, total=False):
    """The inspectable contract passed between graph nodes."""

    task_id: str
    user_request: str
    task_type: TaskType
    execution_mode: ExecutionMode
    requirements: list[str]
    constraints: list[str]
    execution_plan: list[ExecutionStep]
    current_agent: AgentRole | None
    current_step: str | None
    artifact: Artifact | None
    review: ReviewResult | None
    retry_count: int
    max_retries: int
    errors: Annotated[list[AgentError], operator.add]
    requires_human_approval: bool
    approval_status: str | None
    final_output: Artifact | None
    status: WorkflowStatus
    metadata: dict[str, Any]


def create_initial_state(
    user_request: str,
    *,
    max_retries: int = 2,
    task_id: str | None = None,
) -> ATeamState:
    """Validate user input and return a complete initial graph state."""

    workflow_input = WorkflowInput(user_request=user_request, max_retries=max_retries)
    return {
        "task_id": task_id or str(uuid4()),
        "user_request": workflow_input.user_request,
        "current_agent": None,
        "current_step": None,
        "artifact": None,
        "review": None,
        "retry_count": 0,
        "max_retries": workflow_input.max_retries,
        "errors": [],
        "requires_human_approval": False,
        "approval_status": None,
        "final_output": None,
        "status": WorkflowStatus.PENDING,
        "metadata": {},
    }

