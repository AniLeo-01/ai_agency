"""Stitch Prompt Generator: extracts UI sections from a PRD and generates
Google Stitch-ready prompts for each screen."""

import json
from pathlib import Path

from ai_agency.models.prd import PRD


def _collect_screens(prd: PRD) -> dict[str, dict]:
    """Collect all unique screens from the PRD with their context.

    Returns a dict mapping screen_name -> {description, elements, interactions,
    journeys, features}.
    """
    screens: dict[str, dict] = {}

    # Collect from features' UI requirements
    for feature in prd.features:
        for ui_req in feature.ui_requirements:
            name = ui_req.screen_name
            if name not in screens:
                screens[name] = {
                    "description": ui_req.description,
                    "elements": list(ui_req.key_elements),
                    "interactions": list(ui_req.interactions),
                    "journeys": [],
                    "features": [],
                    "data_context": [],
                }
            else:
                # Merge elements and interactions from multiple features
                screens[name]["elements"] = list(
                    dict.fromkeys(screens[name]["elements"] + list(ui_req.key_elements))
                )
                screens[name]["interactions"] = list(
                    dict.fromkeys(screens[name]["interactions"] + list(ui_req.interactions))
                )
            screens[name]["features"].append(feature.name)

    # Enrich with journey context
    for journey in prd.user_journeys:
        for step in journey.steps:
            if step.screen in screens:
                journey_info = f"{journey.journey_name}: Step {step.step_number} - {step.action}"
                screens[step.screen]["journeys"].append(journey_info)

    # Enrich with data model context
    for feature in prd.features:
        for ui_req in feature.ui_requirements:
            if ui_req.screen_name in screens:
                # Find related data models by looking at feature business logic
                for dm in prd.data_models:
                    if dm.name.lower() in feature.description.lower():
                        field_summary = ", ".join(f.name for f in dm.fields[:8])
                        info = f"{dm.name} ({field_summary})"
                        if info not in screens[ui_req.screen_name]["data_context"]:
                            screens[ui_req.screen_name]["data_context"].append(info)

    return screens


def generate_stitch_prompt(
    screen_name: str,
    screen_info: dict,
    product_name: str,
    product_tagline: str,
) -> str:
    """Generate a single Stitch-optimized prompt for one screen."""
    lines = [
        f"Design a modern, clean UI screen for \"{product_name}\" — {product_tagline}.",
        "",
        f"## Screen: {screen_name}",
        f"{screen_info['description']}",
        "",
    ]

    if screen_info["elements"]:
        lines.append("## Key UI Elements")
        for el in screen_info["elements"]:
            lines.append(f"- {el}")
        lines.append("")

    if screen_info["interactions"]:
        lines.append("## User Interactions")
        for interaction in screen_info["interactions"]:
            lines.append(f"- {interaction}")
        lines.append("")

    if screen_info["journeys"]:
        lines.append("## User Flow Context")
        for j in screen_info["journeys"]:
            lines.append(f"- {j}")
        lines.append("")

    if screen_info["data_context"]:
        lines.append("## Data Displayed")
        for d in screen_info["data_context"]:
            lines.append(f"- {d}")
        lines.append("")

    lines.extend([
        "## Design Guidelines",
        "- Use a clean, modern design with consistent spacing",
        "- Responsive layout that works on desktop and mobile",
        "- Use a professional color scheme with clear visual hierarchy",
        "- Include proper states: loading, empty, error, populated",
        "- Follow accessibility best practices (contrast, labels, focus states)",
    ])

    return "\n".join(lines)


def generate_all_stitch_prompts(prd: PRD) -> dict[str, str]:
    """Generate Stitch prompts for all screens in a PRD.

    Returns:
        Dict mapping screen_name -> stitch_prompt_text.
    """
    screens = _collect_screens(prd)
    prompts = {}
    product_name = prd.product_overview.name
    product_tagline = prd.product_overview.tagline

    for screen_name, screen_info in screens.items():
        prompts[screen_name] = generate_stitch_prompt(
            screen_name=screen_name,
            screen_info=screen_info,
            product_name=product_name,
            product_tagline=product_tagline,
        )

    return prompts


def save_stitch_prompts(prompts: dict[str, str], output_dir: str | Path) -> list[Path]:
    """Save Stitch prompts to individual files.

    Returns:
        List of paths to the saved prompt files.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []

    # Save individual screen prompts
    for screen_name, prompt_text in prompts.items():
        safe_name = screen_name.lower().replace(" ", "_").replace("/", "_")
        file_path = out / f"{safe_name}.txt"
        file_path.write_text(prompt_text, encoding="utf-8")
        saved.append(file_path)

    # Save an index/manifest file
    manifest = {
        "screens": list(prompts.keys()),
        "prompt_files": {
            name: f"{name.lower().replace(' ', '_').replace('/', '_')}.txt"
            for name in prompts
        },
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    saved.append(manifest_path)

    return saved
