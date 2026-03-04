"""Pydantic models for Product Roadmap generation.

Provides phased roadmap with milestones, timelines, dependencies,
and resource allocation.
"""

from pydantic import BaseModel, Field


class RoadmapMilestone(BaseModel):
    """A key milestone within a phase."""

    name: str = Field(description="Milestone name")
    description: str = Field(description="What this milestone delivers")
    deliverables: list[str] = Field(description="Specific deliverables", min_length=1)
    success_criteria: str = Field(description="How to verify the milestone is reached")


class RoadmapFeature(BaseModel):
    """A feature scheduled within a roadmap phase."""

    name: str = Field(description="Feature name (should match PRD feature names when applicable)")
    description: str = Field(description="What this feature delivers to users")
    effort: str = Field(description="'small' (days), 'medium' (weeks), or 'large' (months)")
    priority: str = Field(description="'critical', 'high', 'medium', or 'low'")
    dependencies: list[str] = Field(
        default_factory=list,
        description="Other features or milestones this depends on"
    )


class RoadmapPhase(BaseModel):
    """A phase in the product roadmap."""

    phase_number: int = Field(description="Phase number (1, 2, 3, etc.)")
    name: str = Field(description="Phase name (e.g., 'MVP', 'Growth', 'Scale')")
    description: str = Field(description="What this phase achieves")
    duration: str = Field(description="Expected duration (e.g., '6-8 weeks')")
    start: str = Field(description="Relative start (e.g., 'Month 1', 'After Phase 1')")
    features: list[RoadmapFeature] = Field(
        description="Features included in this phase", min_length=1
    )
    milestones: list[RoadmapMilestone] = Field(
        description="Key milestones in this phase", min_length=1
    )
    team_focus: str = Field(description="Primary team focus during this phase")
    risks: list[str] = Field(
        default_factory=list,
        description="Key risks for this phase"
    )


class ResourceAllocation(BaseModel):
    """Resource allocation across roadmap phases."""

    role: str = Field(description="Role (e.g., 'Frontend Engineer', 'Product Manager')")
    count: int = Field(description="Number of people in this role", ge=1)
    phases: list[str] = Field(description="Which phases they are allocated to")


class DependencyChain(BaseModel):
    """A critical dependency chain across the roadmap."""

    chain_name: str = Field(description="Name of the dependency chain")
    steps: list[str] = Field(
        description="Ordered steps in the dependency chain", min_length=2
    )
    critical_path: bool = Field(
        description="Whether this chain is on the critical path"
    )
    risk_if_delayed: str = Field(
        description="Impact if any step in this chain is delayed"
    )


class ProductRoadmap(BaseModel):
    """Complete Product Roadmap.

    A phased roadmap with milestones, features, dependencies,
    resource allocation, and risk mitigation.
    """

    executive_summary: str = Field(
        description="2-3 sentence roadmap overview"
    )
    vision: str = Field(
        description="Product vision — what does success look like in 12-18 months"
    )
    total_duration: str = Field(
        description="Total estimated roadmap duration (e.g., '9-12 months')"
    )
    phases: list[RoadmapPhase] = Field(
        description="Ordered phases of the roadmap", min_length=2
    )
    resource_allocation: list[ResourceAllocation] = Field(
        description="Team resource allocation across phases", min_length=2
    )
    dependency_chains: list[DependencyChain] = Field(
        description="Critical dependency chains across phases", min_length=1
    )
    launch_criteria: list[str] = Field(
        description="Criteria that must be met before public launch", min_length=3
    )
    post_launch: list[str] = Field(
        description="Key activities planned for post-launch", min_length=2
    )

    def to_markdown(self) -> str:
        """Export as formatted Markdown."""
        lines: list[str] = []
        lines.append("# Product Roadmap")
        lines.append(f"\n{self.executive_summary}\n")
        lines.append(f"**Vision:** {self.vision}\n")
        lines.append(f"**Total Duration:** {self.total_duration}\n")

        for phase in self.phases:
            lines.append(f"## Phase {phase.phase_number}: {phase.name}")
            lines.append(f"*{phase.description}*\n")
            lines.append(f"- **Duration:** {phase.duration}")
            lines.append(f"- **Start:** {phase.start}")
            lines.append(f"- **Team Focus:** {phase.team_focus}")

            lines.append("\n### Features")
            lines.append("| Feature | Effort | Priority | Dependencies |")
            lines.append("|---------|--------|----------|--------------|")
            for f in phase.features:
                deps = ", ".join(f.dependencies) if f.dependencies else "None"
                lines.append(
                    f"| {f.name} | {f.effort} | {f.priority} | {deps} |"
                )

            lines.append("\n### Milestones")
            for m in phase.milestones:
                lines.append(f"- **{m.name}:** {m.description}")
                lines.append(f"  - Deliverables: {', '.join(m.deliverables)}")
                lines.append(f"  - Success Criteria: {m.success_criteria}")

            if phase.risks:
                lines.append("\n### Risks")
                for r in phase.risks:
                    lines.append(f"- {r}")
            lines.append("")

        lines.append("## Resource Allocation")
        lines.append("| Role | Count | Phases |")
        lines.append("|------|-------|--------|")
        for ra in self.resource_allocation:
            lines.append(f"| {ra.role} | {ra.count} | {', '.join(ra.phases)} |")
        lines.append("")

        lines.append("## Dependency Chains")
        for dc in self.dependency_chains:
            critical = " [CRITICAL PATH]" if dc.critical_path else ""
            lines.append(f"### {dc.chain_name}{critical}")
            lines.append(" -> ".join(dc.steps))
            lines.append(f"- **Risk if delayed:** {dc.risk_if_delayed}")
            lines.append("")

        lines.append("## Launch Criteria")
        for lc in self.launch_criteria:
            lines.append(f"- [ ] {lc}")
        lines.append("")

        lines.append("## Post-Launch Plan")
        for pl in self.post_launch:
            lines.append(f"- {pl}")

        return "\n".join(lines)
