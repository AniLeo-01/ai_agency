"""Pydantic models for Competitor Analysis.

Provides structured competitor profiling, feature comparison matrices,
SWOT analysis, and positioning strategy.
"""

from pydantic import BaseModel, Field


class CompetitorProfile(BaseModel):
    """Detailed profile of a single competitor."""

    name: str = Field(description="Competitor company/product name")
    website: str = Field(description="Competitor website URL or 'N/A'")
    description: str = Field(description="What the competitor does in 1-2 sentences")
    target_market: str = Field(description="Who they primarily serve")
    pricing_model: str = Field(
        description="How they charge (freemium, subscription, per-seat, etc.)"
    )
    estimated_revenue: str = Field(description="Estimated annual revenue or funding stage")
    strengths: list[str] = Field(description="Key competitive strengths", min_length=2)
    weaknesses: list[str] = Field(description="Key competitive weaknesses", min_length=2)
    market_share: str = Field(description="Estimated market share or relative position")


class FeatureComparison(BaseModel):
    """Feature-by-feature comparison across competitors."""

    feature: str = Field(description="Feature name")
    our_product: str = Field(
        description="Our product's capability: 'planned', 'basic', 'advanced', or 'superior'"
    )
    competitors: dict[str, str] = Field(
        description="Map of competitor name to their capability: 'none', 'basic', 'advanced'"
    )


class SWOTItem(BaseModel):
    """A single item in a SWOT analysis."""

    item: str = Field(description="The SWOT item description")
    impact: str = Field(description="'high', 'medium', or 'low'")
    detail: str = Field(description="Additional context or explanation")


class SWOT(BaseModel):
    """SWOT analysis for the product against the competitive landscape."""

    strengths: list[SWOTItem] = Field(description="Internal strengths", min_length=2)
    weaknesses: list[SWOTItem] = Field(description="Internal weaknesses", min_length=2)
    opportunities: list[SWOTItem] = Field(description="External opportunities", min_length=2)
    threats: list[SWOTItem] = Field(description="External threats", min_length=2)


class PositioningStrategy(BaseModel):
    """How to position the product in the competitive landscape."""

    value_proposition: str = Field(
        description="Core differentiator in one sentence"
    )
    positioning_statement: str = Field(
        description="For [target], [product] is the [category] that [benefit] "
        "unlike [alternatives]"
    )
    differentiation_axes: list[str] = Field(
        description="2-4 key axes on which we differentiate", min_length=2
    )
    go_to_market_angle: str = Field(
        description="How positioning translates to marketing and sales strategy"
    )


class CompetitorAnalysis(BaseModel):
    """Complete Competitor Analysis report.

    Profiles competitors, compares features, performs SWOT analysis,
    and recommends positioning strategy.
    """

    executive_summary: str = Field(
        description="2-3 sentence overview of the competitive landscape"
    )
    competitors: list[CompetitorProfile] = Field(
        description="Detailed profiles of key competitors", min_length=2
    )
    feature_matrix: list[FeatureComparison] = Field(
        description="Feature-by-feature comparison table", min_length=4
    )
    swot: SWOT = Field(
        description="SWOT analysis against the competitive landscape"
    )
    positioning: PositioningStrategy = Field(
        description="Recommended positioning strategy"
    )
    competitive_moat: list[str] = Field(
        description="Defensibility factors that create a competitive moat", min_length=2
    )
    key_takeaways: list[str] = Field(
        description="3-5 actionable takeaways from the competitive analysis", min_length=3
    )

    def to_markdown(self) -> str:
        """Export as formatted Markdown."""
        lines: list[str] = []
        lines.append("# Competitor Analysis")
        lines.append(f"\n{self.executive_summary}\n")

        lines.append("## Competitor Profiles")
        for c in self.competitors:
            lines.append(f"### {c.name}")
            lines.append(f"*{c.description}*\n")
            lines.append(f"- **Target Market:** {c.target_market}")
            lines.append(f"- **Pricing:** {c.pricing_model}")
            lines.append(f"- **Revenue/Stage:** {c.estimated_revenue}")
            lines.append(f"- **Market Share:** {c.market_share}")
            lines.append("- **Strengths:**")
            for s in c.strengths:
                lines.append(f"  - {s}")
            lines.append("- **Weaknesses:**")
            for w in c.weaknesses:
                lines.append(f"  - {w}")
            lines.append("")

        lines.append("## Feature Comparison Matrix")
        comp_names = []
        if self.competitors:
            comp_names = [c.name for c in self.competitors]
        header = "| Feature | Our Product | " + " | ".join(comp_names) + " |"
        sep = "|---------|-------------|" + "|".join(["----------"] * len(comp_names)) + "|"
        lines.append(header)
        lines.append(sep)
        for fm in self.feature_matrix:
            row = f"| {fm.feature} | {fm.our_product}"
            for name in comp_names:
                row += f" | {fm.competitors.get(name, 'N/A')}"
            row += " |"
            lines.append(row)
        lines.append("")

        lines.append("## SWOT Analysis")
        lines.append("### Strengths")
        for s in self.swot.strengths:
            lines.append(f"- **[{s.impact.upper()}]** {s.item} — {s.detail}")
        lines.append("\n### Weaknesses")
        for w in self.swot.weaknesses:
            lines.append(f"- **[{w.impact.upper()}]** {w.item} — {w.detail}")
        lines.append("\n### Opportunities")
        for o in self.swot.opportunities:
            lines.append(f"- **[{o.impact.upper()}]** {o.item} — {o.detail}")
        lines.append("\n### Threats")
        for t in self.swot.threats:
            lines.append(f"- **[{t.impact.upper()}]** {t.item} — {t.detail}")
        lines.append("")

        lines.append("## Positioning Strategy")
        lines.append(f"**Value Proposition:** {self.positioning.value_proposition}\n")
        lines.append(f"**Positioning Statement:** {self.positioning.positioning_statement}\n")
        lines.append("**Differentiation Axes:**")
        for axis in self.positioning.differentiation_axes:
            lines.append(f"- {axis}")
        lines.append(f"\n**Go-to-Market Angle:** {self.positioning.go_to_market_angle}\n")

        lines.append("## Competitive Moat")
        for m in self.competitive_moat:
            lines.append(f"- {m}")
        lines.append("")

        lines.append("## Key Takeaways")
        for t in self.key_takeaways:
            lines.append(f"- {t}")

        return "\n".join(lines)
