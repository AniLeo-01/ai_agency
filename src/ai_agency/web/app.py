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
from ai_agency.generators.competitor_analysis_generator import (
    generate_competitor_analysis,
    save_competitor_analysis,
)
from ai_agency.generators.market_analysis_generator import (
    generate_market_analysis,
    save_market_analysis,
)
from ai_agency.generators.pitch_deck_generator import generate_pitch_deck, save_pitch_deck
from ai_agency.generators.prd_generator import generate_prd, load_prd, save_prd
from ai_agency.generators.roadmap_generator import generate_roadmap, save_roadmap
from ai_agency.generators.stitch_prompt import generate_all_stitch_prompts, save_stitch_prompts
from ai_agency.generators.viability_generator import generate_viability, save_viability

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


class GenerateFromPRDRequest(BaseModel):
    requirements: str | None = None
    prd_json: dict | None = None


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


# --- Shared helper for analysis tools ---


def _build_analysis_prompt(body: GenerateFromPRDRequest) -> str:
    """Build a prompt from either raw requirements or a PRD JSON."""
    if body.requirements:
        return body.requirements
    if body.prd_json:
        prd_data = body.prd_json
        ov = prd_data.get("product_overview", {})
        features = prd_data.get("features", [])
        feature_names = [f.get("name", "") for f in features]
        return (
            f"Product: {ov.get('name', 'Unknown')}\n"
            f"Tagline: {ov.get('tagline', '')}\n"
            f"Problem: {ov.get('problem_statement', '')}\n"
            f"Target Market: {ov.get('target_market', '')}\n"
            f"Competitive Landscape: {ov.get('competitive_landscape', '')}\n"
            f"Features: {', '.join(feature_names)}\n"
            f"Objectives: {chr(10).join(ov.get('objectives', []))}"
        )
    return ""


# --- Market Analysis ---


@app.post("/api/market-analysis/generate")
def api_generate_market_analysis(body: GenerateFromPRDRequest):
    try:
        prompt = _build_analysis_prompt(body)
        if not prompt:
            return {"success": False, "error": "Provide requirements text or a PRD."}

        analysis = generate_market_analysis(prompt)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_market_analysis(analysis, OUTPUT_DIR)

        return {
            "success": True,
            "analysis_json": json.loads(json_path.read_text()),
            "analysis_markdown": md_path.read_text(),
            "summary": {
                "tam": analysis.market_sizing.tam_value,
                "sam": analysis.market_sizing.sam_value,
                "som": analysis.market_sizing.som_value,
                "segments": len(analysis.market_segments),
                "trends": len(analysis.trends),
                "avg_opportunity_score": round(
                    sum(o.score for o in analysis.opportunity_scores)
                    / len(analysis.opportunity_scores),
                    1,
                ),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# --- Competitor Analysis ---


@app.post("/api/competitor-analysis/generate")
def api_generate_competitor_analysis(body: GenerateFromPRDRequest):
    try:
        prompt = _build_analysis_prompt(body)
        if not prompt:
            return {"success": False, "error": "Provide requirements text or a PRD."}

        analysis = generate_competitor_analysis(prompt)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_competitor_analysis(analysis, OUTPUT_DIR)

        return {
            "success": True,
            "analysis_json": json.loads(json_path.read_text()),
            "analysis_markdown": md_path.read_text(),
            "summary": {
                "competitors": len(analysis.competitors),
                "features_compared": len(analysis.feature_matrix),
                "swot_items": (
                    len(analysis.swot.strengths)
                    + len(analysis.swot.weaknesses)
                    + len(analysis.swot.opportunities)
                    + len(analysis.swot.threats)
                ),
                "positioning": analysis.positioning.value_proposition,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# --- Product Viability ---


@app.post("/api/viability/generate")
def api_generate_viability(body: GenerateFromPRDRequest):
    try:
        prompt = _build_analysis_prompt(body)
        if not prompt:
            return {"success": False, "error": "Provide requirements text or a PRD."}

        viability = generate_viability(prompt)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_viability(viability, OUTPUT_DIR)

        weighted_score = sum(v.score * v.weight for v in viability.viability_scores)
        max_score = sum(10 * v.weight for v in viability.viability_scores)

        return {
            "success": True,
            "viability_json": json.loads(json_path.read_text()),
            "viability_markdown": md_path.read_text(),
            "summary": {
                "verdict": viability.overall_viability,
                "weighted_score": weighted_score,
                "max_score": max_score,
                "score_pct": round(weighted_score / max_score * 100) if max_score else 0,
                "budget": viability.total_budget_range,
                "timeline": viability.total_timeline,
                "risks": len(viability.risks),
                "tech_areas": len(viability.tech_feasibility),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# --- Product Roadmap ---


@app.post("/api/roadmap/generate")
def api_generate_roadmap(body: GenerateFromPRDRequest):
    try:
        prompt = _build_analysis_prompt(body)
        if not prompt:
            return {"success": False, "error": "Provide requirements text or a PRD."}

        roadmap = generate_roadmap(prompt)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_roadmap(roadmap, OUTPUT_DIR)

        total_features = sum(len(p.features) for p in roadmap.phases)

        return {
            "success": True,
            "roadmap_json": json.loads(json_path.read_text()),
            "roadmap_markdown": md_path.read_text(),
            "summary": {
                "phases": len(roadmap.phases),
                "total_features": total_features,
                "total_duration": roadmap.total_duration,
                "team_roles": len(roadmap.resource_allocation),
                "dependencies": len(roadmap.dependency_chains),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# --- Pitch Deck ---


@app.post("/api/pitch-deck/generate")
def api_generate_pitch_deck(body: GenerateFromPRDRequest):
    try:
        prompt = _build_analysis_prompt(body)
        if not prompt:
            return {"success": False, "error": "Provide requirements text or a PRD."}

        deck = generate_pitch_deck(prompt)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path, md_path = save_pitch_deck(deck, OUTPUT_DIR)

        return {
            "success": True,
            "deck_json": json.loads(json_path.read_text()),
            "deck_markdown": md_path.read_text(),
            "summary": {
                "company_name": deck.company_name,
                "tagline": deck.tagline,
                "slides": len(deck.slides),
                "funding_ask": deck.funding_ask.amount,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def start():
    """Entry point for the web server."""
    import uvicorn
    uvicorn.run("ai_agency.web.app:app", host="0.0.0.0", port=8000, reload=True)
