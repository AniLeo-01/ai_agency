"""Tests for PRD and Stitch prompt generators (non-LLM logic)."""

import json
import tempfile
from pathlib import Path

from ai_agency.generators.stitch_prompt import (
    _collect_screens,
    generate_all_stitch_prompts,
    generate_stitch_prompt,
    save_stitch_prompts,
)
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
    """Create a sample PRD with multiple screens for testing."""
    return PRD(
        product_overview=ProductOverview(
            name="TaskFlow",
            tagline="Simple task management for small teams",
            problem_statement="Teams need a lightweight tracker",
            objectives=["Launch MVP"],
            target_market="Startups",
            competitive_landscape="Trello exists but is complex",
        ),
        user_personas=[
            UserPersona(
                name="Steve",
                role="CTO",
                goals=["Track tasks"],
                pain_points=["Too complex"],
                tech_proficiency="advanced",
                usage_frequency="Daily",
            ),
        ],
        user_journeys=[
            UserJourney(
                persona="Steve",
                journey_name="Create task",
                description="Create and assign a task",
                entry_point="Dashboard",
                steps=[
                    JourneyStep(
                        step_number=1,
                        action="Click New Task",
                        screen="Dashboard",
                        expected_result="Modal opens",
                    ),
                    JourneyStep(
                        step_number=2,
                        action="Fill form",
                        screen="Task Form",
                        expected_result="Fields populated",
                    ),
                ],
                success_criteria="Task created",
            ),
        ],
        features=[
            Feature(
                name="Task Board",
                description="Kanban board for Task management",
                priority=Priority.critical,
                business_logic=["Status transitions"],
                ui_requirements=[
                    UIRequirement(
                        screen_name="Dashboard",
                        description="Main kanban board",
                        key_elements=["Task cards", "Column headers", "Add button"],
                        interactions=["Drag and drop", "Click to open"],
                    ),
                    UIRequirement(
                        screen_name="Task Form",
                        description="Create/edit task form",
                        key_elements=["Title input", "Description textarea", "Assignee dropdown"],
                        interactions=["Type", "Select", "Submit"],
                    ),
                ],
                acceptance_criteria=["Board shows tasks"],
            ),
            Feature(
                name="User Settings",
                description="User profile and notification settings",
                priority=Priority.medium,
                business_logic=["Validate email"],
                ui_requirements=[
                    UIRequirement(
                        screen_name="Settings Page",
                        description="User settings panel",
                        key_elements=["Profile form", "Notification toggles"],
                        interactions=["Edit profile", "Toggle notifications"],
                    ),
                ],
                acceptance_criteria=["Settings save correctly"],
            ),
        ],
        data_models=[
            DataModel(
                name="Task",
                description="A task entity",
                fields=[
                    DataModelField(
                        name="id", type="uuid", required=True, description="ID",
                    ),
                    DataModelField(
                        name="title", type="string", required=True, description="Title",
                    ),
                ],
            ),
        ],
        api_endpoints=[
            APIEndpoint(
                method=HTTPMethod.POST,
                path="/api/v1/tasks",
                description="Create task",
                response_body="Task",
                auth_required=True,
            ),
        ],
        edge_cases=[
            EdgeCase(
                scenario="Empty board",
                expected_behavior="Show empty state",
                severity=Severity.minor,
            ),
        ],
        success_metrics=[
            SuccessMetric(
                metric="Tasks created",
                target="> 5/week",
                measurement_method="Count API calls",
            ),
        ],
        constraints=["Mobile support"],
        tech_recommendations=TechRecommendations(
            frontend="Next.js",
            backend="FastAPI",
            database="PostgreSQL",
            deployment="Cloud Run",
        ),
    )


class TestStitchPromptGenerator:
    """Tests for the Stitch prompt generation logic."""

    def test_collect_screens_finds_all(self):
        """Should find all unique screens from features."""
        prd = _make_sample_prd()
        screens = _collect_screens(prd)
        assert "Dashboard" in screens
        assert "Task Form" in screens
        assert "Settings Page" in screens
        assert len(screens) == 3

    def test_collect_screens_merges_elements(self):
        """Screens referenced by multiple features should merge elements."""
        prd = _make_sample_prd()
        screens = _collect_screens(prd)
        dashboard = screens["Dashboard"]
        assert "Task cards" in dashboard["elements"]
        assert "Column headers" in dashboard["elements"]

    def test_collect_screens_includes_journey_context(self):
        """Journey steps should be attached to matching screens."""
        prd = _make_sample_prd()
        screens = _collect_screens(prd)
        assert len(screens["Dashboard"]["journeys"]) >= 1
        assert "Create task" in screens["Dashboard"]["journeys"][0]

    def test_generate_stitch_prompt_contains_sections(self):
        """Generated prompt should contain all expected sections."""
        prompt = generate_stitch_prompt(
            screen_name="Dashboard",
            screen_info={
                "description": "Main board view",
                "elements": ["Task cards", "Columns"],
                "interactions": ["Drag and drop"],
                "journeys": ["Create task: Step 1 - Click New Task"],
                "features": ["Task Board"],
                "data_context": ["Task (id, title)"],
            },
            product_name="TaskFlow",
            product_tagline="Simple task management",
        )
        assert "TaskFlow" in prompt
        assert "Dashboard" in prompt
        assert "Task cards" in prompt
        assert "Drag and drop" in prompt
        assert "Design Guidelines" in prompt

    def test_generate_all_stitch_prompts(self):
        """Should generate one prompt per screen."""
        prd = _make_sample_prd()
        prompts = generate_all_stitch_prompts(prd)
        assert len(prompts) == 3
        assert "Dashboard" in prompts
        assert "Task Form" in prompts
        assert "Settings Page" in prompts

    def test_save_stitch_prompts_creates_files(self):
        """Should save prompt files and a manifest."""
        prompts = {
            "Dashboard": "Dashboard prompt content",
            "Task Form": "Task form prompt content",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            saved = save_stitch_prompts(prompts, tmpdir)
            assert len(saved) == 3  # 2 prompts + 1 manifest

            # Check prompt files exist
            assert (Path(tmpdir) / "dashboard.txt").exists()
            assert (Path(tmpdir) / "task_form.txt").exists()

            # Check manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            assert manifest_path.exists()
            manifest = json.loads(manifest_path.read_text())
            assert "Dashboard" in manifest["screens"]
            assert "Task Form" in manifest["screens"]


class TestPRDGeneratorIO:
    """Tests for PRD save/load logic (no LLM calls)."""

    def test_save_and_load_prd(self):
        """PRD should save to JSON and load back correctly."""
        from ai_agency.generators.prd_generator import load_prd, save_prd

        prd = _make_sample_prd()
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path, md_path = save_prd(prd, tmpdir)

            assert json_path.exists()
            assert md_path.exists()

            loaded = load_prd(json_path)
            assert loaded.product_overview.name == "TaskFlow"
            assert len(loaded.features) == 2

    def test_load_prd_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        import pytest

        from ai_agency.generators.prd_generator import load_prd

        with pytest.raises(FileNotFoundError):
            load_prd("/nonexistent/path/prd.json")
