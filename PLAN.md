# AI Agency MVP - Implementation Plan

## Overview

Build two initial tools for the agency's "Spec-to-Ship" pipeline:
1. **PRD Builder** - Transforms raw customer requirements into structured, AI-optimized PRDs
2. **UI Design Generator** - Extracts design sections from PRDs and generates Google Stitch-ready prompts (Phase 1), with full MCP integration later (Phase 2)

## Architecture

```
ai_agency/
├── pyproject.toml                 # Package config (using uv/pip)
├── Dockerfile                     # Multi-stage production image
├── docker-compose.yml             # Dev environment with hot-reload
├── .dockerignore                  # Keep images lean
├── Makefile                       # Convenience commands (build, run, test, lint)
├── .env.example                   # Template for API keys
├── src/
│   └── ai_agency/
│       ├── __init__.py
│       ├── cli.py                 # CLI entry point (Click-based)
│       ├── config.py              # Configuration & env management
│       ├── models/
│       │   ├── __init__.py
│       │   └── prd.py             # Pydantic models for PRD structure
│       ├── generators/
│       │   ├── __init__.py
│       │   ├── prd_generator.py   # LLM-powered PRD generation
│       │   └── stitch_prompt.py   # Stitch prompt generation from PRD
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py            # Abstract LLM provider interface
│       │   ├── anthropic.py       # Claude provider
│       │   └── openai.py          # OpenAI provider
│       └── templates/
│           ├── __init__.py
│           └── prd_system.py      # System prompts for PRD generation
├── output/                        # Default output directory (gitignored)
└── tests/
    ├── __init__.py
    ├── test_models.py
    └── test_generators.py
```

## Docker Strategy

### Why Docker

- **Reproducible environment**: Python version, system deps, and pip packages are all pinned.
- **Zero-setup onboarding**: `docker compose run cli --help` works from a fresh clone.
- **Isolation**: API keys stay in `.env`, never leak into the host environment.
- **CI-ready**: Same image runs tests locally and in CI pipelines.

### Dockerfile Design (multi-stage)

```
Stage 1 ("builder"):
  - python:3.11-slim base
  - Install build tools
  - Copy pyproject.toml, install dependencies into a virtualenv
  - Copy source code, install the package

Stage 2 ("runtime"):
  - python:3.11-slim base (clean)
  - Copy only the virtualenv from builder
  - Set ENTRYPOINT to the ai-agency CLI
  - Non-root user for security
```

This gives a lean (~150MB) production image with no build artifacts.

### docker-compose.yml Design

```yaml
services:
  cli:
    # For running CLI commands: docker compose run cli prd generate -t "..."
    build: .
    env_file: .env
    volumes:
      - ./output:/app/output    # Persist generated files to host
      - ./src:/app/src          # Hot-reload during development
    entrypoint: ["ai-agency"]

  test:
    # For running tests: docker compose run test
    build: .
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    entrypoint: ["pytest"]
    command: ["-v"]

  lint:
    # For linting: docker compose run lint
    build: .
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    entrypoint: ["ruff"]
    command: ["check", "src/", "tests/"]
```

### Makefile Shortcuts

| Command            | What it does                                      |
|--------------------|---------------------------------------------------|
| `make build`       | Build the Docker image                            |
| `make test`        | Run pytest in container                           |
| `make lint`        | Run ruff linter in container                      |
| `make prd`         | Generate PRD (prompts for text or file)           |
| `make design`      | Generate Stitch prompts from existing PRD         |
| `make pipeline`    | Full pipeline: requirements → PRD → Stitch        |
| `make shell`       | Drop into a shell inside the container            |
| `make clean`       | Remove built images and output files              |

## Step-by-Step Implementation

### Step 1: Project Scaffolding ✅ (Complete)
- `pyproject.toml` with dependencies: anthropic, openai, instructor, pydantic, click, rich, python-dotenv
- `.env.example` with required API keys
- Directory structure created

### Step 2: Pydantic PRD Models ✅ (Complete)
- `PRD` root model with full schema:
  - `ProductOverview`, `UserPersona`, `UserJourney`, `Feature`, `DataModel`,
    `APIEndpoint`, `EdgeCase`, `SuccessMetric`, `TechRecommendations`
- Markdown export via `PRD.to_markdown()`
- JSON schema generation for downstream LLM consumption

### Step 3: LLM Provider Abstraction ✅ (Complete)
- `LLMProvider` ABC with `generate_structured(prompt, response_model) -> T`
- `AnthropicProvider` and `OpenAIProvider` using `instructor`
- Factory function `create_provider()` driven by `AI_PROVIDER` env var

### Step 4: PRD Generator ✅ (Complete)
- `generate_prd(requirements)` → PRD
- `generate_prd_from_file(path)` → PRD
- `save_prd(prd, output_dir)` → (json_path, md_path)
- `load_prd(json_path)` → PRD

### Step 5: Stitch Prompt Generator ✅ (Complete)
- `_collect_screens(prd)` → aggregates screens from features + journeys
- `generate_stitch_prompt(...)` → per-screen Stitch-optimized prompt
- `generate_all_stitch_prompts(prd)` → dict of all screen prompts
- `save_stitch_prompts(prompts, output_dir)` → files + manifest.json

### Step 6: CLI Interface ✅ (Complete)
- `ai-agency prd generate --input FILE | --text TEXT --output DIR`
- `ai-agency design generate --prd FILE --output DIR`
- `ai-agency pipeline --input FILE | --text TEXT --output DIR`

### Step 7: Configuration ✅ (Complete)
- `.env` loading via python-dotenv
- `AI_PROVIDER`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `AI_MODEL`

### Step 8: Tests ✅ (Complete)
- `test_models.py`: roundtrip JSON, dict, markdown, schema, enums
- `test_generators.py`: screen collection, prompt generation, file I/O

### Step 9: Docker Support (Current)
- **Dockerfile**: Multi-stage build — `builder` installs deps, `runtime` is lean
- **docker-compose.yml**: `cli`, `test`, `lint` services with volume mounts
- **.dockerignore**: Exclude .git, .env, __pycache__, output/, .venv, etc.
- **Makefile**: Convenience targets wrapping docker compose commands

## Phase 2 (Future): Full Stitch MCP Integration
- Install `@_davideast/stitch-mcp` via Node.js subprocess
- Use Python MCP client (`mcp` pip package) to connect to the Stitch MCP server
- Automate: PRD → Stitch prompts → MCP call → HTML/CSS output → saved locally
- Add `ai-agency design generate --use-stitch` flag
- Docker compose service for MCP server (Node.js sidecar container)

## Key Design Decisions
1. **`instructor` library** over raw API calls: handles structured output, retries, and validation for both Anthropic and OpenAI
2. **Click** over argparse: cleaner CLI with subcommands, auto-help generation
3. **JSON + Markdown dual output**: JSON for machine consumption (pipeline), Markdown for human review
4. **Prompt-first Stitch approach**: Zero infrastructure needed, user just copies prompts to stitch.withgoogle.com
5. **Multi-stage Docker build**: Keeps production image lean (~150MB), separates build from runtime
6. **docker-compose for DX**: Volume mounts for source enable development without rebuilding; separate services for test/lint
7. **Makefile as CLI wrapper**: Memorable commands (`make test`, `make prd`) instead of long docker compose invocations
