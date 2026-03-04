# AI Agency

AI-native product development toolkit — a **Spec-to-Ship** pipeline that transforms raw customer requirements into production-ready specifications.

## What It Does

1. **PRD Builder** — Converts customer requirements into structured, AI-optimized Product Requirements Documents (JSON + Markdown)
2. **UI Design Generator** — Extracts UI specifications from PRDs and generates Google Stitch-ready design prompts
3. **Full Pipeline** — Runs both steps end-to-end in a single command

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An API key for [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)

### Setup

```bash
# Clone the repo
git clone https://github.com/AniLeo-01/ai_agency.git
cd ai_agency

# Configure your API key
cp .env.example .env
# Edit .env with your API key
```

### Web UI

```bash
make build    # Build Docker images
make web      # Start the web UI at http://localhost:8080
```

Open [http://localhost:8080](http://localhost:8080) in your browser. The UI provides:

- **Pipeline** — Enter requirements, get a full PRD + design prompts in one step
- **PRD Generator** — Generate a structured PRD from raw text
- **Design Prompts** — Generate Stitch-ready UI prompts from an existing PRD
- **Results** — View stats, browse the PRD document/JSON, and copy design prompts

### CLI

```bash
# Generate a PRD
make prd TEXT="Build a task management app for small teams"

# Generate design prompts from an existing PRD
make design

# Full pipeline (PRD + design prompts)
make pipeline TEXT="Build a task management app with Kanban boards and time tracking"
```

## Project Structure

```
src/ai_agency/
├── cli.py                  # Click-based CLI
├── config.py               # Environment configuration
├── models/
│   └── prd.py              # Pydantic PRD schema (11 sub-models)
├── generators/
│   ├── prd_generator.py    # LLM-powered PRD generation
│   └── stitch_prompt.py    # Stitch design prompt extraction
├── providers/
│   ├── base.py             # Abstract LLM provider
│   ├── anthropic.py        # Claude provider
│   └── openai.py           # GPT provider
├── templates/
│   └── prd_system.py       # System prompt for PRD generation
└── web/
    ├── app.py              # FastAPI web application
    ├── static/             # CSS and JS
    └── templates/          # HTML templates
```

## Configuration

Set these in your `.env` file:

| Variable | Description | Default |
|---|---|---|
| `AI_PROVIDER` | `anthropic` or `openai` | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `AI_MODEL` | Model override | Claude Sonnet 4 / GPT-4o |
| `STITCH_ACCESS_TOKEN` | Google Stitch access token | — |
| `STITCH_PROJECT_ID` | Google Cloud project ID | — |

### Google Stitch Setup

To enable the Stitch design generation integration:

1. Enable the Stitch API in Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud beta services mcp enable stitch.googleapis.com
   ```

2. Get an access token:
   ```bash
   gcloud auth application-default print-access-token
   ```

3. Add to your `.env`:
   ```
   STITCH_ACCESS_TOKEN=your-token-here
   STITCH_PROJECT_ID=your-gcp-project-id
   ```

4. In the web UI, generate design prompts, then click **Send to Stitch** to create UI designs.

## Docker

The project uses a multi-stage Dockerfile:

- **runtime** stage — CLI entrypoint (`ai-agency`)
- **web** stage — Uvicorn server (mapped to host port 8080)

### Available Make Targets

| Command | Description |
|---|---|
| `make build` | Build all Docker images |
| `make web` | Start the web UI (port 8080) |
| `make web-dev` | Start the web UI in background |
| `make prd` | Generate a PRD |
| `make design` | Generate Stitch design prompts |
| `make pipeline` | Full end-to-end pipeline |
| `make test` | Run tests |
| `make lint` | Run ruff linter |
| `make shell` | Open a shell in the container |
| `make clean` | Remove images and output files |

## Output

The pipeline produces:

```
output/
├── prd.json              # Machine-readable PRD
├── prd.md                # Human-readable PRD
└── designs/
    ├── dashboard.txt     # Stitch prompt per screen
    ├── settings.txt
    └── manifest.json     # Screen index
```

## Development

```bash
make test     # Run pytest
make lint     # Run ruff
make shell    # Interactive shell in container
```
