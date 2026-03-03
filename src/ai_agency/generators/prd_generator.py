"""PRD Generator: transforms raw customer requirements into a structured PRD."""

import json
from pathlib import Path

from ai_agency.models.prd import PRD
from ai_agency.providers import create_provider
from ai_agency.templates.prd_system import PRD_SYSTEM_PROMPT


def generate_prd(requirements: str) -> PRD:
    """Generate a structured PRD from raw customer requirements.

    Args:
        requirements: Raw text containing customer requirements, meeting notes,
                      problem statements, or feature descriptions.

    Returns:
        A fully populated PRD Pydantic model.
    """
    provider = create_provider()
    return provider.generate_structured(
        prompt=requirements,
        response_model=PRD,
        system_prompt=PRD_SYSTEM_PROMPT,
    )


def generate_prd_from_file(input_path: str | Path) -> PRD:
    """Generate a PRD from a requirements file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Requirements file not found: {path}")
    requirements = path.read_text(encoding="utf-8")
    return generate_prd(requirements)


def save_prd(prd: PRD, output_dir: str | Path) -> tuple[Path, Path]:
    """Save the PRD as both JSON and Markdown.

    Returns:
        Tuple of (json_path, markdown_path).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "prd.json"
    json_path.write_text(
        json.dumps(prd.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    md_path = out / "prd.md"
    md_path.write_text(prd.to_markdown(), encoding="utf-8")

    return json_path, md_path


def load_prd(json_path: str | Path) -> PRD:
    """Load a PRD from a JSON file."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"PRD file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return PRD.model_validate(data)
