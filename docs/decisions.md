# Architecture Decision Records

## Decision 001: Stage 1 Uses CLI First

Date: 2026-05-20

Status: Accepted

Context:

The first stage should validate LearnAgent's core runtime before adding HTTP APIs or frontend complexity.

Decision:

Build a Python CLI-first minimum viable version. FastAPI, Flask, and frontend work are deferred.

Rationale:

CLI keeps the initial loop small and makes Router, Tool Layer, LLM Client, Workflow, Memory, and tests easier to validate. Future API entrypoints should reuse the same core workflow.

Impact:

The CLI must stay thin. Core agent logic must live outside the CLI entrypoint so a later API can reuse it.

## Decision 002: DeepSeek Via OpenAI-Compatible API

Date: 2026-05-20

Status: Accepted

Context:

LearnAgent needs a real LLM provider early, while preserving the ability to switch providers later.

Decision:

Use DeepSeek as the primary stage 1 provider through an OpenAI-compatible API. Provide both `MockLLMClient` and `DeepSeekLLMClient`.

Rationale:

An OpenAI-compatible adapter keeps workflow code independent from provider details. Unit tests can use mock clients, while smoke scripts can validate real DeepSeek access.

Impact:

Business code must call LLMs only through the LLM client abstraction. It must not call HTTP APIs directly.

## Decision 003: Model IDs Are Configuration

Date: 2026-05-20

Status: Accepted

Context:

DeepSeek V4 Flash and DeepSeek V4 Pro model IDs must match the actual provider platform names.

Decision:

Keep model names in `.env` and the config module. `.env.example` exposes `DEEPSEEK_SMALL_MODEL` and `DEEPSEEK_LARGE_MODEL`.

Rationale:

Provider model IDs may vary. Hardcoding them in workflow, tools, or agent loop would make future changes risky.

Impact:

Workflow and tools must request model selection by task or mode, not by concrete model string.

## Decision 004: Simple ModelSelector In Stage 1

Date: 2026-05-20

Status: Accepted

Context:

LearnAgent needs small and large model routing without complex multi-model orchestration.

Decision:

Implement a simple rule-based ModelSelector. `normal`, `summary`, and `lightweight` use the small model. `deep`, `planning`, and `repo_analysis` use the large model.

Rationale:

This supports the confirmed DeepSeek strategy while keeping stage 1 implementation straightforward and testable.

Impact:

Workflow should depend on ModelSelector instead of embedding provider-specific model names.

## Decision 005: Mock Web Search And GitHub Analyzer In Stage 1

Date: 2026-05-20

Status: Accepted

Context:

Search and GitHub analysis are important, but real external integrations bring provider choice, credentials, rate limits, parsing quality, and token-budget concerns.

Decision:

Stage 1 defines replaceable tool interfaces and mock implementations. Real Web Search and GitHub API integration are deferred.

Rationale:

This validates architecture without committing to search APIs or GitHub credentials too early.

Impact:

Workflow must depend on Tool interfaces and ToolRegistry, not concrete mock classes. Real implementations can be added later after confirmation.

## Decision 006: Local Session And Memory Storage

Date: 2026-05-20

Status: Accepted

Context:

LearnAgent needs local debug traces and long-term learning memory, but should not introduce a database in stage 1.

Decision:

Use JSONL for sessions and workflow traces, and Markdown with frontmatter for long-term memory. Store local data under `storage/sessions/`, `storage/runs/`, and `storage/memory/`.

Rationale:

JSONL is append-friendly and good for debugging. Markdown memory is human-readable and easy to review.

Impact:

`storage/` is ignored by Git. User learning records, run traces, LLM responses, and local memory files must not be committed.

## Decision 007: Test Boundaries

Date: 2026-05-20

Status: Accepted

Context:

The project needs reliable tests while avoiding accidental API usage.

Decision:

Use pytest. Unit tests default to mock LLMs and mock tools. Real integration tests and smoke scripts run only when explicitly enabled with `RUN_REAL_TESTS=1` and required credentials.

Rationale:

This keeps normal test runs fast, deterministic, and free of API cost.

Impact:

Real LLM validation should be provided by `scripts/smoke_llm_real.py` once the LLM client is implemented.

## Decision 008: JSON Action Fallback For Tool Calling

Date: 2026-05-20

Status: Accepted

Context:

DeepSeek tool calling behavior may vary across model versions and API surfaces.

Decision:

Stage 1 may support JSON action output as a fallback to standard tool calling.

Rationale:

JSON action fallback lets the agent loop validate tool selection even if native tool calling is unstable.

Impact:

Tool call parsing differences should be isolated in the LLM client or agent-loop boundary, not spread through business workflow code.
