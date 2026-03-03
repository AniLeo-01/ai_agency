# AI Agency MVP - Implementation Plan

## Overview

Build two initial tools for the agency's "Spec-to-Ship" pipeline:
1. **PRD Builder** - Transforms raw customer requirements into structured, AI-optimized PRDs
2. **UI Design Generator** - Extracts design sections from PRDs and generates Google Stitch-ready prompts (Phase 1), with full MCP integration later (Phase 2)

## Architecture

```
ai_agency/
├── pyproject.toml                 # Package config (using uv/pip)
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

## Step-by-Step Implementation

### Step 1: Project Scaffolding
- Create `pyproject.toml` with dependencies:
  - `anthropic` - Claude API
  - `openai` - OpenAI API
  - `pydantic` >= 2.0 - Data models & validation
  - `instructor` - Structured LLM output (works with both providers)
  - `click` - CLI framework
  - `rich` - Terminal output formatting
  - `python-dotenv` - Environment variable management
- Create `.env.example` with required API keys
- Create the directory structure

### Step 2: Pydantic PRD Models (`src/ai_agency/models/prd.py`)
Define the structured PRD schema:
- `PRD` (root model)
  - `product_overview: ProductOverview` (name, description, objectives, target_market)
  - `user_personas: list[UserPersona]` (name, role, goals, pain_points, tech_proficiency)
  - `user_journeys: list[UserJourney]` (persona, journey_name, steps[], entry_point, success_criteria)
  - `features: list[Feature]` (name, description, priority, business_logic, ui_requirements, acceptance_criteria)
  - `data_models: list[DataModel]` (name, description, fields as JSON schema)
  - `api_endpoints: list[APIEndpoint]` (method, path, description, request_schema, response_schema)
  - `edge_cases: list[EdgeCase]` (scenario, expected_behavior, severity)
  - `success_metrics: list[SuccessMetric]` (metric, target, measurement_method)
  - `constraints: list[str]`
  - `tech_recommendations: TechRecommendations` (frontend, backend, database, deployment)

Each model includes `model_config` with JSON schema generation for LLM consumption.

### Step 3: LLM Provider Abstraction (`src/ai_agency/providers/`)
- `base.py`: Abstract `LLMProvider` class with `generate_structured(prompt, model_class) -> T`
- `anthropic.py`: Claude implementation using `instructor` + `anthropic` SDK
- `openai.py`: OpenAI implementation using `instructor` + `openai` SDK
- Config selects provider via `AI_PROVIDER` env var (default: `anthropic`)

### Step 4: PRD Generator (`src/ai_agency/generators/prd_generator.py`)
- Takes raw customer input (text string or file path)
- Applies the system prompt template that instructs the LLM to:
  - Ask clarifying questions if input is ambiguous (interactive mode)
  - Separate business logic from UI requirements
  - Generate concrete data models with JSON schemas
  - Define RESTful API endpoints
- Uses `instructor` to get structured `PRD` Pydantic model output
- Exports PRD as:
  - JSON (machine-readable, for downstream tools)
  - Markdown (human-readable, for review)

### Step 5: Stitch Prompt Generator (`src/ai_agency/generators/stitch_prompt.py`)
- Takes a generated PRD (JSON file or PRD object)
- Extracts UI-relevant sections:
  - User journeys (step-by-step flows)
  - Feature UI requirements
  - User personas (for context)
- For each screen/page identified in the PRD, generates a Stitch-optimized prompt that includes:
  - Screen purpose and context
  - Key UI elements needed
  - User actions on this screen
  - Data to display
  - Navigation flows
- Outputs a directory of prompt files (one per screen), ready to paste into stitch.withgoogle.com

### Step 6: CLI Interface (`src/ai_agency/cli.py`)
Three commands:
```bash
# Generate a PRD from customer requirements
ai-agency prd generate --input requirements.txt --output output/my_project/
ai-agency prd generate --interactive  # Interactive mode with follow-up questions

# Generate Stitch prompts from a PRD
ai-agency design generate --prd output/my_project/prd.json --output output/my_project/designs/

# Full pipeline: requirements → PRD → Stitch prompts
ai-agency pipeline run --input requirements.txt --output output/my_project/
```

### Step 7: Configuration (`src/ai_agency/config.py`)
- Load from `.env` file + environment variables
- Required: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Optional: `AI_PROVIDER` (anthropic|openai), `AI_MODEL` (model name override)
- Optional: `STITCH_API_KEY` (for future MCP integration)

### Step 8: Tests
- `test_models.py`: Validate PRD Pydantic models serialize/deserialize correctly
- `test_generators.py`: Test prompt template generation, Stitch prompt extraction logic

## Phase 2 (Future): Full Stitch MCP Integration
- Install `@_davideast/stitch-mcp` via Node.js subprocess
- Use Python MCP client (`mcp` pip package) to connect to the Stitch MCP server
- Automate: PRD → Stitch prompts → MCP call → HTML/CSS output → saved locally
- Add `ai-agency design generate --use-stitch` flag

## Key Design Decisions
1. **`instructor` library** over raw API calls: handles structured output, retries, and validation for both Anthropic and OpenAI
2. **Click** over argparse: cleaner CLI with subcommands, auto-help generation
3. **JSON + Markdown dual output**: JSON for machine consumption (pipeline), Markdown for human review
4. **Prompt-first Stitch approach**: Zero infrastructure needed, user just copies prompts to stitch.withgoogle.com
