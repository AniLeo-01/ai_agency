"""Tests for the new AI product tool models:
Market Analysis, Competitor Analysis, Product Viability, Roadmap, and Pitch Deck.
"""

from ai_agency.models.competitor_analysis import (
    SWOT,
    CompetitorAnalysis,
    CompetitorProfile,
    FeatureComparison,
    PositioningStrategy,
    SWOTItem,
)
from ai_agency.models.market_analysis import (
    MarketAnalysis,
    MarketBarrier,
    MarketSegment,
    MarketSizing,
    MarketTrend,
    OpportunityScore,
    YearlyProjection,
)
from ai_agency.models.pitch_deck import (
    FinancialHighlight,
    FundingAsk,
    PitchDeck,
    PitchSlide,
)
from ai_agency.models.roadmap import (
    DependencyChain,
    ProductRoadmap,
    ResourceAllocation,
    RoadmapFeature,
    RoadmapMilestone,
    RoadmapPhase,
)
from ai_agency.models.viability import (
    BuildVsBuy,
    MilestoneValidation,
    ProductViability,
    ResourceEstimate,
    RiskFactor,
    TechFeasibility,
    ViabilityScore,
)

# --- Sample builders ---


def _make_market_analysis() -> MarketAnalysis:
    return MarketAnalysis(
        executive_summary="Large and growing market with significant opportunity.",
        market_sizing=MarketSizing(
            tam_value="$50B",
            tam_description="Global project management software market",
            sam_value="$12B",
            sam_description="SMB segment in North America and Europe",
            som_value="$800M",
            som_description="Realistic capture over 5 years",
        ),
        market_segments=[
            MarketSegment(
                name="SMB SaaS",
                size_usd="$8B",
                growth_rate="14%",
                relevance="Primary target segment",
            ),
            MarketSegment(
                name="Enterprise",
                size_usd="$20B",
                growth_rate="8%",
                relevance="Future expansion opportunity",
            ),
        ],
        trends=[
            MarketTrend(
                trend="AI-powered tools",
                description="AI integration in productivity tools",
                impact="Creates new product categories",
                direction="growing",
                timeframe="Short-term (1yr)",
            ),
            MarketTrend(
                trend="Remote work",
                description="Sustained remote work adoption",
                impact="Increases demand for collaboration tools",
                direction="stable",
                timeframe="Mid-term (2-3yr)",
            ),
            MarketTrend(
                trend="Consolidation",
                description="Tool fatigue driving all-in-one solutions",
                impact="Bundled platforms gaining share",
                direction="growing",
                timeframe="Mid-term (2-3yr)",
            ),
        ],
        opportunity_scores=[
            OpportunityScore(category="Market Size", score=8, rationale="Large TAM"),
            OpportunityScore(category="Growth Rate", score=7, rationale="Above average"),
            OpportunityScore(category="Competition", score=5, rationale="Crowded"),
            OpportunityScore(category="Timing", score=9, rationale="AI wave"),
        ],
        barriers=[
            MarketBarrier(
                barrier="High competition",
                severity="high",
                mitigation="Differentiate with AI features",
            ),
            MarketBarrier(
                barrier="Customer acquisition cost",
                severity="medium",
                mitigation="Product-led growth strategy",
            ),
        ],
        projections=[
            YearlyProjection(year="Year 1", revenue="$500K", users="5,000", market_share="0.01%"),
            YearlyProjection(year="Year 2", revenue="$2M", users="20,000", market_share="0.04%"),
            YearlyProjection(year="Year 3", revenue="$8M", users="75,000", market_share="0.15%"),
        ],
        key_insights=["AI features are the key differentiator", "SMBs underserved", "PLG is best"],
        methodology="Top-down estimation from industry reports combined with bottom-up analysis.",
    )


def _make_competitor_analysis() -> CompetitorAnalysis:
    return CompetitorAnalysis(
        executive_summary="Competitive but fragmented market with opportunity for differentiation.",
        competitors=[
            CompetitorProfile(
                name="Asana",
                website="asana.com",
                description="Enterprise project management platform",
                target_market="Mid-market and enterprise teams",
                pricing_model="Per-seat subscription, freemium tier",
                estimated_revenue="$500M ARR",
                strengths=["Strong brand", "Feature-rich"],
                weaknesses=["Complex for small teams", "Expensive at scale"],
                market_share="15%",
            ),
            CompetitorProfile(
                name="Trello",
                website="trello.com",
                description="Visual kanban board tool",
                target_market="Small teams and individuals",
                pricing_model="Freemium with paid tiers",
                estimated_revenue="$100M ARR",
                strengths=["Simple UI", "Large user base"],
                weaknesses=["Limited for complex projects", "Stagnant innovation"],
                market_share="8%",
            ),
        ],
        feature_matrix=[
            FeatureComparison(
                feature="AI Task Suggestions",
                our_product="planned",
                competitors={"Asana": "basic", "Trello": "none"},
            ),
            FeatureComparison(
                feature="Kanban Board",
                our_product="advanced",
                competitors={"Asana": "advanced", "Trello": "advanced"},
            ),
            FeatureComparison(
                feature="Time Tracking",
                our_product="planned",
                competitors={"Asana": "advanced", "Trello": "basic"},
            ),
            FeatureComparison(
                feature="Mobile App",
                our_product="basic",
                competitors={"Asana": "advanced", "Trello": "advanced"},
            ),
        ],
        swot=SWOT(
            strengths=[
                SWOTItem(item="AI-first approach", impact="high", detail="Unique differentiator"),
                SWOTItem(item="Modern tech stack", impact="medium", detail="Faster iteration"),
            ],
            weaknesses=[
                SWOTItem(item="No brand recognition", impact="high", detail="New entrant"),
                SWOTItem(item="Small team", impact="medium", detail="Limited capacity"),
            ],
            opportunities=[
                SWOTItem(item="AI wave", impact="high", detail="Market timing advantage"),
                SWOTItem(item="SMB underserved", impact="medium", detail="Gap in market"),
            ],
            threats=[
                SWOTItem(item="Big player copies", impact="high", detail="Asana adds AI"),
                SWOTItem(item="Economic downturn", impact="medium", detail="Budget cuts"),
            ],
        ),
        positioning=PositioningStrategy(
            value_proposition="AI-powered task management that thinks ahead",
            positioning_statement="For small tech teams, TaskFlow is the AI task manager "
            "that automates workflow unlike Trello or Asana",
            differentiation_axes=["AI intelligence", "Simplicity"],
            go_to_market_angle="Product-led growth targeting developers",
        ),
        competitive_moat=["Proprietary AI model", "Community network effects"],
        key_takeaways=["Lead with AI", "Target SMBs first", "Keep it simple"],
    )


def _make_viability() -> ProductViability:
    return ProductViability(
        executive_summary="Product is technically viable with moderate investment.",
        overall_viability="viable",
        tech_feasibility=[
            TechFeasibility(
                area="Frontend SPA",
                feasibility="high",
                current_tech="Next.js 14",
                complexity="medium",
                notes="Standard web app development",
            ),
            TechFeasibility(
                area="AI Integration",
                feasibility="medium",
                current_tech="OpenAI API, LangChain",
                complexity="high",
                notes="Prompt engineering and fine-tuning needed",
            ),
            TechFeasibility(
                area="Real-time Collaboration",
                feasibility="medium",
                current_tech="WebSockets, Liveblocks",
                complexity="high",
                notes="Conflict resolution is non-trivial",
            ),
        ],
        resource_estimates=[
            ResourceEstimate(
                area="Frontend",
                team_size="2 engineers",
                duration="3 months",
                skills_required=["React", "TypeScript", "WebSocket"],
                cost_estimate="$80K-$120K",
            ),
            ResourceEstimate(
                area="Backend",
                team_size="2 engineers",
                duration="3 months",
                skills_required=["Python", "FastAPI", "PostgreSQL"],
                cost_estimate="$80K-$120K",
            ),
        ],
        total_budget_range="$300K-$500K",
        total_timeline="4-6 months to MVP",
        risks=[
            RiskFactor(
                risk="AI model quality issues",
                category="technical",
                probability="medium",
                impact="high",
                mitigation="Iterative prompt engineering with user feedback",
            ),
            RiskFactor(
                risk="Market timing",
                category="market",
                probability="low",
                impact="critical",
                mitigation="Fast MVP to validate demand",
            ),
            RiskFactor(
                risk="Team hiring delays",
                category="operational",
                probability="medium",
                impact="medium",
                mitigation="Start with contractors, hire full-time later",
            ),
        ],
        viability_scores=[
            ViabilityScore(
                dimension="Technical Feasibility",
                score=8,
                weight=4,
                rationale="Proven tech stack",
            ),
            ViabilityScore(
                dimension="Market Readiness",
                score=7,
                weight=5,
                rationale="Growing demand for AI tools",
            ),
            ViabilityScore(
                dimension="Financial Viability",
                score=6,
                weight=3,
                rationale="Moderate investment needed",
            ),
            ViabilityScore(
                dimension="Team Readiness",
                score=7,
                weight=3,
                rationale="Core team in place",
            ),
        ],
        build_vs_buy=[
            BuildVsBuy(
                component="Authentication",
                recommendation="buy",
                rationale="Auth is solved; build time not justified",
                options=["Clerk", "Auth0", "Firebase Auth"],
            ),
            BuildVsBuy(
                component="Task Engine",
                recommendation="build",
                rationale="Core differentiator — must be custom",
                options=[],
            ),
        ],
        validation_milestones=[
            MilestoneValidation(
                milestone="Technical Prototype",
                description="AI-powered task creation working end-to-end",
                success_criteria="User can describe a project and get structured tasks",
                timeline="4 weeks",
            ),
            MilestoneValidation(
                milestone="User Validation",
                description="10 beta users complete onboarding and use for 1 week",
                success_criteria="80% retention after first week",
                timeline="8 weeks",
            ),
        ],
        recommendations=[
            "Start with AI task creation as the hero feature",
            "Use a managed database to reduce DevOps overhead",
            "Hire a product designer early — UX is a key differentiator",
        ],
    )


def _make_roadmap() -> ProductRoadmap:
    return ProductRoadmap(
        executive_summary="3-phase roadmap from MVP to growth over 9 months.",
        vision="AI-first task management adopted by 10,000 teams in 12 months.",
        total_duration="9-12 months",
        phases=[
            RoadmapPhase(
                phase_number=1,
                name="MVP",
                description="Core task management with AI creation",
                duration="8 weeks",
                start="Month 1",
                features=[
                    RoadmapFeature(
                        name="Task Board",
                        description="Kanban board for task management",
                        effort="large",
                        priority="critical",
                        dependencies=[],
                    ),
                    RoadmapFeature(
                        name="AI Task Creator",
                        description="AI-powered task generation from description",
                        effort="large",
                        priority="critical",
                        dependencies=["Task Board"],
                    ),
                ],
                milestones=[
                    RoadmapMilestone(
                        name="Alpha Release",
                        description="Internal testing version",
                        deliverables=["Task board", "AI creation", "Auth"],
                        success_criteria="Team can manage a project end-to-end",
                    ),
                ],
                team_focus="Core product development",
                risks=["Scope creep", "AI quality"],
            ),
            RoadmapPhase(
                phase_number=2,
                name="Growth",
                description="Collaboration features and integrations",
                duration="8 weeks",
                start="After Phase 1",
                features=[
                    RoadmapFeature(
                        name="Team Collaboration",
                        description="Real-time multi-user features",
                        effort="large",
                        priority="high",
                        dependencies=["Task Board"],
                    ),
                ],
                milestones=[
                    RoadmapMilestone(
                        name="Beta Launch",
                        description="Public beta with invite system",
                        deliverables=["Collaboration", "Invites", "Onboarding"],
                        success_criteria="100 beta users onboarded",
                    ),
                ],
                team_focus="Growth and collaboration",
            ),
        ],
        resource_allocation=[
            ResourceAllocation(role="Frontend Engineer", count=2, phases=["MVP", "Growth"]),
            ResourceAllocation(role="Backend Engineer", count=2, phases=["MVP", "Growth"]),
            ResourceAllocation(role="Product Designer", count=1, phases=["MVP", "Growth"]),
        ],
        dependency_chains=[
            DependencyChain(
                chain_name="AI Pipeline",
                steps=["Task Board", "AI Task Creator", "AI Recommendations"],
                critical_path=True,
                risk_if_delayed="Delays the core value proposition",
            ),
        ],
        launch_criteria=["Performance < 2s load time", "Zero critical bugs", "Onboarding tested"],
        post_launch=["User feedback collection", "Performance monitoring", "Content marketing"],
    )


def _make_pitch_deck() -> PitchDeck:
    return PitchDeck(
        company_name="TaskFlow",
        tagline="AI-powered task management for small teams",
        elevator_pitch="TaskFlow uses AI to turn project descriptions into organized tasks. "
        "Small teams waste hours organizing work — we automate it. "
        "We're targeting the $12B SMB project management market.",
        slides=[
            PitchSlide(
                slide_number=1,
                title="TaskFlow",
                slide_type="title",
                headline="AI-Powered Task Management",
                bullet_points=["Task management reimagined with AI"],
                speaker_notes="Welcome. We are TaskFlow.",
                visual_suggestion="Company logo with tagline",
            ),
            PitchSlide(
                slide_number=2,
                title="The Problem",
                slide_type="problem",
                headline="Small teams waste 5+ hours/week organizing work",
                bullet_points=["Manual task creation", "No structure", "Context switching"],
                speaker_notes="Every small team faces this problem.",
                visual_suggestion="Bar chart showing time wasted",
            ),
            PitchSlide(
                slide_number=3,
                title="Our Solution",
                slide_type="solution",
                headline="Describe your project, get organized tasks instantly",
                bullet_points=["AI-powered", "Instant structure", "Simple UX"],
                speaker_notes="TaskFlow solves this with AI.",
                visual_suggestion="Product screenshot showing AI in action",
            ),
            PitchSlide(
                slide_number=4,
                title="Market",
                slide_type="market",
                headline="$12B addressable market growing 14% YoY",
                bullet_points=["TAM: $50B", "SAM: $12B", "SOM: $800M"],
                speaker_notes="The market is large and growing.",
                visual_suggestion="TAM/SAM/SOM funnel chart",
            ),
            PitchSlide(
                slide_number=5,
                title="Product",
                slide_type="product",
                headline="AI that organizes your work",
                bullet_points=["Kanban board", "AI task creation", "Real-time collaboration"],
                speaker_notes="Let me show you the product.",
                visual_suggestion="Product demo screenshot",
            ),
            PitchSlide(
                slide_number=6,
                title="Business Model",
                slide_type="business_model",
                headline="Freemium SaaS with per-seat pricing",
                bullet_points=["Free tier for up to 5 users", "$12/seat/month for teams"],
                speaker_notes="We monetize through per-seat pricing.",
                visual_suggestion="Pricing table comparison",
            ),
            PitchSlide(
                slide_number=7,
                title="Traction",
                slide_type="traction",
                headline="500 waitlist signups in 2 weeks",
                bullet_points=["500 waitlist", "20 LOIs", "3 pilot customers"],
                speaker_notes="Early traction is strong.",
                visual_suggestion="Growth chart showing signups over time",
            ),
            PitchSlide(
                slide_number=8,
                title="The Ask",
                slide_type="ask",
                headline="Raising $2M to reach product-market fit",
                bullet_points=["$2M seed round", "18 month runway", "Hire 5 engineers"],
                speaker_notes="We're raising 2 million dollars.",
                visual_suggestion="Pie chart of fund allocation",
            ),
        ],
        financial_highlights=[
            FinancialHighlight(metric="ARR Target Y1", value="$500K", context="Based on 500 teams"),
            FinancialHighlight(metric="CAC", value="$150", context="PLG-driven acquisition"),
            FinancialHighlight(metric="LTV", value="$2,400", context="24-month avg retention"),
        ],
        funding_ask=FundingAsk(
            amount="$2M Seed",
            use_of_funds=["Engineering (60%)", "Go-to-market (25%)", "Operations (15%)"],
            milestones_to_reach=["1,000 paying teams", "Product-market fit signal"],
            runway="18 months",
        ),
        appendix_topics=[
            "Detailed financial model",
            "Technical architecture",
            "Competitive deep-dive",
        ],
    )


# --- Tests ---


class TestMarketAnalysis:
    def test_roundtrip_json(self):
        analysis = _make_market_analysis()
        json_str = analysis.model_dump_json()
        restored = MarketAnalysis.model_validate_json(json_str)
        assert restored.market_sizing.tam_value == "$50B"
        assert len(restored.market_segments) == 2

    def test_to_markdown(self):
        analysis = _make_market_analysis()
        md = analysis.to_markdown()
        assert "# Market Analysis" in md
        assert "TAM" in md
        assert "SAM" in md
        assert "SOM" in md
        assert "Opportunity Assessment" in md
        assert "5-Year Projections" in md

    def test_opportunity_scores_valid_range(self):
        analysis = _make_market_analysis()
        for score in analysis.opportunity_scores:
            assert 1 <= score.score <= 10

    def test_json_schema(self):
        schema = MarketAnalysis.model_json_schema()
        assert "properties" in schema
        assert "market_sizing" in schema["properties"]


class TestCompetitorAnalysis:
    def test_roundtrip_json(self):
        analysis = _make_competitor_analysis()
        json_str = analysis.model_dump_json()
        restored = CompetitorAnalysis.model_validate_json(json_str)
        assert len(restored.competitors) == 2
        assert restored.competitors[0].name == "Asana"

    def test_to_markdown(self):
        analysis = _make_competitor_analysis()
        md = analysis.to_markdown()
        assert "# Competitor Analysis" in md
        assert "Feature Comparison Matrix" in md
        assert "SWOT Analysis" in md
        assert "Positioning Strategy" in md
        assert "Asana" in md
        assert "Trello" in md

    def test_feature_matrix_structure(self):
        analysis = _make_competitor_analysis()
        for fm in analysis.feature_matrix:
            assert isinstance(fm.competitors, dict)
            assert "Asana" in fm.competitors

    def test_swot_completeness(self):
        analysis = _make_competitor_analysis()
        assert len(analysis.swot.strengths) >= 2
        assert len(analysis.swot.weaknesses) >= 2
        assert len(analysis.swot.opportunities) >= 2
        assert len(analysis.swot.threats) >= 2


class TestProductViability:
    def test_roundtrip_json(self):
        viability = _make_viability()
        json_str = viability.model_dump_json()
        restored = ProductViability.model_validate_json(json_str)
        assert restored.overall_viability == "viable"
        assert len(restored.tech_feasibility) == 3

    def test_to_markdown(self):
        viability = _make_viability()
        md = viability.to_markdown()
        assert "# Product Viability Assessment" in md
        assert "Technical Feasibility" in md
        assert "Risk Assessment" in md
        assert "Viability Scores" in md
        assert "Build vs. Buy" in md

    def test_weighted_score_calculation(self):
        viability = _make_viability()
        weighted = sum(v.score * v.weight for v in viability.viability_scores)
        max_score = sum(10 * v.weight for v in viability.viability_scores)
        assert weighted > 0
        assert weighted <= max_score

    def test_viability_scores_valid(self):
        viability = _make_viability()
        for vs in viability.viability_scores:
            assert 1 <= vs.score <= 10
            assert 1 <= vs.weight <= 5


class TestProductRoadmap:
    def test_roundtrip_json(self):
        roadmap = _make_roadmap()
        json_str = roadmap.model_dump_json()
        restored = ProductRoadmap.model_validate_json(json_str)
        assert len(restored.phases) == 2
        assert restored.phases[0].name == "MVP"

    def test_to_markdown(self):
        roadmap = _make_roadmap()
        md = roadmap.to_markdown()
        assert "# Product Roadmap" in md
        assert "Phase 1: MVP" in md
        assert "Phase 2: Growth" in md
        assert "Resource Allocation" in md
        assert "Launch Criteria" in md
        assert "Dependency Chains" in md

    def test_phases_ordered(self):
        roadmap = _make_roadmap()
        for i, phase in enumerate(roadmap.phases):
            assert phase.phase_number == i + 1

    def test_dependency_chain_has_steps(self):
        roadmap = _make_roadmap()
        for dc in roadmap.dependency_chains:
            assert len(dc.steps) >= 2


class TestPitchDeck:
    def test_roundtrip_json(self):
        deck = _make_pitch_deck()
        json_str = deck.model_dump_json()
        restored = PitchDeck.model_validate_json(json_str)
        assert restored.company_name == "TaskFlow"
        assert len(restored.slides) == 8

    def test_to_markdown(self):
        deck = _make_pitch_deck()
        md = deck.to_markdown()
        assert "# Pitch Deck: TaskFlow" in md
        assert "Elevator Pitch" in md
        assert "Slide 1:" in md
        assert "Financial Highlights" in md
        assert "Funding Ask" in md

    def test_slides_ordered(self):
        deck = _make_pitch_deck()
        for i, slide in enumerate(deck.slides):
            assert slide.slide_number == i + 1

    def test_funding_ask_structure(self):
        deck = _make_pitch_deck()
        assert deck.funding_ask.amount == "$2M Seed"
        assert len(deck.funding_ask.use_of_funds) >= 2
        assert len(deck.funding_ask.milestones_to_reach) >= 2

    def test_json_schema(self):
        schema = PitchDeck.model_json_schema()
        assert "properties" in schema
        assert "slides" in schema["properties"]
