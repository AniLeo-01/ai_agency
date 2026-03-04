"""FastAPI web application for the AI Agency toolkit."""

import json
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ai_agency.config import get_model, get_provider, get_stitch_project_id, get_stitch_token
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


class StitchProjectRequest(BaseModel):
    name: str


class StitchGenerateRequest(BaseModel):
    project_id: str
    screens: dict[str, str]  # screen_name -> prompt text


class StitchEditRequest(BaseModel):
    project_id: str
    screen_ids: list[str]
    prompt: str


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
    prd_data = json.loads(json_path.read_text())
    overview = prd_data.get("product_overview", {})
    return {
        "success": True,
        "prd_json": prd_data,
        "prd_markdown": md_path.read_text() if md_path.exists() else "",
        "summary": {
            "product_name": overview.get("name", "Unknown"),
            "tagline": overview.get("tagline", ""),
            "features": len(prd_data.get("features", [])),
            "api_endpoints": len(prd_data.get("api_endpoints", [])),
            "data_models": len(prd_data.get("data_models", [])),
            "personas": len(prd_data.get("user_personas", [])),
            "journeys": len(prd_data.get("user_journeys", [])),
        },
    }


@app.get("/api/designs/latest")
async def api_latest_designs():
    """Return the most recently generated design prompts if they exist."""
    design_dir = OUTPUT_DIR / "designs"
    manifest_path = design_dir / "manifest.json"
    if not manifest_path.exists():
        return {"success": False, "error": "No designs generated yet."}
    manifest = json.loads(manifest_path.read_text())
    screens = {}
    for screen_name, filename in manifest.get("prompt_files", {}).items():
        prompt_path = design_dir / filename
        if prompt_path.exists():
            screens[screen_name] = prompt_path.read_text(encoding="utf-8")
    return {
        "success": True,
        "screens": screens,
        "screen_count": len(screens),
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


# --- Stitch API routes ---


@app.get("/api/stitch/status")
async def api_stitch_status():
    """Check if Stitch is configured and return project list."""
    token = get_stitch_token()
    if not token:
        return {
            "configured": False,
            "error": "Set STITCH_ACCESS_TOKEN in .env",
        }
    try:
        from ai_agency.integrations.stitch import StitchClient

        project_id = get_stitch_project_id()
        client = StitchClient(token, project_id)
        projects = client.list_projects()
        return {"configured": True, "projects": projects, "gcp_project": project_id}
    except Exception as e:
        error_str = str(e)
        if "401" in error_str:
            return {
                "configured": True,
                "auth_error": True,
                "error": "Access token expired. Run: gcloud auth application-default print-access-token",
            }
        return {"configured": False, "error": error_str}


@app.post("/api/stitch/project")
def api_stitch_create_project(body: StitchProjectRequest):
    """Create a new Stitch project."""
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        result = client.create_project(body.name)
        if isinstance(result, dict) and result.get("isError"):
            msg = ""
            for item in result.get("content", []):
                if item.get("type") == "text":
                    msg = item["text"]
                    break
            return {"success": False, "error": msg or "Stitch API error"}
        return {"success": True, "project": result}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/stitch/generate")
def api_stitch_generate(body: StitchGenerateRequest):
    """Generate screens in Stitch from design prompts."""
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        results = {}
        errors = {}
        for screen_name, prompt in body.screens.items():
            try:
                result = client.generate_screen(prompt, body.project_id)
                results[screen_name] = result
            except Exception as e:
                errors[screen_name] = str(e)

        response = {
            "success": True,
            "generated": results,
            "errors": errors,
            "total": len(body.screens),
            "succeeded": len(results),
            "failed": len(errors),
            "project_id": body.project_id,
        }

        # Persist to disk
        _save_stitch_results(response)

        return response
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def _save_stitch_results(data: dict):
    """Save Stitch generation results to output/stitch/results.json."""
    stitch_dir = OUTPUT_DIR / "stitch"
    stitch_dir.mkdir(parents=True, exist_ok=True)
    results_path = stitch_dir / "results.json"

    # Merge with existing results if present
    existing = {}
    if results_path.exists():
        try:
            existing = json.loads(results_path.read_text())
        except Exception:
            existing = {}

    # Update project_id and merge generated screens
    existing["project_id"] = data.get("project_id", existing.get("project_id", ""))
    prev_gen = existing.get("generated", {})
    prev_gen.update(data.get("generated", {}))
    existing["generated"] = prev_gen
    prev_err = existing.get("errors", {})
    prev_err.update(data.get("errors", {}))
    existing["errors"] = prev_err
    existing["total"] = len(prev_gen) + len(prev_err)
    existing["succeeded"] = len(prev_gen)
    existing["failed"] = len(prev_err)
    existing["success"] = True

    results_path.write_text(json.dumps(existing, indent=2, default=str))


def _find_screen_url(screen_id: str, url_key: str = "htmlCode") -> str | None:
    """Look up a screen's download URL from saved results.

    url_key: 'htmlCode' for code URL, 'screenshot' for image URL.
    """
    results_path = OUTPUT_DIR / "stitch" / "results.json"
    if not results_path.exists():
        return None
    try:
        data = json.loads(results_path.read_text())
        for _name, result in data.get("generated", {}).items():
            sc = result.get("structuredContent", {})
            for comp in sc.get("outputComponents", []):
                for s in comp.get("design", {}).get("screens", []):
                    if s.get("id") == screen_id:
                        entry = s.get(url_key, {})
                        if isinstance(entry, dict):
                            return entry.get("downloadUrl")
    except Exception:
        pass
    return None


@app.get("/api/stitch/latest")
async def api_stitch_latest():
    """Return the most recently saved Stitch results."""
    results_path = OUTPUT_DIR / "stitch" / "results.json"
    if not results_path.exists():
        return {"success": False, "error": "No Stitch results saved yet."}
    try:
        data = json.loads(results_path.read_text())
        return data
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/stitch/edit")
def api_stitch_edit_screen(body: StitchEditRequest):
    """Edit existing Stitch screens with a new prompt."""
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        result = client.edit_screens(body.project_id, body.screen_ids, body.prompt)

        if isinstance(result, dict) and result.get("isError"):
            msg = ""
            for item in result.get("content", []):
                if item.get("type") == "text":
                    msg = item["text"]
                    break
            return {"success": False, "error": msg or "Stitch edit error"}

        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.delete("/api/stitch/screen/{project_id}/{screen_id}")
def api_stitch_delete_screen(project_id: str, screen_id: str):
    """Delete a screen from Stitch and remove from saved results."""
    # Try to delete via Stitch API (may not be supported)
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        client.delete_screen(project_id, screen_id)
    except Exception:
        pass  # API delete is best-effort; we always clean up locally

    # Remove from saved results
    results_path = OUTPUT_DIR / "stitch" / "results.json"
    if results_path.exists():
        try:
            data = json.loads(results_path.read_text())
            generated = data.get("generated", {})
            # Walk through each screen group and remove matching screen IDs
            to_remove = []
            for name, result in generated.items():
                sc = result.get("structuredContent", {})
                comps = sc.get("outputComponents", [])
                for comp in comps:
                    design = comp.get("design", {})
                    screens = design.get("screens", [])
                    design["screens"] = [
                        s for s in screens if s.get("id") != screen_id
                    ]
                # If no screens left in any component, mark for removal
                remaining = sum(
                    len(c.get("design", {}).get("screens", []))
                    for c in comps
                    if c.get("design")
                )
                if remaining == 0 and comps:
                    to_remove.append(name)
            for name in to_remove:
                del generated[name]
            data["generated"] = generated
            data["succeeded"] = len(generated)
            data["total"] = len(generated) + len(data.get("errors", {}))
            results_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            return {"success": False, "error": f"Failed to update saved results: {e}"}

    return {"success": True}


@app.get("/api/stitch/screen/{project_id}/{screen_id}/code")
def api_stitch_screen_code(project_id: str, screen_id: str):
    """Fetch the HTML code for a Stitch screen."""
    import httpx

    # First try to find the direct download URL from saved results
    code_url = _find_screen_url(screen_id, "htmlCode")
    if code_url:
        try:
            resp = httpx.get(code_url, timeout=30)
            resp.raise_for_status()
            return {"success": True, "html": resp.text}
        except Exception:
            pass  # Fall through to API

    # Fallback: use Stitch API
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        code = client.fetch_screen_code(project_id, screen_id)
        return {"success": True, "html": code}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/stitch/screen/{project_id}/{screen_id}/image")
def api_stitch_screen_image(project_id: str, screen_id: str):
    """Fetch the screenshot image for a Stitch screen as base64."""
    import base64

    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        image_bytes = client.fetch_screen_image(project_id, screen_id)
        return {
            "success": True,
            "image": base64.b64encode(image_bytes).decode(),
            "mime_type": "image/png",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def start():
    """Entry point for the web server."""
    import uvicorn
    uvicorn.run("ai_agency.web.app:app", host="0.0.0.0", port=8000, reload=True)
