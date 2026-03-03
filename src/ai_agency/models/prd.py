"""Pydantic models for the structured PRD (Product Requirements Document).

These models define the schema for AI-generated PRDs. They are designed to be:
1. Machine-readable (JSON serialization for downstream AI agents)
2. Human-readable (Markdown export for review)
3. LLM-optimized (clear field descriptions guide structured generation)
"""

from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class TechProficiency(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class Severity(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"


# --- Sub-models ---


class ProductOverview(BaseModel):
    """High-level product description and business context."""

    name: str = Field(description="Product or project name")
    tagline: str = Field(description="One-sentence product description")
    problem_statement: str = Field(description="The core problem this product solves")
    objectives: list[str] = Field(
        description="3-5 measurable business objectives",
        min_length=1,
    )
    target_market: str = Field(description="Primary target market or industry")
    competitive_landscape: str = Field(
        description="Brief overview of existing solutions and how this differs"
    )


class UserPersona(BaseModel):
    """A distinct user type who will interact with the product."""

    name: str = Field(description="Persona name (e.g., 'Operations Manager Maria')")
    role: str = Field(description="Job title or role")
    goals: list[str] = Field(description="What this persona wants to achieve with the product")
    pain_points: list[str] = Field(
        description="Current frustrations that this product addresses"
    )
    tech_proficiency: TechProficiency = Field(
        description="Technical skill level of this persona"
    )
    usage_frequency: str = Field(
        description="How often they'll use the product (daily, weekly, etc.)"
    )


class JourneyStep(BaseModel):
    """A single step in a user journey."""

    step_number: int = Field(description="Sequential step number")
    action: str = Field(description="What the user does")
    screen: str = Field(description="Screen/page where this happens")
    expected_result: str = Field(description="What happens after the action")


class UserJourney(BaseModel):
    """An end-to-end flow a user takes to accomplish a goal."""

    persona: str = Field(description="Which persona this journey belongs to")
    journey_name: str = Field(description="Name of this journey (e.g., 'First-time onboarding')")
    description: str = Field(description="Brief description of the journey's purpose")
    entry_point: str = Field(description="Where/how the user starts this journey")
    steps: list[JourneyStep] = Field(description="Ordered list of steps in the journey")
    success_criteria: str = Field(description="How we know the journey was completed successfully")


class UIRequirement(BaseModel):
    """UI-specific requirement for a feature."""

    screen_name: str = Field(description="Name of the screen/page")
    description: str = Field(description="What this screen should display and enable")
    key_elements: list[str] = Field(
        description="List of UI elements needed (buttons, forms, tables, charts, etc.)"
    )
    interactions: list[str] = Field(
        description="User interactions on this screen (click, drag, type, etc.)"
    )


class Feature(BaseModel):
    """A product feature with separated business logic and UI requirements."""

    name: str = Field(description="Feature name")
    description: str = Field(description="What this feature does and why it matters")
    priority: Priority = Field(description="Implementation priority")
    business_logic: list[str] = Field(
        description="Backend/logic rules (validation, calculations, workflows)"
    )
    ui_requirements: list[UIRequirement] = Field(
        description="UI screens and elements needed for this feature"
    )
    acceptance_criteria: list[str] = Field(
        description="Testable criteria that confirm this feature works correctly"
    )


class DataModelField(BaseModel):
    """A field within a data model."""

    name: str = Field(description="Field name (snake_case)")
    type: str = Field(description="Data type (string, integer, boolean, datetime, uuid, etc.)")
    required: bool = Field(description="Whether this field is required")
    description: str = Field(description="What this field represents")
    constraints: str | None = Field(
        default=None, description="Validation constraints (max_length, min_value, regex, etc.)"
    )


class DataModel(BaseModel):
    """A data entity/model with its schema definition."""

    name: str = Field(description="Model name (PascalCase)")
    description: str = Field(description="What this entity represents")
    fields: list[DataModelField] = Field(description="Fields in this model")
    relationships: list[str] = Field(
        default_factory=list,
        description="Relationships to other models (e.g., 'belongs_to User', 'has_many Orders')",
    )


class APIEndpoint(BaseModel):
    """A REST API endpoint definition."""

    method: HTTPMethod = Field(description="HTTP method")
    path: str = Field(description="URL path (e.g., '/api/v1/users/{id}')")
    description: str = Field(description="What this endpoint does")
    request_body: str | None = Field(
        default=None,
        description="Request body schema description (reference DataModel names)",
    )
    response_body: str = Field(
        description="Response body schema description (reference DataModel names)"
    )
    auth_required: bool = Field(default=True, description="Whether authentication is required")
    error_cases: list[str] = Field(
        default_factory=list,
        description="Possible error responses (e.g., '404: User not found')",
    )


class EdgeCase(BaseModel):
    """An edge case or boundary condition to handle."""

    scenario: str = Field(description="Description of the edge case scenario")
    expected_behavior: str = Field(description="How the system should handle this")
    severity: Severity = Field(description="Impact if not handled")


class SuccessMetric(BaseModel):
    """A measurable metric for tracking product success."""

    metric: str = Field(description="What to measure (e.g., 'User activation rate')")
    target: str = Field(description="Target value (e.g., '> 40% within first week')")
    measurement_method: str = Field(description="How to measure this metric")


class TechRecommendations(BaseModel):
    """Recommended technology stack."""

    frontend: str = Field(description="Frontend framework recommendation with rationale")
    backend: str = Field(description="Backend framework recommendation with rationale")
    database: str = Field(description="Database recommendation with rationale")
    deployment: str = Field(description="Deployment platform recommendation with rationale")
    additional: list[str] = Field(
        default_factory=list,
        description="Additional tools/services (auth, email, payments, etc.)",
    )


# --- Root PRD Model ---


class PRD(BaseModel):
    """Complete Product Requirements Document.

    This is the root model that contains all sections of a structured PRD.
    Designed for both human review (Markdown export) and machine consumption
    (JSON for downstream AI coding and design agents).
    """

    product_overview: ProductOverview = Field(
        description="High-level product description, objectives, and market context"
    )
    user_personas: list[UserPersona] = Field(
        description="Distinct user types who will use this product", min_length=1
    )
    user_journeys: list[UserJourney] = Field(
        description="End-to-end user flows for key tasks", min_length=1
    )
    features: list[Feature] = Field(
        description="Product features with separated business logic and UI requirements",
        min_length=1,
    )
    data_models: list[DataModel] = Field(
        description="Data entities and their schemas", min_length=1
    )
    api_endpoints: list[APIEndpoint] = Field(
        description="REST API endpoint definitions", min_length=1
    )
    edge_cases: list[EdgeCase] = Field(
        description="Edge cases and boundary conditions to handle"
    )
    success_metrics: list[SuccessMetric] = Field(
        description="Measurable metrics for tracking product success", min_length=1
    )
    constraints: list[str] = Field(
        description="Technical, business, or regulatory constraints"
    )
    tech_recommendations: TechRecommendations = Field(
        description="Recommended technology stack with rationale"
    )

    def to_markdown(self) -> str:
        """Export the PRD as a formatted Markdown document."""
        lines: list[str] = []
        ov = self.product_overview

        lines.append(f"# PRD: {ov.name}")
        lines.append(f"*{ov.tagline}*\n")

        # Product Overview
        lines.append("## 1. Product Overview")
        lines.append(f"**Problem Statement:** {ov.problem_statement}\n")
        lines.append(f"**Target Market:** {ov.target_market}\n")
        lines.append(f"**Competitive Landscape:** {ov.competitive_landscape}\n")
        lines.append("### Objectives")
        for obj in ov.objectives:
            lines.append(f"- {obj}")
        lines.append("")

        # User Personas
        lines.append("## 2. User Personas")
        for persona in self.user_personas:
            lines.append(f"### {persona.name} ({persona.role})")
            lines.append(f"- **Tech Proficiency:** {persona.tech_proficiency.value}")
            lines.append(f"- **Usage:** {persona.usage_frequency}")
            lines.append("- **Goals:**")
            for g in persona.goals:
                lines.append(f"  - {g}")
            lines.append("- **Pain Points:**")
            for p in persona.pain_points:
                lines.append(f"  - {p}")
            lines.append("")

        # User Journeys
        lines.append("## 3. User Journeys")
        for journey in self.user_journeys:
            lines.append(f"### {journey.journey_name}")
            lines.append(f"**Persona:** {journey.persona}")
            lines.append(f"**Entry Point:** {journey.entry_point}")
            lines.append(f"**Description:** {journey.description}\n")
            lines.append("| Step | Action | Screen | Expected Result |")
            lines.append("|------|--------|--------|-----------------|")
            for step in journey.steps:
                lines.append(
                    f"| {step.step_number} | {step.action} "
                    f"| {step.screen} | {step.expected_result} |"
                )
            lines.append(f"\n**Success Criteria:** {journey.success_criteria}\n")

        # Features
        lines.append("## 4. Features")
        for feat in self.features:
            lines.append(f"### {feat.name} [{feat.priority.value.upper()}]")
            lines.append(f"{feat.description}\n")
            lines.append("**Business Logic:**")
            for bl in feat.business_logic:
                lines.append(f"- {bl}")
            lines.append("\n**UI Requirements:**")
            for ui in feat.ui_requirements:
                lines.append(f"- **{ui.screen_name}:** {ui.description}")
                lines.append(f"  - Elements: {', '.join(ui.key_elements)}")
                lines.append(f"  - Interactions: {', '.join(ui.interactions)}")
            lines.append("\n**Acceptance Criteria:**")
            for ac in feat.acceptance_criteria:
                lines.append(f"- [ ] {ac}")
            lines.append("")

        # Data Models
        lines.append("## 5. Data Models")
        for dm in self.data_models:
            lines.append(f"### {dm.name}")
            lines.append(f"{dm.description}\n")
            lines.append("| Field | Type | Required | Description | Constraints |")
            lines.append("|-------|------|----------|-------------|-------------|")
            for f in dm.fields:
                constraints = f.constraints or "-"
                req = "Yes" if f.required else "No"
                lines.append(f"| {f.name} | {f.type} | {req} | {f.description} | {constraints} |")
            if dm.relationships:
                lines.append(f"\n**Relationships:** {', '.join(dm.relationships)}")
            lines.append("")

        # API Endpoints
        lines.append("## 6. API Endpoints")
        for ep in self.api_endpoints:
            auth = "Auth required" if ep.auth_required else "Public"
            lines.append(f"### `{ep.method.value} {ep.path}` [{auth}]")
            lines.append(f"{ep.description}\n")
            if ep.request_body:
                lines.append(f"- **Request:** {ep.request_body}")
            lines.append(f"- **Response:** {ep.response_body}")
            if ep.error_cases:
                lines.append("- **Errors:**")
                for err in ep.error_cases:
                    lines.append(f"  - {err}")
            lines.append("")

        # Edge Cases
        lines.append("## 7. Edge Cases")
        for ec in self.edge_cases:
            lines.append(f"- **[{ec.severity.value.upper()}]** {ec.scenario}")
            lines.append(f"  - Expected: {ec.expected_behavior}")
        lines.append("")

        # Success Metrics
        lines.append("## 8. Success Metrics")
        lines.append("| Metric | Target | Measurement |")
        lines.append("|--------|--------|-------------|")
        for sm in self.success_metrics:
            lines.append(f"| {sm.metric} | {sm.target} | {sm.measurement_method} |")
        lines.append("")

        # Constraints
        lines.append("## 9. Constraints")
        for c in self.constraints:
            lines.append(f"- {c}")
        lines.append("")

        # Tech Recommendations
        tr = self.tech_recommendations
        lines.append("## 10. Tech Recommendations")
        lines.append(f"- **Frontend:** {tr.frontend}")
        lines.append(f"- **Backend:** {tr.backend}")
        lines.append(f"- **Database:** {tr.database}")
        lines.append(f"- **Deployment:** {tr.deployment}")
        if tr.additional:
            lines.append("- **Additional:**")
            for a in tr.additional:
                lines.append(f"  - {a}")

        return "\n".join(lines)
