"""Command-line entry point for configured A Team workflows."""

import argparse
import sys
from collections.abc import Sequence

from the_a_team.config import Settings
from the_a_team.logging_config import configure_logging
from the_a_team.providers import ProviderError
from the_a_team.runtime import run_configured_workflow
from the_a_team.schemas import WorkflowStatus
from the_a_team.state import ATeamState


def _report_result(state: ATeamState) -> int:
    status = state["status"]
    artifact = state.get("final_output")

    if status == WorkflowStatus.COMPLETED and artifact is not None:
        print(f"# {artifact.title}\n\n{artifact.summary}\n\n{artifact.content}")
        return 0

    if status == WorkflowStatus.HUMAN_INTERVENTION_REQUIRED:
        print("The workflow stopped and needs human review.", file=sys.stderr)
        review = state.get("review")
        if review is not None:
            for issue in review.issues:
                print(f"- {issue}", file=sys.stderr)
            for instruction in review.revision_instructions:
                print(f"- Suggested revision: {instruction}", file=sys.stderr)
        return 2

    errors = state.get("errors", [])
    if errors:
        for error in errors:
            print(f"{error.node.value}: {error.message}", file=sys.stderr)
    else:
        print(f"Workflow ended with status '{status.value}'.", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run one workflow request from the command line."""

    parser = argparse.ArgumentParser(
        prog="the-a-team",
        description="Run a request through the configured orchestrator, engineer, and reviewer.",
    )
    parser.add_argument("request", nargs="+", help="the work request to run")
    args = parser.parse_args(argv)

    settings = Settings()
    configure_logging(settings.log_level)
    try:
        state = run_configured_workflow(" ".join(args.request), settings=settings)
    except ProviderError as error:
        print(f"Provider configuration error: {error}", file=sys.stderr)
        return 2
    return _report_result(state)
