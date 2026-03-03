"""FastAPI web application for the AI Agency toolkit."""

import json
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ai_agency.config import get_model, get_provider
from ai_agency.generators.prd_generator import generate_prd, load_prd, save_prd
from ai_agency.generators.stitch_prompt import generate_all_stitch_prompts, save_stitch_prompts

WEB_DIR = Path(__file__).parent
OUTPUT_DIR = Path("/app/output") if Path("/app/output").exists() else Path("output")

# Samples dir: check Docker mount first, then relative to project root
_DOCKER_SAMPLES = Path("/app/samples")
_LOCAL_SAMPLES = Path(__file__).resolve().parent.parent.parent.parent / "samples"
SAMPLES_DIR = _DOCKER_SAMPLES if _DOCKER_SAMPLES.exists() else _LOCAL_SAMPLES

app = FastAPI(title="AI Agency", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


# --- Request / Response models ---


class GeneratePRDRequest(BaseModel):
    requirements: str


class GenerateDesignRequest(BaseModel):
    prd_json: dict | None = None


class PipelineRequest(BaseModel):
    requirements: str


# --- Pages ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# --- API routes ---


@app.get("/api/config")
async def get_config():
    try:
        provider = get_provider()
        model = get_model()
    except Exception:
        provider = "not configured"
        model = "not configured"
    return {"provider": provider, "model": model}


@app.post("/api/prd/generate")
def api_generate_prd(body: GeneratePRDRequest):
    try:
        prd = generate_prd(body.requirements)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_prd(prd, OUTPUT_DIR)
        return {
            "success": True,
            "prd_json": json.loads(json_path.read_text()),
            "prd_markdown": md_path.read_text(),
            "summary": {
                "product_name": prd.product_overview.name,
                "tagline": prd.product_overview.tagline,
                "features": len(prd.features),
                "api_endpoints": len(prd.api_endpoints),
                "data_models": len(prd.data_models),
                "personas": len(prd.user_personas),
                "journeys": len(prd.user_journeys),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/design/generate")
async def api_generate_design(body: GenerateDesignRequest):
    try:
        # Load from provided JSON or from saved file
        if body.prd_json:
            from ai_agency.models.prd import PRD
            prd = PRD.model_validate(body.prd_json)
        else:
            prd_path = OUTPUT_DIR / "prd.json"
            if not prd_path.exists():
                return {"success": False, "error": "No PRD found. Generate a PRD first."}
            prd = load_prd(prd_path)

        prompts = generate_all_stitch_prompts(prd)
        design_dir = OUTPUT_DIR / "designs"
        save_stitch_prompts(prompts, design_dir)

        return {
            "success": True,
            "screens": {name: text for name, text in prompts.items()},
            "screen_count": len(prompts),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/pipeline")
def api_pipeline(body: PipelineRequest):
    try:
        # Step 1: Generate PRD
        prd = generate_prd(body.requirements)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_prd(prd, OUTPUT_DIR)

        # Step 2: Generate design prompts
        prompts = generate_all_stitch_prompts(prd)
        design_dir = OUTPUT_DIR / "designs"
        save_stitch_prompts(prompts, design_dir)

        return {
            "success": True,
            "prd_json": json.loads(json_path.read_text()),
            "prd_markdown": md_path.read_text(),
            "screens": {name: text for name, text in prompts.items()},
            "summary": {
                "product_name": prd.product_overview.name,
                "tagline": prd.product_overview.tagline,
                "features": len(prd.features),
                "api_endpoints": len(prd.api_endpoints),
                "data_models": len(prd.data_models),
                "personas": len(prd.user_personas),
                "journeys": len(prd.user_journeys),
                "screens": len(prompts),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/prd/latest")
async def api_latest_prd():
    """Return the most recently generated PRD if it exists."""
    json_path = OUTPUT_DIR / "prd.json"
    md_path = OUTPUT_DIR / "prd.md"
    if not json_path.exists():
        return {"success": False, "error": "No PRD generated yet."}
    return {
        "success": True,
        "prd_json": json.loads(json_path.read_text()),
        "prd_markdown": md_path.read_text() if md_path.exists() else "",
    }


@app.get("/api/samples")
async def api_samples():
    """Return available sample requirement files."""
    samples = []
    if SAMPLES_DIR.exists():
        for f in sorted(SAMPLES_DIR.glob("*.txt")):
            content = f.read_text(encoding="utf-8")
            # Use filename as label: "saas_team_workspace" -> "SaaS Team Workspace"
            label = f.stem.replace("_", " ").title()
            # Fix common casing
            label = label.replace("Saas", "SaaS").replace("Devops", "DevOps")
            label = label.replace("Ecommerce", "E-Commerce")
            # Extract first paragraph as description
            paragraphs = content.strip().split("\n\n")
            description = paragraphs[0].strip() if paragraphs else ""
            samples.append({
                "id": f.stem,
                "label": label,
                "description": description,
                "content": content,
            })
    return {"samples": samples}


def start():
    """Entry point for the web server."""
    import uvicorn
    uvicorn.run("ai_agency.web.app:app", host="0.0.0.0", port=8000, reload=True)
