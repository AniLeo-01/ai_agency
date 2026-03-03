"""CLI interface for the AI Agency toolkit."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
@click.version_option(package_name="ai-agency")
def cli():
    """AI Agency — PRD generation and UI design pipeline."""
    pass


# --- PRD commands ---


@cli.group()
def prd():
    """Generate and manage Product Requirements Documents."""
    pass


@prd.command("generate")
@click.option(
    "--input", "-i", "input_path",
    type=click.Path(exists=True),
    help="Path to a requirements text file.",
)
@click.option(
    "--text", "-t",
    type=str,
    help="Raw requirements text (alternative to --input).",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output",
    help="Output directory for PRD files.",
)
def prd_generate(input_path: str | None, text: str | None, output: str):
    """Generate a structured PRD from customer requirements."""
    from ai_agency.generators.prd_generator import generate_prd, generate_prd_from_file, save_prd

    if not input_path and not text:
        console.print("[bold red]Error:[/] Provide either --input FILE or --text 'requirements'.")
        sys.exit(1)

    console.print(Panel("Generating PRD...", style="bold blue"))

    try:
        if input_path:
            console.print(f"Reading requirements from: {input_path}")
            prd_result = generate_prd_from_file(input_path)
        else:
            prd_result = generate_prd(text)

        json_path, md_path = save_prd(prd_result, output)

        console.print(Panel.fit(
            f"[bold green]PRD generated successfully![/]\n\n"
            f"  JSON: {json_path}\n"
            f"  Markdown: {md_path}\n\n"
            f"  Product: {prd_result.product_overview.name}\n"
            f"  Features: {len(prd_result.features)}\n"
            f"  API Endpoints: {len(prd_result.api_endpoints)}\n"
            f"  Data Models: {len(prd_result.data_models)}",
            title="PRD Output",
        ))

    except Exception as e:
        console.print(f"[bold red]Error generating PRD:[/] {e}")
        sys.exit(1)


# --- Design commands ---


@cli.group()
def design():
    """Generate UI design prompts from a PRD."""
    pass


@design.command("generate")
@click.option(
    "--prd", "-p", "prd_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to a PRD JSON file (from 'prd generate').",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output/designs",
    help="Output directory for Stitch prompt files.",
)
def design_generate(prd_path: str, output: str):
    """Generate Google Stitch-ready prompts from a PRD."""
    from ai_agency.generators.prd_generator import load_prd
    from ai_agency.generators.stitch_prompt import generate_all_stitch_prompts, save_stitch_prompts

    console.print(Panel("Generating Stitch design prompts...", style="bold blue"))

    try:
        prd_data = load_prd(prd_path)
        prompts = generate_all_stitch_prompts(prd_data)
        saved_files = save_stitch_prompts(prompts, output)

        console.print(Panel.fit(
            f"[bold green]Stitch prompts generated![/]\n\n"
            f"  Screens: {len(prompts)}\n"
            f"  Files saved: {len(saved_files)}\n"
            f"  Output: {output}/\n\n"
            f"  Screens:\n" + "\n".join(f"    - {name}" for name in prompts.keys()) +
            "\n\n  [dim]Copy each .txt file content into stitch.withgoogle.com[/]",
            title="Design Prompts",
        ))

    except Exception as e:
        console.print(f"[bold red]Error generating design prompts:[/] {e}")
        sys.exit(1)


# --- Pipeline command ---


@cli.command("pipeline")
@click.option(
    "--input", "-i", "input_path",
    type=click.Path(exists=True),
    help="Path to a requirements text file.",
)
@click.option(
    "--text", "-t",
    type=str,
    help="Raw requirements text.",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output",
    help="Output directory for all generated files.",
)
def pipeline(input_path: str | None, text: str | None, output: str):
    """Full pipeline: requirements -> PRD -> Stitch design prompts."""
    from ai_agency.generators.prd_generator import generate_prd, generate_prd_from_file, save_prd
    from ai_agency.generators.stitch_prompt import generate_all_stitch_prompts, save_stitch_prompts

    if not input_path and not text:
        console.print("[bold red]Error:[/] Provide either --input FILE or --text 'requirements'.")
        sys.exit(1)

    out = Path(output)

    # Step 1: Generate PRD
    console.print(Panel("Step 1/2: Generating PRD...", style="bold blue"))
    try:
        if input_path:
            console.print(f"Reading requirements from: {input_path}")
            prd_result = generate_prd_from_file(input_path)
        else:
            prd_result = generate_prd(text)

        json_path, md_path = save_prd(prd_result, out)
        console.print(f"  [green]PRD saved:[/] {json_path}, {md_path}")

    except Exception as e:
        console.print(f"[bold red]Error generating PRD:[/] {e}")
        sys.exit(1)

    # Step 2: Generate Stitch prompts
    console.print(Panel("Step 2/2: Generating Stitch design prompts...", style="bold blue"))
    try:
        prompts = generate_all_stitch_prompts(prd_result)
        design_dir = out / "designs"
        save_stitch_prompts(prompts, design_dir)

        console.print(Panel.fit(
            f"[bold green]Pipeline complete![/]\n\n"
            f"  Product: {prd_result.product_overview.name}\n"
            f"  Features: {len(prd_result.features)}\n"
            f"  API Endpoints: {len(prd_result.api_endpoints)}\n"
            f"  Data Models: {len(prd_result.data_models)}\n"
            f"  Design Screens: {len(prompts)}\n\n"
            f"  Output directory: {out}/\n"
            f"    prd.json      — Machine-readable PRD\n"
            f"    prd.md        — Human-readable PRD\n"
            f"    designs/      — Stitch prompt files ({len(prompts)} screens)",
            title="Pipeline Complete",
        ))

    except Exception as e:
        console.print(f"[bold red]Error generating design prompts:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
