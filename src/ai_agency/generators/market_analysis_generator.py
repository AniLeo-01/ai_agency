"""Market Analysis Generator: produces structured market analysis from product info."""

import json
from pathlib import Path

from ai_agency.models.market_analysis import MarketAnalysis
from ai_agency.providers import create_provider
from ai_agency.templates.market_analysis_system import MARKET_ANALYSIS_SYSTEM_PROMPT


def generate_market_analysis(requirements: str) -> MarketAnalysis:
    """Generate a Market Analysis from raw product requirements or a PRD summary.

    Args:
        requirements: Product description, requirements text, or PRD-derived summary.

    Returns:
        A fully populated MarketAnalysis model.
    """
    provider = create_provider()
    return provider.generate_structured(
        prompt=requirements,
        response_model=MarketAnalysis,
        system_prompt=MARKET_ANALYSIS_SYSTEM_PROMPT,
    )


def save_market_analysis(analysis: MarketAnalysis, output_dir: str | Path) -> tuple[Path, Path]:
    """Save the Market Analysis as both JSON and Markdown.

    Returns:
        Tuple of (json_path, markdown_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "market_analysis.json"
    json_path.write_text(
        json.dumps(analysis.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    md_path = out / "market_analysis.md"
    md_path.write_text(analysis.to_markdown(), encoding="utf-8")

    return json_path, md_path
