"""Engineering node: produce or revise the requested artifact."""

from dataclasses import dataclass
from typing import Any

from the_a_team.agents.common import failure_update, log_agent_start
from the_a_team.providers import ReasoningProvider, ReasoningRequest
from the_a_team.schemas import AgentRole, Artifact, WorkflowStatus
from the_a_team.state import ATeamState


@dataclass(frozen=True, slots=True)
class EngineerAgent:
    """Create artifacts from plans and reviewer revision instructions."""

    provider: ReasoningProvider

    def __call__(self, state: ATeamState) -> dict[str, Any]:
        role = AgentRole.ENGINEER
        log_agent_start(state, role, self.provider.name)
        try:
            review = state.get("review")
            response = self.provider.generate(
                ReasoningRequest(
                    role=role,
                    objective="Create the requested artifact or revise it from reviewer feedback.",
                    context={
                        "user_request": state["user_request"],
                        "requirements": state["requirements"],
                        "constraints": state.get("constraints", []),
                        "execution_plan": [
                            step.model_dump(mode="json") for step in state.get("execution_plan", [])
                        ],
                        "previous_artifact": (
                            state["artifact"].model_dump(mode="json")
                            if state.get("artifact")
                            else None
                        ),
                        "revision_instructions": (
                            review.revision_instructions if review and not review.passed else []
                        ),
                        "retry_count": state.get("retry_count", 0),
                    },
                )
            )
            artifact = Artifact.model_validate(response.structured_output)
            return {
                "artifact": artifact,
                "current_agent": role,
                "current_step": "artifact_ready",
                "status": WorkflowStatus.RUNNING,
            }
        except Exception as error:
            return failure_update(state, role, error)
