"""Shared state initialization tests."""

import pytest
from pydantic import ValidationError

from the_a_team.schemas import WorkflowStatus
from the_a_team.state import create_initial_state


def test_initial_state_is_complete_and_pending() -> None:
    state = create_initial_state("Plan a feature", max_retries=3, task_id="known-id")

    assert state["task_id"] == "known-id"
    assert state["status"] == WorkflowStatus.PENDING
    assert state["retry_count"] == 0
    assert state["max_retries"] == 3
    assert state["errors"] == []


def test_initial_state_rejects_empty_request() -> None:
    with pytest.raises(ValidationError):
        create_initial_state("")
