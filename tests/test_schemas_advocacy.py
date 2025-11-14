"""
Tests for advocacy Pydantic schemas.

Following TDD approach - these tests are written BEFORE implementation.
Tests cover validation, constraints, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError


class TestStrengthItem:
    """Tests for StrengthItem model (inherits from TitledItem)."""

    def test_strength_item_valid(self):
        """Valid StrengthItem with title and description."""
        from madspark.schemas.advocacy import StrengthItem

        strength = StrengthItem(
            title="Market Opportunity",
            description="Growing demand in enterprise sector with 25% CAGR"
        )

        assert strength.title == "Market Opportunity"
        assert "25% CAGR" in strength.description

    def test_strength_item_inherits_titled_item_validation(self):
        """StrengthItem inherits TitledItem validation constraints."""
        from madspark.schemas.advocacy import StrengthItem

        # Title too long
        with pytest.raises(ValidationError) as exc_info:
            StrengthItem(
                title="A" * 201,
                description="Valid description"
            )
        assert "200" in str(exc_info.value)

    def test_strength_item_serialization(self):
        """StrengthItem serializes to dict."""
        from madspark.schemas.advocacy import StrengthItem

        strength = StrengthItem(
            title="Innovation",
            description="Novel approach to solving problem"
        )

        data = strength.model_dump()
        assert isinstance(data, dict)
        assert data["title"] == "Innovation"


class TestOpportunityItem:
    """Tests for OpportunityItem model (inherits from TitledItem)."""

    def test_opportunity_item_valid(self):
        """Valid OpportunityItem with title and description."""
        from madspark.schemas.advocacy import OpportunityItem

        opportunity = OpportunityItem(
            title="Strategic Partnerships",
            description="Potential collaboration with industry leaders"
        )

        assert opportunity.title == "Strategic Partnerships"
        assert "collaboration" in opportunity.description

    def test_opportunity_item_unicode_support(self):
        """OpportunityItem supports unicode."""
        from madspark.schemas.advocacy import OpportunityItem

        opportunity = OpportunityItem(
            title="市場機会",
            description="日本市場への展開の可能性"
        )

        assert "市場" in opportunity.title


class TestConcernResponse:
    """Tests for ConcernResponse model (concern + response pair)."""

    def test_concern_response_valid(self):
        """Valid ConcernResponse with concern and response."""
        from madspark.schemas.advocacy import ConcernResponse

        cr = ConcernResponse(
            concern="High development cost",
            response="Can be mitigated through phased rollout and MVP approach"
        )

        assert cr.concern == "High development cost"
        assert "phased rollout" in cr.response

    def test_concern_response_concern_too_short(self):
        """Concern must be at least 1 character."""
        from madspark.schemas.advocacy import ConcernResponse

        with pytest.raises(ValidationError) as exc_info:
            ConcernResponse(
                concern="",
                response="Valid response here"
            )
        assert "concern" in str(exc_info.value).lower()

    def test_concern_response_concern_too_long(self):
        """Concern cannot exceed 500 characters."""
        from madspark.schemas.advocacy import ConcernResponse

        with pytest.raises(ValidationError) as exc_info:
            ConcernResponse(
                concern="A" * 501,
                response="Valid response"
            )
        assert "500" in str(exc_info.value)

    def test_concern_response_response_too_long(self):
        """Response cannot exceed 1000 characters."""
        from madspark.schemas.advocacy import ConcernResponse

        with pytest.raises(ValidationError) as exc_info:
            ConcernResponse(
                concern="Valid concern",
                response="A" * 1001
            )
        assert "1000" in str(exc_info.value)

    def test_concern_response_serialization(self):
        """ConcernResponse serializes to dict."""
        from madspark.schemas.advocacy import ConcernResponse

        cr = ConcernResponse(
            concern="Technical complexity",
            response="Address with experienced team"
        )

        data = cr.model_dump()
        assert data["concern"] == "Technical complexity"
        assert data["response"] == "Address with experienced team"


class TestAdvocacyResponse:
    """Tests for AdvocacyResponse model (complete advocacy output)."""

    def test_advocacy_response_valid_minimal(self):
        """Valid AdvocacyResponse with minimum required fields."""
        from madspark.schemas.advocacy import AdvocacyResponse, StrengthItem, OpportunityItem, ConcernResponse

        advocacy = AdvocacyResponse(
            strengths=[
                StrengthItem(title="Strong team", description="Experienced founders")
            ],
            opportunities=[
                OpportunityItem(title="Market gap", description="Unserved segment")
            ],
            addressing_concerns=[
                ConcernResponse(concern="Cost", response="Bootstrap approach")
            ]
        )

        assert len(advocacy.strengths) == 1
        assert len(advocacy.opportunities) == 1
        assert len(advocacy.addressing_concerns) == 1

    def test_advocacy_response_valid_full(self):
        """Valid AdvocacyResponse with multiple items."""
        from madspark.schemas.advocacy import AdvocacyResponse, StrengthItem, OpportunityItem, ConcernResponse

        advocacy = AdvocacyResponse(
            strengths=[
                StrengthItem(title="Strength 1", description="Description 1"),
                StrengthItem(title="Strength 2", description="Description 2"),
                StrengthItem(title="Strength 3", description="Description 3")
            ],
            opportunities=[
                OpportunityItem(title="Opportunity 1", description="Description 1"),
                OpportunityItem(title="Opportunity 2", description="Description 2")
            ],
            addressing_concerns=[
                ConcernResponse(concern="Concern 1", response="Response 1"),
                ConcernResponse(concern="Concern 2", response="Response 2"),
                ConcernResponse(concern="Concern 3", response="Response 3"),
                ConcernResponse(concern="Concern 4", response="Response 4")
            ]
        )

        assert len(advocacy.strengths) == 3
        assert len(advocacy.opportunities) == 2
        assert len(advocacy.addressing_concerns) == 4

    def test_advocacy_response_empty_strengths_array(self):
        """Strengths array must have at least one item."""
        from madspark.schemas.advocacy import AdvocacyResponse, OpportunityItem, ConcernResponse

        with pytest.raises(ValidationError) as exc_info:
            AdvocacyResponse(
                strengths=[],
                opportunities=[
                    OpportunityItem(title="Opportunity", description="Description")
                ],
                addressing_concerns=[
                    ConcernResponse(concern="Concern", response="Response")
                ]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_advocacy_response_empty_opportunities_array(self):
        """Opportunities array must have at least one item."""
        from madspark.schemas.advocacy import AdvocacyResponse, StrengthItem, ConcernResponse

        with pytest.raises(ValidationError) as exc_info:
            AdvocacyResponse(
                strengths=[
                    StrengthItem(title="Strength", description="Description")
                ],
                opportunities=[],
                addressing_concerns=[
                    ConcernResponse(concern="Concern", response="Response")
                ]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_advocacy_response_empty_concerns_array(self):
        """Addressing_concerns array must have at least one item."""
        from madspark.schemas.advocacy import AdvocacyResponse, StrengthItem, OpportunityItem

        with pytest.raises(ValidationError) as exc_info:
            AdvocacyResponse(
                strengths=[
                    StrengthItem(title="Strength", description="Description")
                ],
                opportunities=[
                    OpportunityItem(title="Opportunity", description="Description")
                ],
                addressing_concerns=[]
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_advocacy_response_unicode_support(self):
        """AdvocacyResponse supports unicode in all fields."""
        from madspark.schemas.advocacy import AdvocacyResponse, StrengthItem, OpportunityItem, ConcernResponse

        advocacy = AdvocacyResponse(
            strengths=[
                StrengthItem(title="強み", description="経験豊富なチーム")
            ],
            opportunities=[
                OpportunityItem(title="機会", description="市場拡大の可能性")
            ],
            addressing_concerns=[
                ConcernResponse(concern="懸念事項", response="対応策を実施")
            ]
        )

        assert "強み" in advocacy.strengths[0].title
        assert "機会" in advocacy.opportunities[0].title

    def test_advocacy_response_serialization(self):
        """AdvocacyResponse serializes to dict with nested structures."""
        from madspark.schemas.advocacy import AdvocacyResponse, StrengthItem, OpportunityItem, ConcernResponse

        advocacy = AdvocacyResponse(
            strengths=[
                StrengthItem(title="Strength", description="Description")
            ],
            opportunities=[
                OpportunityItem(title="Opportunity", description="Description")
            ],
            addressing_concerns=[
                ConcernResponse(concern="Concern", response="Response")
            ]
        )

        data = advocacy.model_dump()
        assert isinstance(data, dict)
        assert isinstance(data["strengths"], list)
        assert len(data["strengths"]) == 1
        assert data["strengths"][0]["title"] == "Strength"
        assert data["addressing_concerns"][0]["concern"] == "Concern"


class TestAdvocacyAdapters:
    """Tests for adapter conversions with advocacy schemas."""

    def test_advocacy_response_to_genai_schema(self):
        """AdvocacyResponse converts to GenAI schema format."""
        from madspark.schemas.advocacy import AdvocacyResponse
        from madspark.schemas.adapters import pydantic_to_genai_schema

        schema = pydantic_to_genai_schema(AdvocacyResponse)

        assert schema["type"] == "OBJECT"
        assert "strengths" in schema["properties"]
        assert schema["properties"]["strengths"]["type"] == "ARRAY"
        assert "opportunities" in schema["properties"]
        assert "addressing_concerns" in schema["properties"]
        assert "required" in schema
        assert "strengths" in schema["required"]

    def test_genai_response_to_advocacy(self):
        """GenAI JSON response parses to AdvocacyResponse."""
        from madspark.schemas.advocacy import AdvocacyResponse
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "strengths": [
                {"title": "Strong team", "description": "Experienced founders"}
            ],
            "opportunities": [
                {"title": "Market gap", "description": "Unserved segment"}
            ],
            "addressing_concerns": [
                {"concern": "High cost", "response": "Bootstrap approach"}
            ]
        })

        advocacy = genai_response_to_pydantic(response_text, AdvocacyResponse)

        assert isinstance(advocacy, AdvocacyResponse)
        assert len(advocacy.strengths) == 1
        assert advocacy.strengths[0].title == "Strong team"
        assert advocacy.addressing_concerns[0].concern == "High cost"

    def test_genai_response_complex_advocacy(self):
        """GenAI response with multiple items parses correctly."""
        from madspark.schemas.advocacy import AdvocacyResponse
        from madspark.schemas.adapters import genai_response_to_pydantic
        import json

        response_text = json.dumps({
            "strengths": [
                {"title": "S1", "description": "D1"},
                {"title": "S2", "description": "D2"}
            ],
            "opportunities": [
                {"title": "O1", "description": "D1"},
                {"title": "O2", "description": "D2"},
                {"title": "O3", "description": "D3"}
            ],
            "addressing_concerns": [
                {"concern": "C1", "response": "R1"}
            ]
        })

        advocacy = genai_response_to_pydantic(response_text, AdvocacyResponse)

        assert len(advocacy.strengths) == 2
        assert len(advocacy.opportunities) == 3
        assert len(advocacy.addressing_concerns) == 1
