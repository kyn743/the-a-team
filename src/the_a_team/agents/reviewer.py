"""Reviewer node: independently grade artifacts and control revisions."""

from dataclasses import dataclass
from typing import Any

from the_a_team.agents.common import failure_update, log_agent_start
from the_a_team.providers import ReasoningProvider, ReasoningRequest
from the_a_team.schemas import AgentRole, ReviewResult, WorkflowStatus
from the_a_team.state import ATeamState


@dataclass(frozen=True, slots=True)
class ReviewerAgent:
    """Return a structured PASS/REVISE decision without rewriting the artifact."""

    provider: ReasoningProvider

    def __call__(self, state: ATeamState) -> dict[str, Any]:
        role = AgentRole.REVIEWER
        log_agent_start(state, role, self.provider.name)
        try:
            artifact = state["artifact"]
            if artifact is None:
                raise ValueError("Reviewer cannot run without an artifact.")

            response = self.provider.generate(
                ReasoningRequest(
                    role=role,
                    objective="Evaluate the artifact against every requirement and return PASS or REVISE.",
                    context={
                        "user_request": state["user_request"],
                        "requirements": state["requirements"],
                        "constraints": state.get("constraints", []),
                        "artifact": artifact.model_dump(mode="json"),
                    },
                )
            )
            review = ReviewResult.model_validate(response.structured_output)

            if review.passed:
                return {
                    "review": review,
                    "final_output": artifact,
                    "current_agent": role,
                    "current_step": "review_passed",
                    "status": WorkflowStatus.COMPLETED,
                }

            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 0)
            if retry_count >= max_retries:
                return {
                    "review": review,
                    "current_agent": role,
                    "current_step": "retry_limit_reached",
                    "requires_human_approval": True,
                    "status": WorkflowStatus.HUMAN_INTERVENTION_REQUIRED,
                }

            return {
                "review": review,
                "retry_count": retry_count + 1,
                "current_agent": role,
                "current_step": "revision_requested",
                "status": WorkflowStatus.REVISION_REQUIRED,
            }
        except Exception as error:
            return failure_update(state, role, error)

