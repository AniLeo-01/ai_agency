"""Pydantic models for Market Analysis.

Provides structured market sizing (TAM/SAM/SOM), trend analysis,
opportunity scoring, and data suitable for chart rendering.
"""

from pydantic import BaseModel, Field


class MarketSegment(BaseModel):
    """A segment within the target market."""

    name: str = Field(description="Segment name (e.g., 'Enterprise SaaS', 'SMB Retail')")
    size_usd: str = Field(description="Estimated segment size in USD (e.g., '$4.2B')")
    growth_rate: str = Field(description="Annual growth rate (e.g., '12.5%')")
    relevance: str = Field(description="Why this segment matters for the product")


class MarketTrend(BaseModel):
    """A macro or micro trend affecting the market."""

    trend: str = Field(description="Name of the trend")
    description: str = Field(description="What is happening and why")
    impact: str = Field(description="How this trend impacts the product opportunity")
    direction: str = Field(description="'growing', 'stable', or 'declining'")
    timeframe: str = Field(description="Short-term (1yr), mid-term (2-3yr), or long-term (5yr+)")


class MarketSizing(BaseModel):
    """TAM / SAM / SOM market sizing."""

    tam_value: str = Field(description="Total Addressable Market value (e.g., '$50B')")
    tam_description: str = Field(description="How the TAM was estimated")
    sam_value: str = Field(description="Serviceable Addressable Market value (e.g., '$12B')")
    sam_description: str = Field(description="How the SAM was scoped from TAM")
    som_value: str = Field(description="Serviceable Obtainable Market value (e.g., '$800M')")
    som_description: str = Field(description="Realistic capture based on go-to-market strategy")


class OpportunityScore(BaseModel):
    """Quantified opportunity assessment."""

    category: str = Field(description="Scoring category (e.g., 'Market Size', 'Growth Rate')")
    score: int = Field(description="Score from 1 to 10", ge=1, le=10)
    rationale: str = Field(description="Why this score was given")


class MarketBarrier(BaseModel):
    """A barrier to entry or challenge in the market."""

    barrier: str = Field(description="Name of the barrier")
    severity: str = Field(description="'high', 'medium', or 'low'")
    mitigation: str = Field(description="How the product can overcome this barrier")


class YearlyProjection(BaseModel):
    """Revenue or growth projection for a single year."""

    year: str = Field(description="Year label (e.g., 'Year 1', '2026')")
    revenue: str = Field(description="Projected revenue (e.g., '$500K')")
    users: str = Field(description="Projected user count (e.g., '5,000')")
    market_share: str = Field(description="Projected market share (e.g., '0.1%')")


class MarketAnalysis(BaseModel):
    """Complete Market Analysis report.

    Provides structured data for market sizing, trends, opportunities,
    barriers, and projections — with chart-ready numerical data.
    """

    executive_summary: str = Field(
        description="2-3 sentence summary of the market opportunity"
    )
    market_sizing: MarketSizing = Field(
        description="TAM / SAM / SOM breakdown"
    )
    market_segments: list[MarketSegment] = Field(
        description="Key market segments with size and growth", min_length=2
    )
    trends: list[MarketTrend] = Field(
        description="Major market trends affecting the opportunity", min_length=3
    )
    opportunity_scores: list[OpportunityScore] = Field(
        description="Quantified opportunity assessment across dimensions", min_length=4
    )
    barriers: list[MarketBarrier] = Field(
        description="Barriers to entry and how to overcome them", min_length=2
    )
    projections: list[YearlyProjection] = Field(
        description="5-year revenue and growth projections", min_length=3
    )
    key_insights: list[str] = Field(
        description="3-5 actionable insights from the market analysis", min_length=3
    )
    methodology: str = Field(
        description="Brief description of analysis methodology and data sources assumed"
    )

    def to_markdown(self) -> str:
        """Export as formatted Markdown."""
        lines: list[str] = []
        lines.append("# Market Analysis")
        lines.append(f"\n{self.executive_summary}\n")

        lines.append("## Market Sizing")
        lines.append("| Metric | Value | Description |")
        lines.append("|--------|-------|-------------|")
        lines.append(
            f"| TAM | {self.market_sizing.tam_value} | {self.market_sizing.tam_description} |"
        )
        lines.append(
            f"| SAM | {self.market_sizing.sam_value} | {self.market_sizing.sam_description} |"
        )
        lines.append(
            f"| SOM | {self.market_sizing.som_value} | {self.market_sizing.som_description} |"
        )
        lines.append("")

        lines.append("## Market Segments")
        lines.append("| Segment | Size | Growth Rate | Relevance |")
        lines.append("|---------|------|-------------|-----------|")
        for seg in self.market_segments:
            lines.append(
                f"| {seg.name} | {seg.size_usd} | {seg.growth_rate} | {seg.relevance} |"
            )
        lines.append("")

        lines.append("## Market Trends")
        for t in self.trends:
            lines.append(f"### {t.trend} [{t.direction}]")
            lines.append(f"{t.description}")
            lines.append(f"- **Impact:** {t.impact}")
            lines.append(f"- **Timeframe:** {t.timeframe}\n")

        lines.append("## Opportunity Assessment")
        lines.append("| Category | Score (1-10) | Rationale |")
        lines.append("|----------|-------------|-----------|")
        for o in self.opportunity_scores:
            lines.append(f"| {o.category} | {o.score}/10 | {o.rationale} |")
        lines.append("")

        lines.append("## Barriers to Entry")
        for b in self.barriers:
            lines.append(f"- **[{b.severity.upper()}] {b.barrier}**")
            lines.append(f"  - Mitigation: {b.mitigation}")
        lines.append("")

        lines.append("## 5-Year Projections")
        lines.append("| Year | Revenue | Users | Market Share |")
        lines.append("|------|---------|-------|-------------|")
        for p in self.projections:
            lines.append(f"| {p.year} | {p.revenue} | {p.users} | {p.market_share} |")
        lines.append("")

        lines.append("## Key Insights")
        for insight in self.key_insights:
            lines.append(f"- {insight}")
        lines.append("")

        lines.append(f"## Methodology\n{self.methodology}")

        return "\n".join(lines)
