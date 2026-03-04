"""Competitor Analysis Generator: profiles competitors and produces strategic analysis."""

import json
from pathlib import Path

from ai_agency.models.competitor_analysis import CompetitorAnalysis
from ai_agency.providers import create_provider
from ai_agency.templates.competitor_analysis_system import COMPETITOR_ANALYSIS_SYSTEM_PROMPT


def generate_competitor_analysis(requirements: str) -> CompetitorAnalysis:
    """Generate a Competitor Analysis from raw product requirements or a PRD summary.

    Args:
        requirements: Product description, requirements text, or PRD-derived summary.

    Returns:
        A fully populated CompetitorAnalysis model.
    """
    provider = create_provider()
    return provider.generate_structured(
        prompt=requirements,
        response_model=CompetitorAnalysis,
        system_prompt=COMPETITOR_ANALYSIS_SYSTEM_PROMPT,
    )


def save_competitor_analysis(
    analysis: CompetitorAnalysis, output_dir: str | Path
) -> tuple[Path, Path]:
    """Save the Competitor Analysis as both JSON and Markdown.

    Returns:
        Tuple of (json_path, markdown_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "competitor_analysis.json"
    json_path.write_text(
        json.dumps(analysis.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    md_path = out / "competitor_analysis.md"
    md_path.write_text(analysis.to_markdown(), encoding="utf-8")

    return json_path, md_path
