"""LangGraph assembly for The A Team v0.1 workflow."""

from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from the_a_team.agents import EngineerAgent, OrchestratorAgent, ReviewerAgent
from the_a_team.providers import ReasoningProvider
from the_a_team.schemas import WorkflowStatus
from the_a_team.state import ATeamState, create_initial_state


def _route_after_worker(state: ATeamState) -> str:
    if state["status"] == WorkflowStatus.FAILED:
        return "end"
    return "continue"


def _route_after_review(state: ATeamState) -> str:
    if state["status"] == WorkflowStatus.REVISION_REQUIRED:
        return "revise"
    return "end"


def build_graph(
    *,
    orchestrator_provider: ReasoningProvider,
    engineer_provider: ReasoningProvider,
    reviewer_provider: ReasoningProvider,
) -> CompiledStateGraph:
    """Build the provider-injected v0.1 orchestration graph."""

    builder = StateGraph(ATeamState)
    builder.add_node("orchestrator", OrchestratorAgent(orchestrator_provider))
    builder.add_node("engineer", EngineerAgent(engineer_provider))
    builder.add_node("reviewer", ReviewerAgent(reviewer_provider))

    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges(
        "orchestrator",
        _route_after_worker,
        {"continue": "engineer", "end": END},
    )
    builder.add_conditional_edges(
        "engineer",
        _route_after_worker,
        {"continue": "reviewer", "end": END},
    )
    builder.add_conditional_edges(
        "reviewer",
        _route_after_review,
        {"revise": "engineer", "end": END},
    )
    return builder.compile()


def run_workflow(
    graph: CompiledStateGraph,
    user_request: str,
    *,
    max_retries: int = 2,
    task_id: str | None = None,
) -> ATeamState:
    """Initialize and synchronously run a workflow to a terminal state."""

    initial_state = create_initial_state(
        user_request,
        max_retries=max_retries,
        task_id=task_id,
    )
    recursion_limit = max(25, (2 * max_retries) + 5)
    result = graph.invoke(initial_state, {"recursion_limit": recursion_limit})
    return cast(ATeamState, result)

