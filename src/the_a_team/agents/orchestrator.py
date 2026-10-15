"""Orchestrator node: classify, plan, and delegate."""

from dataclasses import dataclass
from typing import Any

from the_a_team.agents.common import failure_update, log_agent_start
from the_a_team.providers import ReasoningProvider, ReasoningRequest
from the_a_team.schemas import AgentRole, OrchestrationPlan, WorkflowStatus
from the_a_team.state import ATeamState


@dataclass(frozen=True, slots=True)
class OrchestratorAgent:
    """Create structured execution plans without doing engineering work."""

    provider: ReasoningProvider

    def __call__(self, state: ATeamState) -> dict[str, Any]:
        role = AgentRole.ORCHESTRATOR
        log_agent_start(state, role, self.provider.name)
        try:
            response = self.provider.generate(
                ReasoningRequest(
                    role=role,
                    objective=(
                        "Classify the request and produce an execution plan for the "
                        "engineering agent."
                    ),
                    context={"user_request": state["user_request"]},
                )
            )
            plan = OrchestrationPlan.model_validate(response.structured_output)
            return {
                "task_type": plan.task_type,
                "execution_mode": plan.execution_mode,
                "requirements": plan.requirements,
                "constraints": plan.constraints,
                "execution_plan": plan.steps,
                "current_agent": role,
                "current_step": "plan_complete",
                "status": WorkflowStatus.RUNNING,
            }
        except Exception as error:
            return failure_update(state, role, error)
