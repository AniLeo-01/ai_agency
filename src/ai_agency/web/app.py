"""FastAPI web application for the AI Agency toolkit."""

import json
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ai_agency.config import get_model, get_provider, get_stitch_project_id, get_stitch_token
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


class StitchProjectRequest(BaseModel):
    name: str


class StitchGenerateRequest(BaseModel):
    project_id: str
    screens: dict[str, str]  # screen_name -> prompt text


class StitchEditRequest(BaseModel):
    project_id: str
    screen_ids: list[str]
    prompt: str


class GenerateFromPRDRequest(BaseModel):
    requirements: str | None = None
    prd_json: dict | None = None


# --- Pages ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(name="index.html", request=request)


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
    from ai_agency.config import get_stitch_api_key
    from ai_agency.integrations.stitch import StitchClient

    api_key = get_stitch_api_key()
    token = "" if api_key else get_stitch_token()
    if not api_key and not token:
        return {
            "configured": False,
            "error": "Set STITCH_API_KEY or STITCH_ACCESS_TOKEN in .env",
        }
    try:
        if api_key:
            client = StitchClient(api_key=api_key)
        else:
            project_id = get_stitch_project_id()
            client = StitchClient(access_token=token, project_id=project_id)
        projects = client.list_projects()
        return {
            "configured": True,
            "projects": projects,
            "auth_method": "api_key" if api_key else "oauth",
            "gcp_project": "" if api_key else get_stitch_project_id(),
        }
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "403" in error_str:
            return {
                "configured": True,
                "auth_error": True,
                "error": "Auth failed. Check STITCH_API_KEY, or refresh OAuth: gcloud auth application-default print-access-token",
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
    """Generate screens in Stitch, streaming each result as SSE."""
    def _stream():
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        results = {}
        errors = {}
        total = len(body.screens)

        for screen_name, prompt in body.screens.items():
            try:
                result = client.generate_screen(prompt, body.project_id)
                results[screen_name] = result
                # Cache assets immediately while URLs are fresh
                _cache_screen_assets(result)
                event = {"event": "screen", "name": screen_name, "status": "ok", "result": result}
            except Exception as e:
                errors[screen_name] = str(e)
                event = {"event": "screen", "name": screen_name, "status": "error", "error": str(e)}
            yield f"data: {json.dumps(event, default=str)}\n\n"

        response = {
            "success": True,
            "generated": results,
            "errors": errors,
            "total": total,
            "succeeded": len(results),
            "failed": len(errors),
            "project_id": body.project_id,
            "prompts": dict(body.screens),
        }
        _save_stitch_results(response)

        done = {"event": "done", "succeeded": len(results), "failed": len(errors), "total": total}
        yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


class StitchRetryRequest(BaseModel):
    screen_names: list[str]  # names of failed prompts to retry


@app.post("/api/stitch/retry")
def api_stitch_retry(body: StitchRetryRequest):
    """Retry generation for failed prompts, streaming each result as SSE."""
    results_path = OUTPUT_DIR / "stitch" / "results.json"
    if not results_path.exists():
        return {"success": False, "error": "No Stitch results found."}
    try:
        existing = json.loads(results_path.read_text())
    except Exception as e:
        return {"success": False, "error": str(e)}

    project_id = existing.get("project_id", "")
    stored_prompts = existing.get("prompts", {})
    if not project_id:
        return {"success": False, "error": "No project ID in saved results."}

    screens_to_retry = {}
    missing = []
    for name in body.screen_names:
        if name in stored_prompts:
            screens_to_retry[name] = stored_prompts[name]
        else:
            missing.append(name)

    if not screens_to_retry:
        return {"success": False, "error": f"No stored prompts found for: {', '.join(missing)}"}

    def _stream():
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        results = {}
        errors = {}

        for screen_name, prompt in screens_to_retry.items():
            try:
                result = client.generate_screen(prompt, project_id)
                results[screen_name] = result
                _cache_screen_assets(result)
                event = {"event": "screen", "name": screen_name, "status": "ok", "result": result}
            except Exception as e:
                errors[screen_name] = str(e)
                event = {"event": "screen", "name": screen_name, "status": "error", "error": str(e)}
            yield f"data: {json.dumps(event, default=str)}\n\n"

        response = {
            "success": True,
            "generated": results,
            "errors": errors,
            "total": len(screens_to_retry),
            "succeeded": len(results),
            "failed": len(errors),
            "project_id": project_id,
            "prompts": screens_to_retry,
        }
        _save_stitch_results(response)

        done = {"event": "done", "succeeded": len(results), "failed": len(errors), "total": len(screens_to_retry)}
        yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


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
    # Remove from errors if now successfully generated
    for name in data.get("generated", {}):
        prev_err.pop(name, None)
    existing["errors"] = prev_err
    existing["total"] = len(prev_gen) + len(prev_err)
    existing["succeeded"] = len(prev_gen)
    existing["failed"] = len(prev_err)
    existing["success"] = True

    # Merge prompts so we can retry failed ones later
    prev_prompts = existing.get("prompts", {})
    prev_prompts.update(data.get("prompts", {}))
    existing["prompts"] = prev_prompts

    results_path.write_text(json.dumps(existing, indent=2, default=str))


def _code_cache_dir() -> Path:
    d = OUTPUT_DIR / "stitch" / "code_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_cached_code(screen_id: str) -> str | None:
    path = _code_cache_dir() / f"{screen_id}.html"
    return path.read_text(encoding="utf-8") if path.exists() else None


def _save_cached_code(screen_id: str, html: str):
    (_code_cache_dir() / f"{screen_id}.html").write_text(html, encoding="utf-8")


def _delete_cached_code(screen_id: str):
    path = _code_cache_dir() / f"{screen_id}.html"
    if path.exists():
        path.unlink()


def _image_cache_dir() -> Path:
    d = OUTPUT_DIR / "stitch" / "image_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_cached_image(screen_id: str) -> bytes | None:
    path = _image_cache_dir() / f"{screen_id}.png"
    return path.read_bytes() if path.exists() else None


def _save_cached_image(screen_id: str, data: bytes):
    (_image_cache_dir() / f"{screen_id}.png").write_bytes(data)


def _delete_cached_image(screen_id: str):
    path = _image_cache_dir() / f"{screen_id}.png"
    if path.exists():
        path.unlink()


def _fetch_and_cache_image(screen_id: str, image_url: str) -> bytes | None:
    """Download screenshot image from a URL with retry on 429, cache on success."""
    import time

    import httpx

    for attempt in range(3):
        try:
            resp = httpx.get(image_url, timeout=30)
            resp.raise_for_status()
            _save_cached_image(screen_id, resp.content)
            return resp.content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception:
            return None
    return None


def _fetch_and_cache_code(screen_id: str, code_url: str) -> str | None:
    """Download HTML from a URL with retry on 429, cache on success."""
    import time

    import httpx

    for attempt in range(3):
        try:
            resp = httpx.get(code_url, timeout=30)
            resp.raise_for_status()
            _save_cached_code(screen_id, resp.text)
            return resp.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception:
            return None
    return None


def _cache_screen_assets(result: dict):
    """Immediately cache HTML code + screenshot image for a single screen result."""
    sc = result.get("structuredContent", {})
    for comp in sc.get("outputComponents", []):
        for s in comp.get("design", {}).get("screens", []):
            sid = s.get("id")
            if not sid:
                continue
            # Cache screenshot image first (visible in thumbnails)
            if not _get_cached_image(sid):
                img_entry = s.get("screenshot", {})
                img_url = img_entry.get("downloadUrl") if isinstance(img_entry, dict) else None
                if img_url:
                    _fetch_and_cache_image(sid, img_url)
            # Cache HTML code
            if not _get_cached_code(sid):
                entry = s.get("htmlCode", {})
                url = entry.get("downloadUrl") if isinstance(entry, dict) else None
                if url:
                    _fetch_and_cache_code(sid, url)


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

        # Invalidate cached code and images for edited screens
        for sid in body.screen_ids:
            _delete_cached_code(sid)
            _delete_cached_image(sid)

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

    # Remove cached code and image
    _delete_cached_code(screen_id)
    _delete_cached_image(screen_id)

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
    # 1. Serve from disk cache if available
    cached = _get_cached_code(screen_id)
    if cached:
        return {"success": True, "html": cached}

    # 2. Try direct download URL with retry
    code_url = _find_screen_url(screen_id, "htmlCode")
    if code_url:
        html = _fetch_and_cache_code(screen_id, code_url)
        if html:
            return {"success": True, "html": html}

    # 3. Fallback: use Stitch API
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        code = client.fetch_screen_code(project_id, screen_id)
        _save_cached_code(screen_id, code)
        return {"success": True, "html": code}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/stitch/screen/{project_id}/{screen_id}/preview")
def api_stitch_screen_preview(project_id: str, screen_id: str):
    """Serve the raw HTML for a Stitch screen (for iframe src)."""
    # 1. Serve from disk cache
    cached = _get_cached_code(screen_id)
    if cached:
        return Response(content=cached, media_type="text/html")

    # 2. Try direct download URL
    code_url = _find_screen_url(screen_id, "htmlCode")
    if code_url:
        html = _fetch_and_cache_code(screen_id, code_url)
        if html:
            return Response(content=html, media_type="text/html")

    # 3. Fallback: Stitch API
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        code = client.fetch_screen_code(project_id, screen_id)
        _save_cached_code(screen_id, code)
        return Response(content=code, media_type="text/html")
    except Exception:
        return Response(
            content="<html><body style='display:flex;align-items:center;justify-content:center;height:100%;margin:0;background:#1a1a2e;color:#666;font-family:sans-serif;'>Preview unavailable</body></html>",
            media_type="text/html",
        )


@app.get("/api/stitch/screen/{project_id}/{screen_id}/image")
def api_stitch_screen_image(project_id: str, screen_id: str):
    """Serve the screenshot image for a Stitch screen as raw PNG (usable in <img src>)."""

    # 1. Serve from disk cache if available
    cached = _get_cached_image(screen_id)
    if cached:
        return Response(content=cached, media_type="image/png")

    # 2. Try direct download URL with retry
    img_url = _find_screen_url(screen_id, "screenshot")
    if img_url:
        img_bytes = _fetch_and_cache_image(screen_id, img_url)
        if img_bytes:
            return Response(content=img_bytes, media_type="image/png")

    # 3. Fallback: use Stitch API
    try:
        from ai_agency.integrations.stitch import create_stitch_client

        client = create_stitch_client()
        image_bytes = client.fetch_screen_image(project_id, screen_id)
        _save_cached_image(screen_id, image_bytes)
        return Response(content=image_bytes, media_type="image/png")
    except Exception:
        return Response(status_code=404)


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
