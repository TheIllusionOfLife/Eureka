"""
Tests for skepticism Pydantic schemas.

Following TDD approach - these tests are written BEFORE implementation.
Tests cover validation, constraints, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError


class TestCriticalFlaw:
    """Tests for CriticalFlaw model (inherits from TitledItem)."""

    def test_critical_flaw_valid(self):
        """Valid CriticalFlaw with title and description."""
        from madspark.schemas.skepticism import CriticalFlaw

        flaw = CriticalFlaw(
            title="Scalability Concerns",
            description="Current architecture cannot handle more than 1000 concurrent users"
        )

        assert flaw.title == "Scalability Concerns"
        assert "1000 concurrent users" in flaw.description

    def test_critical_flaw_inherits_validation(self):
        """CriticalFlaw inherits TitledItem validation."""
        from madspark.schemas.skepticism import CriticalFlaw

        with pytest.raises(ValidationError):
            CriticalFlaw(title="", description="Valid description")


class TestRiskChallenge:
    """Tests for RiskChallenge model (inherits from TitledItem)."""

    def test_risk_challenge_valid(self):
        """Valid RiskChallenge with title and description."""
        from madspark.schemas.skepticism import RiskChallenge

        risk = RiskChallenge(
            title="Regulatory Uncertainty",
            description="Unclear regulations in key markets may delay launch"
        )

        assert risk.title == "Regulatory Uncertainty"
        assert "regulations" in risk.description


class TestQuestionableAssumption:
    """Tests for QuestionableAssumption model."""

    def test_questionable_assumption_valid(self):
        """Valid QuestionableAssumption with assumption and concern."""
        from madspark.schemas.skepticism import QuestionableAssumption

        qa = QuestionableAssumption(
            assumption="Users will pay premium pricing",
            concern="Market research shows price sensitivity in target demographic"
        )

        assert qa.assumption == "Users will pay premium pricing"
        assert "price sensitivity" in qa.concern

    def test_questionable_assumption_too_short(self):
        """Assumption must be at least 1 character."""
        from madspark.schemas.skepticism import QuestionableAssumption

        with pytest.raises(ValidationError):
            QuestionableAssumption(
                assumption="",
                concern="Valid concern"
            )

    def test_questionable_assumption_too_long(self):
        """Assumption cannot exceed 500 characters."""
        from madspark.schemas.skepticism import QuestionableAssumption

        with pytest.raises(ValidationError):
            QuestionableAssumption(
                assumption="A" * 501,
                concern="Valid concern"
            )

    def test_questionable_assumption_concern_too_long(self):
        """Concern cannot exceed 1000 characters."""
        from madspark.schemas.skepticism import QuestionableAssumption

        with pytest.raises(ValidationError):
            QuestionableAssumption(
                assumption="Valid assumption",
                concern="A" * 1001
            )


class TestMissingConsideration:
    """Tests for MissingConsideration model."""

    def test_missing_consideration_valid(self):
        """Valid MissingConsideration with aspect and importance."""
        from madspark.schemas.skepticism import MissingConsideration

        mc = MissingConsideration(
            aspect="Data Privacy Compliance",
            importance="GDPR compliance is critical for EU market entry"
        )

        assert mc.aspect == "Data Privacy Compliance"
        assert "GDPR" in mc.importance

    def test_missing_consideration_aspect_too_short(self):
        """Aspect must be at least 1 character."""
        from madspark.schemas.skepticism import MissingConsideration

        with pytest.raises(ValidationError):
            MissingConsideration(
                aspect="",
                importance="Valid importance"
            )

    def test_missing_consideration_aspect_too_long(self):
        """Aspect cannot exceed 200 characters."""
        from madspark.schemas.skepticism import MissingConsideration

        with pytest.raises(ValidationError):
            MissingConsideration(
                aspect="A" * 201,
                importance="Valid importance"
            )

    def test_missing_consideration_importance_too_long(self):
        """Importance cannot exceed 1000 characters."""
        from madspark.schemas.skepticism import MissingConsideration

        with pytest.raises(ValidationError):
            MissingConsideration(
                aspect="Valid aspect",
                importance="A" * 1001
            )


class TestSkepticismResponse:
    """Tests for SkepticismResponse model (complete skepticism output)."""

    def test_skepticism_response_valid_minimal(self):
        """Valid SkepticismResponse with minimum required fields."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw, RiskChallenge,
            QuestionableAssumption, MissingConsideration
        )

        skepticism = SkepticismResponse(
            critical_flaws=[
                CriticalFlaw(title="Flaw", description="Description")
            ],
            risks_and_challenges=[
                RiskChallenge(title="Risk", description="Description")
            ],
            questionable_assumptions=[
                QuestionableAssumption(assumption="Assumption", concern="Concern")
            ],
            missing_considerations=[
                MissingConsideration(aspect="Aspect", importance="Importance")
            ]
        )

        assert len(skepticism.critical_flaws) == 1
        assert len(skepticism.risks_and_challenges) == 1
        assert len(skepticism.questionable_assumptions) == 1
        assert len(skepticism.missing_considerations) == 1

    def test_skepticism_response_valid_full(self):
        """Valid SkepticismResponse with multiple items."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw, RiskChallenge,
            QuestionableAssumption, MissingConsideration
        )

        skepticism = SkepticismResponse(
            critical_flaws=[
                CriticalFlaw(title="F1", description="D1"),
                CriticalFlaw(title="F2", description="D2")
            ],
            risks_and_challenges=[
                RiskChallenge(title="R1", description="D1"),
                RiskChallenge(title="R2", description="D2"),
                RiskChallenge(title="R3", description="D3")
            ],
            questionable_assumptions=[
                QuestionableAssumption(assumption="A1", concern="C1"),
                QuestionableAssumption(assumption="A2", concern="C2")
            ],
            missing_considerations=[
                MissingConsideration(aspect="M1", importance="I1"),
                MissingConsideration(aspect="M2", importance="I2"),
                MissingConsideration(aspect="M3", importance="I3"),
                MissingConsideration(aspect="M4", importance="I4")
            ]
        )

        assert len(skepticism.critical_flaws) == 2
        assert len(skepticism.risks_and_challenges) == 3
        assert len(skepticism.questionable_assumptions) == 2
        assert len(skepticism.missing_considerations) == 4

    def test_skepticism_response_empty_flaws_array(self):
        """Critical_flaws array must have at least one item."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, RiskChallenge,
            QuestionableAssumption, MissingConsideration
        )

        with pytest.raises(ValidationError) as exc_info:
            SkepticismResponse(
                critical_flaws=[],
                risks_and_challenges=[
                    RiskChallenge(title="R", description="D")
                ],
                questionable_assumptions=[
                    QuestionableAssumption(assumption="A", concern="C")
                ],
                missing_considerations=[
                    MissingConsideration(aspect="M", importance="I")
                ]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_skepticism_response_empty_risks_array(self):
        """Risks_and_challenges array must have at least one item."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw,
            QuestionableAssumption, MissingConsideration
        )

        with pytest.raises(ValidationError) as exc_info:
            SkepticismResponse(
                critical_flaws=[
                    CriticalFlaw(title="F", description="D")
                ],
                risks_and_challenges=[],
                questionable_assumptions=[
                    QuestionableAssumption(assumption="A", concern="C")
                ],
                missing_considerations=[
                    MissingConsideration(aspect="M", importance="I")
                ]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_skepticism_response_empty_assumptions_array(self):
        """Questionable_assumptions array must have at least one item."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw, RiskChallenge,
            MissingConsideration
        )

        with pytest.raises(ValidationError) as exc_info:
            SkepticismResponse(
                critical_flaws=[
                    CriticalFlaw(title="F", description="D")
                ],
                risks_and_challenges=[
                    RiskChallenge(title="R", description="D")
                ],
                questionable_assumptions=[],
                missing_considerations=[
                    MissingConsideration(aspect="M", importance="I")
                ]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_skepticism_response_empty_considerations_array(self):
        """Missing_considerations array must have at least one item."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw, RiskChallenge,
            QuestionableAssumption
        )

        with pytest.raises(ValidationError) as exc_info:
            SkepticismResponse(
                critical_flaws=[
                    CriticalFlaw(title="F", description="D")
                ],
                risks_and_challenges=[
                    RiskChallenge(title="R", description="D")
                ],
                questionable_assumptions=[
                    QuestionableAssumption(assumption="A", concern="C")
                ],
                missing_considerations=[]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_skepticism_response_unicode_support(self):
        """SkepticismResponse supports unicode."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw, RiskChallenge,
            QuestionableAssumption, MissingConsideration
        )

        skepticism = SkepticismResponse(
            critical_flaws=[
                CriticalFlaw(title="致命的欠陥", description="スケーラビリティの問題")
            ],
            risks_and_challenges=[
                RiskChallenge(title="リスク", description="規制の不確実性")
            ],
            questionable_assumptions=[
                QuestionableAssumption(assumption="仮定", concern="懸念")
            ],
            missing_considerations=[
                MissingConsideration(aspect="側面", importance="重要性")
            ]
        )

        assert "致命的" in skepticism.critical_flaws[0].title

    def test_skepticism_response_serialization(self):
        """SkepticismResponse serializes to dict."""
        from madspark.schemas.skepticism import (
            SkepticismResponse, CriticalFlaw, RiskChallenge,
            QuestionableAssumption, MissingConsideration
        )

        skepticism = SkepticismResponse(
            critical_flaws=[
                CriticalFlaw(title="Flaw", description="Description")
            ],
            risks_and_challenges=[
                RiskChallenge(title="Risk", description="Description")
            ],
            questionable_assumptions=[
                QuestionableAssumption(assumption="Assumption", concern="Concern")
            ],
            missing_considerations=[
                MissingConsideration(aspect="Aspect", importance="Importance")
            ]
        )

        data = skepticism.model_dump()
        assert isinstance(data, dict)
        assert len(data["critical_flaws"]) == 1
        assert data["questionable_assumptions"][0]["assumption"] == "Assumption"


class TestSkepticismAdapters:
    """Tests for adapter conversions with skepticism schemas."""

    def test_skepticism_response_to_genai_schema(self):
        """SkepticismResponse converts to GenAI schema."""
        from madspark.schemas.skepticism import SkepticismResponse
        from madspark.schemas.adapters import pydantic_to_genai_schema

        schema = pydantic_to_genai_schema(SkepticismResponse)

        assert schema["type"] == "OBJECT"
        assert "critical_flaws" in schema["properties"]
        assert schema["properties"]["critical_flaws"]["type"] == "ARRAY"
        assert "risks_and_challenges" in schema["properties"]
        assert "questionable_assumptions" in schema["properties"]
        assert "missing_considerations" in schema["properties"]

    def test_genai_response_to_skepticism(self):
        """GenAI JSON response parses to SkepticismResponse."""
        from madspark.schemas.skepticism import SkepticismResponse
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "critical_flaws": [
                {"title": "Flaw", "description": "Description"}
            ],
            "risks_and_challenges": [
                {"title": "Risk", "description": "Description"}
            ],
            "questionable_assumptions": [
                {"assumption": "Assumption", "concern": "Concern"}
            ],
            "missing_considerations": [
                {"aspect": "Aspect", "importance": "Importance"}
            ]
        })

        skepticism = genai_response_to_pydantic(response_text, SkepticismResponse)

        assert isinstance(skepticism, SkepticismResponse)
        assert len(skepticism.critical_flaws) == 1
        assert skepticism.questionable_assumptions[0].assumption == "Assumption"
