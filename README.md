# The A Team

The A Team is a provider-agnostic orchestration project built with Python and
LangGraph. The core workflow proves orchestration, review routing, and retry
handling while allowing model providers to be added behind a shared contract.

```text
User request -> Orchestrator -> Engineer -> Reviewer
                                  ^             |
                                  |--- REVISE --|
                                                |
                                             PASS -> End
```

The architecture keeps five responsibilities separate:

- Agents reason about work.
- Providers supply model intelligence to agents.
- Tools perform external actions. No tools are included in v0.1.
- Structured state carries workflow data between nodes.
- The graph owns routing, review loops, and retry limits.

Human approval is a deliberate future boundary. The v0.1 graph records whether
approval is required but does not implement an approval node.

## Development setup

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
pytest
```

No API key is needed for the v0.1 test suite. Tests inject deterministic
providers instead of calling external models.

## Package layout

```text
src/the_a_team/
  agents/       Agent nodes and role-specific validation
  providers/    Provider-neutral request/response contracts
  config.py     Environment-backed settings
  graph.py      LangGraph construction and routing
  schemas.py    Pydantic workflow contracts
  state.py      Shared graph state and initialization
```

## OpenAI provider

The optional `OpenAIProvider` uses the Responses API and Pydantic structured
outputs. Each agent still depends on the neutral `ReasoningProvider` contract,
so the graph and agent logic do not depend directly on OpenAI.

The provider is covered with fake-client unit tests. Running the test suite
does not make network requests or consume API credits. Runtime configuration
and a live workflow entry point will be added separately.

## Scope

The core workflow intentionally excludes research, Notion, NotebookLM, Gemini,
file-editing tools, persistence, and automatic live-model execution. Those capabilities can be
added behind tool and provider interfaces after the orchestration loop is
proven.

