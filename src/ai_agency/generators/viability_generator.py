"""Product Viability Generator: assesses technical feasibility and business viability."""

import json
from pathlib import Path

from ai_agency.models.viability import ProductViability
from ai_agency.providers import create_provider
from ai_agency.templates.viability_system import VIABILITY_SYSTEM_PROMPT


def generate_viability(requirements: str) -> ProductViability:
    """Generate a Product Viability Assessment from raw requirements or a PRD summary.

    Args:
        requirements: Product description, requirements text, or PRD-derived summary.

    Returns:
        A fully populated ProductViability model.
    """
    provider = create_provider()
    return provider.generate_structured(
        prompt=requirements,
        response_model=ProductViability,
        system_prompt=VIABILITY_SYSTEM_PROMPT,
    )


def save_viability(viability: ProductViability, output_dir: str | Path) -> tuple[Path, Path]:
    """Save the Viability Assessment as both JSON and Markdown.

    Returns:
        Tuple of (json_path, markdown_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "viability.json"
    json_path.write_text(
        json.dumps(viability.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    md_path = out / "viability.md"
    md_path.write_text(viability.to_markdown(), encoding="utf-8")

    return json_path, md_path
