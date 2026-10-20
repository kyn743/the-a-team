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
does not make network requests or consume API credits.

## Run a configured workflow

The `the-a-team` command reads `.env` and `ATEAM_*` environment variables. By
default, providers are `unconfigured`, so the command reports a provider
failure without making a network request. To opt in to live OpenAI calls, set
all three role providers and provide a key in your local, git-ignored `.env`:

```env
ATEAM_ORCHESTRATOR_PROVIDER=openai
ATEAM_ENGINEER_PROVIDER=openai
ATEAM_REVIEWER_PROVIDER=openai
ATEAM_OPENAI_MODEL=gpt-6-astra
OPENAI_API_KEY=your-key-here
```

Then run a request from the project environment:

```bash
the-a-team "Draft a concise project plan for adding a health check endpoint"
```

The command prints the reviewed artifact on success. If the reviewer reaches
the configured retry limit, the command reports that human review is needed.
Running it with OpenAI configured makes external API calls and may incur
charges. The tests never make those calls.

## Scope

The core workflow intentionally excludes research, Notion, NotebookLM, Gemini,
file-editing tools, and persistence. Live model calls are opt-in through the
explicit command-line invocation and configured providers. No external tools
are included in v0.1.

