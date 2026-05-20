# LearnAgent Codex Rebuild

LearnAgent is an experimental learning-agent project for helping self-learners move through a loop of discovering a topic, understanding core concepts, reading sources or repositories, practicing, and reviewing progress.

This branch starts with a Python CLI-first architecture. The first stage focuses on project structure, configuration, LLM abstraction, tool registration, router, workflow, local memory/session storage, and tests.

## Stage 1 Direction

- CLI first, no FastAPI or frontend yet.
- DeepSeek is the primary real LLM provider through an OpenAI-compatible API.
- Unit tests use mock clients and mock tools by default.
- Real LLM checks are isolated behind smoke scripts and environment variables.
- Web search and GitHub analysis are mocked in stage 1, with replaceable tool interfaces.
- Local session, run trace, and memory data live under `storage/` and are ignored by Git.

## Configuration

Create a local `.env` from `.env.example` when running real smoke tests. Do not commit `.env`.

```env
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=
DEEPSEEK_SMALL_MODEL=
DEEPSEEK_LARGE_MODEL=
LEARNAGENT_MODEL_MODE=normal
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048
RUN_REAL_TESTS=0
```

The actual DeepSeek model IDs must come from the provider configuration. They should not be hardcoded in workflow, agent loop, or tool code.

## Planned Commands

These commands will become available as implementation lands:

```powershell
python -m app.main
python -m pytest
python scripts/smoke_llm_real.py
```

Real integration tests and smoke scripts should only call external services when `RUN_REAL_TESTS=1` and the required API key is present.
