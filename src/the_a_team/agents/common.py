"""Shared agent-node behavior."""

import logging
from typing import Any

from the_a_team.schemas import AgentError, AgentRole, WorkflowStatus
from the_a_team.state import ATeamState

logger = logging.getLogger(__name__)


def failure_update(
    state: ATeamState,
    role: AgentRole,
    error: Exception,
) -> dict[str, Any]:
    """Convert a node-boundary exception into inspectable workflow state."""

    task_id = state.get("task_id", "unknown")
    logger.exception("agent_failed role=%s task_id=%s", role.value, task_id)
    return {
        "current_agent": role,
        "current_step": "failed",
        "status": WorkflowStatus.FAILED,
        "errors": [
            AgentError(
                node=role,
                error_type=type(error).__name__,
                message=str(error),
                recoverable=False,
                attempts=state.get("retry_count", 0) + 1,
            )
        ],
    }


def log_agent_start(state: ATeamState, role: AgentRole, provider_name: str) -> None:
    """Emit a compact node-start event."""

    logger.info(
        "agent_started role=%s provider=%s task_id=%s",
        role.value,
        provider_name,
        state.get("task_id", "unknown"),
    )

