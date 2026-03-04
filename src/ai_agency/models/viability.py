"""Pydantic models for Product Viability Assessment.

Evaluates technical feasibility, resource requirements, risk factors,
and overall viability scoring given current technology landscape.
"""

from pydantic import BaseModel, Field


class TechFeasibility(BaseModel):
    """Assessment of technical feasibility for a specific aspect."""

    area: str = Field(description="Technical area (e.g., 'Real-time sync', 'ML pipeline')")
    feasibility: str = Field(description="'high', 'medium', or 'low'")
    current_tech: str = Field(description="Available technology/frameworks to implement this")
    complexity: str = Field(description="'low', 'medium', 'high', or 'very_high'")
    notes: str = Field(description="Key considerations, gotchas, or dependencies")


class ResourceEstimate(BaseModel):
    """Resource requirement estimate for a work area."""

    area: str = Field(description="Work area (e.g., 'Frontend', 'Backend', 'DevOps')")
    team_size: str = Field(description="Recommended team size (e.g., '2-3 engineers')")
    duration: str = Field(description="Estimated duration (e.g., '3-4 months')")
    skills_required: list[str] = Field(description="Key skills needed")
    cost_estimate: str = Field(description="Rough cost estimate range (e.g., '$150K-$200K')")


class RiskFactor(BaseModel):
    """A risk that could impact product viability."""

    risk: str = Field(description="Risk description")
    category: str = Field(
        description="'technical', 'market', 'financial', 'regulatory', or 'operational'"
    )
    probability: str = Field(description="'high', 'medium', or 'low'")
    impact: str = Field(description="'critical', 'high', 'medium', or 'low'")
    mitigation: str = Field(description="How to mitigate or reduce this risk")


class ViabilityScore(BaseModel):
    """Viability score for a specific dimension."""

    dimension: str = Field(
        description="Scoring dimension (e.g., 'Technical Feasibility', 'Market Readiness')"
    )
    score: int = Field(description="Score from 1 to 10", ge=1, le=10)
    weight: int = Field(description="Weight factor from 1 to 5 (importance)", ge=1, le=5)
    rationale: str = Field(description="Why this score was given")


class BuildVsBuy(BaseModel):
    """Build vs. buy recommendation for a component."""

    component: str = Field(description="Component name")
    recommendation: str = Field(description="'build', 'buy', or 'open_source'")
    rationale: str = Field(description="Why this recommendation")
    options: list[str] = Field(description="Specific product/framework options if buy/open_source")


class MilestoneValidation(BaseModel):
    """A validation milestone to de-risk the product."""

    milestone: str = Field(description="Milestone name")
    description: str = Field(description="What needs to be validated")
    success_criteria: str = Field(description="How to know if validation passed")
    timeline: str = Field(description="Estimated time to reach this milestone")


class ProductViability(BaseModel):
    """Complete Product Viability Assessment.

    Evaluates whether the product can be built successfully with current
    technology, team, and budget constraints.
    """

    executive_summary: str = Field(
        description="2-3 sentence viability verdict"
    )
    overall_viability: str = Field(
        description="'highly_viable', 'viable', 'conditionally_viable', or 'not_viable'"
    )
    tech_feasibility: list[TechFeasibility] = Field(
        description="Technical feasibility assessment by area", min_length=3
    )
    resource_estimates: list[ResourceEstimate] = Field(
        description="Resource requirements by work area", min_length=2
    )
    total_budget_range: str = Field(
        description="Total estimated budget range (e.g., '$400K-$600K for MVP')"
    )
    total_timeline: str = Field(
        description="Total estimated timeline (e.g., '4-6 months to MVP')"
    )
    risks: list[RiskFactor] = Field(
        description="Risk factors that could impact viability", min_length=3
    )
    viability_scores: list[ViabilityScore] = Field(
        description="Viability scores across dimensions", min_length=4
    )
    build_vs_buy: list[BuildVsBuy] = Field(
        description="Build vs. buy recommendations for key components", min_length=2
    )
    validation_milestones: list[MilestoneValidation] = Field(
        description="Key milestones to validate before full investment", min_length=2
    )
    recommendations: list[str] = Field(
        description="3-5 actionable recommendations", min_length=3
    )

    def to_markdown(self) -> str:
        """Export as formatted Markdown."""
        lines: list[str] = []
        lines.append("# Product Viability Assessment")
        lines.append(f"\n**Verdict: {self.overall_viability.replace('_', ' ').title()}**\n")
        lines.append(f"{self.executive_summary}\n")

        lines.append("## Technical Feasibility")
        lines.append("| Area | Feasibility | Complexity | Technology | Notes |")
        lines.append("|------|------------|------------|------------|-------|")
        for tf in self.tech_feasibility:
            lines.append(
                f"| {tf.area} | {tf.feasibility} | {tf.complexity} "
                f"| {tf.current_tech} | {tf.notes} |"
            )
        lines.append("")

        lines.append("## Resource Estimates")
        lines.append(f"**Total Budget:** {self.total_budget_range}")
        lines.append(f"**Total Timeline:** {self.total_timeline}\n")
        for re in self.resource_estimates:
            lines.append(f"### {re.area}")
            lines.append(f"- **Team:** {re.team_size}")
            lines.append(f"- **Duration:** {re.duration}")
            lines.append(f"- **Cost:** {re.cost_estimate}")
            lines.append(f"- **Skills:** {', '.join(re.skills_required)}")
            lines.append("")

        lines.append("## Risk Assessment")
        lines.append("| Risk | Category | Probability | Impact | Mitigation |")
        lines.append("|------|----------|------------|--------|------------|")
        for r in self.risks:
            lines.append(
                f"| {r.risk} | {r.category} | {r.probability} "
                f"| {r.impact} | {r.mitigation} |"
            )
        lines.append("")

        lines.append("## Viability Scores")
        lines.append("| Dimension | Score | Weight | Rationale |")
        lines.append("|-----------|-------|--------|-----------|")
        for vs in self.viability_scores:
            lines.append(f"| {vs.dimension} | {vs.score}/10 | x{vs.weight} | {vs.rationale} |")
        total = sum(vs.score * vs.weight for vs in self.viability_scores)
        max_total = sum(10 * vs.weight for vs in self.viability_scores)
        lines.append(f"\n**Weighted Score: {total}/{max_total}**\n")

        lines.append("## Build vs. Buy")
        for bb in self.build_vs_buy:
            lines.append(f"- **{bb.component}** — {bb.recommendation.upper()}")
            lines.append(f"  - {bb.rationale}")
            if bb.options:
                lines.append(f"  - Options: {', '.join(bb.options)}")
        lines.append("")

        lines.append("## Validation Milestones")
        for vm in self.validation_milestones:
            lines.append(f"### {vm.milestone}")
            lines.append(f"{vm.description}")
            lines.append(f"- **Success Criteria:** {vm.success_criteria}")
            lines.append(f"- **Timeline:** {vm.timeline}\n")

        lines.append("## Recommendations")
        for rec in self.recommendations:
            lines.append(f"- {rec}")

        return "\n".join(lines)
