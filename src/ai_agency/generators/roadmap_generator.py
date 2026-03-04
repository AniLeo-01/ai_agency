"""Product Roadmap Generator: creates phased product roadmap with milestones."""

import json
from pathlib import Path

from ai_agency.models.roadmap import ProductRoadmap
from ai_agency.providers import create_provider
from ai_agency.templates.roadmap_system import ROADMAP_SYSTEM_PROMPT


def generate_roadmap(requirements: str) -> ProductRoadmap:
    """Generate a Product Roadmap from raw requirements or a PRD summary.

    Args:
        requirements: Product description, requirements text, or PRD-derived summary.

    Returns:
        A fully populated ProductRoadmap model.
    """
    provider = create_provider()
    return provider.generate_structured(
        prompt=requirements,
        response_model=ProductRoadmap,
        system_prompt=ROADMAP_SYSTEM_PROMPT,
    )


def save_roadmap(roadmap: ProductRoadmap, output_dir: str | Path) -> tuple[Path, Path]:
    """Save the Roadmap as both JSON and Markdown.

    Returns:
        Tuple of (json_path, markdown_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "roadmap.json"
    json_path.write_text(
        json.dumps(roadmap.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    md_path = out / "roadmap.md"
    md_path.write_text(roadmap.to_markdown(), encoding="utf-8")

    return json_path, md_path
