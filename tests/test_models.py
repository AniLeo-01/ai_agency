"""Tests for PRD Pydantic models."""


from ai_agency.models.prd import (
    PRD,
    APIEndpoint,
    DataModel,
    DataModelField,
    EdgeCase,
    Feature,
    HTTPMethod,
    JourneyStep,
    Priority,
    ProductOverview,
    Severity,
    SuccessMetric,
    TechRecommendations,
    UIRequirement,
    UserJourney,
    UserPersona,
)


def _make_sample_prd() -> PRD:
    """Create a minimal but complete PRD for testing."""
    return PRD(
        product_overview=ProductOverview(
            name="TaskFlow",
            tagline="Simple task management for small teams",
            problem_statement="Small teams lack a lightweight task tracker",
            objectives=["Launch MVP in 4 weeks", "Acquire 100 beta users"],
            target_market="Small tech startups (2-10 people)",
            competitive_landscape="Trello and Asana exist but are too complex for tiny teams",
        ),
        user_personas=[
            UserPersona(
                name="Startup Steve",
                role="Founder / CTO",
                goals=["Track team progress", "Assign tasks quickly"],
                pain_points=[
                    "Current tools are overengineered",
                    "Too many clicks to create a task",
                ],
                tech_proficiency="advanced",
                usage_frequency="Daily",
            ),
        ],
        user_journeys=[
            UserJourney(
                persona="Startup Steve",
                journey_name="Create and assign a task",
                description="User creates a new task and assigns it to a team member",
                entry_point="Dashboard",
                steps=[
                    JourneyStep(
                        step_number=1,
                        action="Click 'New Task' button",
                        screen="Dashboard",
                        expected_result="Task creation modal opens",
                    ),
                    JourneyStep(
                        step_number=2,
                        action="Fill in title, description, assignee",
                        screen="Task Creation Modal",
                        expected_result="Form fields are populated",
                    ),
                    JourneyStep(
                        step_number=3,
                        action="Click 'Create'",
                        screen="Task Creation Modal",
                        expected_result="Task appears in the board",
                    ),
                ],
                success_criteria="Task is visible on the board with correct assignee",
            ),
        ],
        features=[
            Feature(
                name="Task Board",
                description="Kanban-style board for viewing and managing tasks",
                priority=Priority.critical,
                business_logic=[
                    "Tasks have statuses: todo, in_progress, done",
                    "Only assignee or creator can change status",
                ],
                ui_requirements=[
                    UIRequirement(
                        screen_name="Dashboard",
                        description="Main board view with columns for each status",
                        key_elements=["Column headers", "Task cards", "New Task button"],
                        interactions=[
                            "Drag-and-drop between columns",
                            "Click card to open details",
                        ],
                    ),
                ],
                acceptance_criteria=[
                    "Tasks display title and assignee avatar",
                    "Drag-and-drop updates task status in real-time",
                ],
            ),
        ],
        data_models=[
            DataModel(
                name="Task",
                description="A unit of work assigned to a team member",
                fields=[
                    DataModelField(
                        name="id", type="uuid", required=True,
                        description="Unique identifier",
                    ),
                    DataModelField(
                        name="title", type="string", required=True,
                        description="Task title", constraints="max_length=200",
                    ),
                    DataModelField(
                        name="status", type="string", required=True,
                        description="Current status", constraints="enum: todo, in_progress, done",
                    ),
                ],
                relationships=["belongs_to User (as assignee)", "belongs_to User (as creator)"],
            ),
        ],
        api_endpoints=[
            APIEndpoint(
                method=HTTPMethod.POST,
                path="/api/v1/tasks",
                description="Create a new task",
                request_body="Task (title, description, assignee_id)",
                response_body="Task object with generated id",
                auth_required=True,
                error_cases=["400: Missing required fields", "404: Assignee not found"],
            ),
        ],
        edge_cases=[
            EdgeCase(
                scenario="User drags task to same column",
                expected_behavior="No status change, no API call",
                severity=Severity.minor,
            ),
        ],
        success_metrics=[
            SuccessMetric(
                metric="Tasks created per user per week",
                target="> 5",
                measurement_method="Count POST /api/v1/tasks per user",
            ),
        ],
        constraints=["Must work on mobile browsers", "No paid third-party services for MVP"],
        tech_recommendations=TechRecommendations(
            frontend="Next.js with Tailwind CSS — fast prototyping, strong ecosystem",
            backend="FastAPI — Python-native, great for AI integration",
            database="PostgreSQL — reliable, supports JSON fields",
            deployment="Google Cloud Run — serverless, auto-scaling",
            additional=["Clerk for auth", "Resend for email"],
        ),
    )


class TestPRDModels:
    """Tests for PRD model serialization and validation."""

    def test_prd_roundtrip_json(self):
        """PRD should serialize to JSON and deserialize back identically."""
        prd = _make_sample_prd()
        json_str = prd.model_dump_json()
        restored = PRD.model_validate_json(json_str)
        assert restored.product_overview.name == "TaskFlow"
        assert len(restored.features) == 1
        assert len(restored.api_endpoints) == 1

    def test_prd_dict_roundtrip(self):
        """PRD should convert to dict and back."""
        prd = _make_sample_prd()
        data = prd.model_dump()
        restored = PRD.model_validate(data)
        assert restored.product_overview.tagline == prd.product_overview.tagline

    def test_prd_to_markdown(self):
        """Markdown export should contain key sections."""
        prd = _make_sample_prd()
        md = prd.to_markdown()
        assert "# PRD: TaskFlow" in md
        assert "## 1. Product Overview" in md
        assert "## 2. User Personas" in md
        assert "## 3. User Journeys" in md
        assert "## 4. Features" in md
        assert "## 5. Data Models" in md
        assert "## 6. API Endpoints" in md
        assert "## 7. Edge Cases" in md
        assert "## 8. Success Metrics" in md
        assert "Startup Steve" in md
        assert "Dashboard" in md

    def test_prd_json_schema(self):
        """PRD should generate a valid JSON schema."""
        schema = PRD.model_json_schema()
        assert "properties" in schema
        assert "product_overview" in schema["properties"]

    def test_feature_priority_enum(self):
        """Priority enum should work correctly."""
        feat = Feature(
            name="Test",
            description="Test feature",
            priority="high",
            business_logic=["rule1"],
            ui_requirements=[],
            acceptance_criteria=["works"],
        )
        assert feat.priority == Priority.high
        assert feat.priority.value == "high"

    def test_data_model_optional_constraints(self):
        """DataModelField constraints should be optional."""
        field = DataModelField(
            name="email",
            type="string",
            required=True,
            description="User email",
        )
        assert field.constraints is None

        field_with = DataModelField(
            name="email",
            type="string",
            required=True,
            description="User email",
            constraints="format: email",
        )
        assert field_with.constraints == "format: email"
