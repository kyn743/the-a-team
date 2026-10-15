"""Structured contracts shared across agents, providers, and graph state."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base contract that rejects unexpected provider output fields."""

    model_config = ConfigDict(extra="forbid")


class AgentRole(StrEnum):
    ORCHESTRATOR = "orchestrator"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"


class TaskType(StrEnum):
    SOFTWARE_ENGINEERING = "software_engineering"
    ACADEMIC = "academic"
    RESEARCH = "research"
    STUDY = "study"
    PLANNING = "planning"
    GENERAL = "general"


class ExecutionMode(StrEnum):
    ASSIST = "assist"
    COLLABORATE = "collaborate"
    EXECUTE = "execute"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    REVISION_REQUIRED = "revision_required"
    COMPLETED = "completed"
    HUMAN_INTERVENTION_REQUIRED = "human_intervention_required"
    FAILED = "failed"


class ReviewSeverity(StrEnum):
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class ExecutionStep(StrictModel):
    """One planned unit of work."""

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    assigned_agent: AgentRole


class OrchestrationPlan(StrictModel):
    """Structured output expected from the orchestrator."""

    task_type: TaskType
    execution_mode: ExecutionMode
    requirements: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    steps: list[ExecutionStep] = Field(min_length=1)


class Artifact(StrictModel):
    """Provider-neutral work product created by an agent."""

    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewResult(StrictModel):
    """Machine-actionable reviewer decision."""

    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    satisfied_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)
    severity: ReviewSeverity


class AgentError(StrictModel):
    """An agent or provider failure preserved in workflow state."""

    node: AgentRole
    error_type: str
    message: str
    recoverable: bool = False
    attempts: int = Field(default=1, ge=1)


class WorkflowInput(StrictModel):
    """Validated input used to initialize the graph state."""

    user_request: str = Field(min_length=1)
    max_retries: int = Field(default=2, ge=0, le=20)
