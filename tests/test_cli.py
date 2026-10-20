"""Tests for the command-line workflow entry point."""

from the_a_team import cli
from the_a_team.config import Settings
from the_a_team.schemas import Artifact, ReviewResult, ReviewSeverity, WorkflowStatus
from the_a_team.state import ATeamState


def test_cli_prints_completed_artifact(monkeypatch, capsys) -> None:
    settings = Settings(_env_file=None)
    state: ATeamState = {
        "status": WorkflowStatus.COMPLETED,
        "final_output": Artifact(
            title="A concise plan",
            summary="A three-step plan.",
            content="1. Plan\n2. Build\n3. Verify",
        ),
        "errors": [],
    }
    captured: dict[str, object] = {}

    monkeypatch.setattr(cli, "Settings", lambda: settings)
    monkeypatch.setattr(
        cli,
        "run_configured_workflow",
        lambda request, *, settings: (
            captured.update(
                request=request,
                settings=settings,
            )
            or state
        ),
    )

    exit_code = cli.main(["Create", "a", "plan"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert captured["request"] == "Create a plan"
    assert captured["settings"] is settings
    assert "# A concise plan" in output
    assert "1. Plan\n2. Build\n3. Verify" in output


def test_cli_reports_provider_configuration_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(
        cli,
        "run_configured_workflow",
        lambda request, *, settings: (_ for _ in ()).throw(
            cli.ProviderError("Unknown reasoning provider 'typo'.")
        ),
    )

    exit_code = cli.main(["Create", "a", "plan"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Provider configuration error" in captured.err
    assert "Unknown reasoning provider 'typo'." in captured.err


def test_cli_reports_unconfigured_provider_without_network_call(monkeypatch, capsys) -> None:
    settings = Settings(_env_file=None)
    monkeypatch.setattr(cli, "Settings", lambda: settings)

    exit_code = cli.main(["Run", "a", "request"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "orchestrator: No implementation is configured" in captured.err


def test_cli_reports_human_intervention_details(capsys) -> None:
    state: ATeamState = {
        "status": WorkflowStatus.HUMAN_INTERVENTION_REQUIRED,
        "review": ReviewResult(
            passed=False,
            score=0.5,
            issues=["The artifact misses a requirement."],
            revision_instructions=["Add the missing requirement."],
            severity=ReviewSeverity.MAJOR,
        ),
    }

    exit_code = cli._report_result(state)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "needs human review" in captured.err
    assert "The artifact misses a requirement." in captured.err
    assert "Suggested revision: Add the missing requirement." in captured.err
