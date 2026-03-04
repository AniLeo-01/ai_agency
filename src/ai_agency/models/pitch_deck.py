"""Pydantic models for Pitch Deck generation.

Generates structured slide-by-slide content for a startup pitch deck,
following the proven pitch deck formula.
"""

from pydantic import BaseModel, Field


class PitchSlide(BaseModel):
    """A single slide in the pitch deck."""

    slide_number: int = Field(description="Slide order number")
    title: str = Field(description="Slide title")
    slide_type: str = Field(
        description="Slide type: 'title', 'problem', 'solution', 'market', "
        "'product', 'business_model', 'traction', 'competition', "
        "'team', 'financials', 'ask', 'vision'"
    )
    headline: str = Field(description="One powerful sentence that captures the slide's message")
    bullet_points: list[str] = Field(
        description="3-5 bullet points with key content for this slide", min_length=1
    )
    speaker_notes: str = Field(
        description="What the presenter should say for this slide (2-4 sentences)"
    )
    visual_suggestion: str = Field(
        description="Suggested visual/graphic for the slide (chart type, image, diagram)"
    )


class FinancialHighlight(BaseModel):
    """A key financial metric for the pitch."""

    metric: str = Field(description="Metric name (e.g., 'ARR', 'CAC', 'LTV')")
    value: str = Field(description="Metric value or target")
    context: str = Field(description="Why this metric matters for investors")


class FundingAsk(BaseModel):
    """Funding request details."""

    amount: str = Field(description="Funding amount requested (e.g., '$2M Seed')")
    use_of_funds: list[str] = Field(
        description="How the funds will be allocated", min_length=2
    )
    milestones_to_reach: list[str] = Field(
        description="What milestones the funding will enable", min_length=2
    )
    runway: str = Field(description="Expected runway with this funding (e.g., '18 months')")


class PitchDeck(BaseModel):
    """Complete Pitch Deck.

    Follows the proven pitch deck structure:
    Title -> Problem -> Solution -> Market -> Product -> Business Model ->
    Traction -> Competition -> Team -> Financials -> Ask -> Vision
    """

    company_name: str = Field(description="Company or product name")
    tagline: str = Field(description="One-line company description")
    elevator_pitch: str = Field(
        description="30-second elevator pitch (3-4 sentences)"
    )
    slides: list[PitchSlide] = Field(
        description="Ordered slides for the pitch deck", min_length=8
    )
    financial_highlights: list[FinancialHighlight] = Field(
        description="Key financial metrics and projections", min_length=3
    )
    funding_ask: FundingAsk = Field(
        description="Funding request details"
    )
    appendix_topics: list[str] = Field(
        description="Topics to prepare for appendix/Q&A", min_length=3
    )

    def to_markdown(self) -> str:
        """Export as formatted Markdown."""
        lines: list[str] = []
        lines.append(f"# Pitch Deck: {self.company_name}")
        lines.append(f"*{self.tagline}*\n")

        lines.append("## Elevator Pitch")
        lines.append(f"{self.elevator_pitch}\n")

        lines.append("---\n")

        for slide in self.slides:
            lines.append(f"## Slide {slide.slide_number}: {slide.title}")
            lines.append(f"**Type:** {slide.slide_type}")
            lines.append(f"**Headline:** *{slide.headline}*\n")
            for bp in slide.bullet_points:
                lines.append(f"- {bp}")
            lines.append(f"\n**Visual:** {slide.visual_suggestion}")
            lines.append(f"\n**Speaker Notes:** {slide.speaker_notes}")
            lines.append("\n---\n")

        lines.append("## Financial Highlights")
        lines.append("| Metric | Value | Context |")
        lines.append("|--------|-------|---------|")
        for fh in self.financial_highlights:
            lines.append(f"| {fh.metric} | {fh.value} | {fh.context} |")
        lines.append("")

        lines.append("## Funding Ask")
        lines.append(f"**Amount:** {self.funding_ask.amount}")
        lines.append(f"**Runway:** {self.funding_ask.runway}\n")
        lines.append("**Use of Funds:**")
        for uof in self.funding_ask.use_of_funds:
            lines.append(f"- {uof}")
        lines.append("\n**Milestones:**")
        for m in self.funding_ask.milestones_to_reach:
            lines.append(f"- {m}")
        lines.append("")

        lines.append("## Appendix / Q&A Prep")
        for topic in self.appendix_topics:
            lines.append(f"- {topic}")

        return "\n".join(lines)
