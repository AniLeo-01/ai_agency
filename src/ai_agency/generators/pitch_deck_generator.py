"""Pitch Deck Generator: creates slide-by-slide pitch deck content."""

import json
from pathlib import Path

from ai_agency.models.pitch_deck import PitchDeck
from ai_agency.providers import create_provider
from ai_agency.templates.pitch_deck_system import PITCH_DECK_SYSTEM_PROMPT


def generate_pitch_deck(requirements: str) -> PitchDeck:
    """Generate a Pitch Deck from raw requirements or a PRD summary.

    Args:
        requirements: Product description, requirements text, or PRD-derived summary.

    Returns:
        A fully populated PitchDeck model.
    """
    provider = create_provider()
    return provider.generate_structured(
        prompt=requirements,
        response_model=PitchDeck,
        system_prompt=PITCH_DECK_SYSTEM_PROMPT,
    )


def save_pitch_deck(deck: PitchDeck, output_dir: str | Path) -> tuple[Path, Path]:
    """Save the Pitch Deck as both JSON and Markdown.

    Returns:
        Tuple of (json_path, markdown_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "pitch_deck.json"
    json_path.write_text(
        json.dumps(deck.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    md_path = out / "pitch_deck.md"
    md_path.write_text(deck.to_markdown(), encoding="utf-8")

    return json_path, md_path
