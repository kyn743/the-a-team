"""Runtime wiring for configured workflow execution."""

from langgraph.graph.state import CompiledStateGraph

from the_a_team.config import Settings
from the_a_team.graph import build_graph, run_workflow
from the_a_team.providers import ReasoningProvider
from the_a_team.providers.factory import build_providers
from the_a_team.schemas import AgentRole
from the_a_team.state import ATeamState


def build_configured_graph(
    settings: Settings | None = None,
) -> CompiledStateGraph:
    """Build the workflow graph with providers selected by application settings."""

    configured_settings = settings if settings is not None else Settings()
    providers: dict[AgentRole, ReasoningProvider] = build_providers(settings=configured_settings)
    return build_graph(
        orchestrator_provider=providers[AgentRole.ORCHESTRATOR],
        engineer_provider=providers[AgentRole.ENGINEER],
        reviewer_provider=providers[AgentRole.REVIEWER],
    )


def run_configured_workflow(
    user_request: str,
    settings: Settings | None = None,
) -> ATeamState:
    """Run a workflow using providers and retry limits from application settings."""

    configured_settings = settings if settings is not None else Settings()
    graph = build_configured_graph(configured_settings)
    return run_workflow(
        graph,
        user_request,
        max_retries=configured_settings.max_retries,
    )
