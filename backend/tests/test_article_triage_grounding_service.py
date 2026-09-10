import pytest

from app.schemas.article_triage import ArticleTriageResult
from app.services.article_triage_grounding_service import (
    validate_triage_grounding,
)


def make_triage(evidence):
    return ArticleTriageResult(
        company_name="PayU",
        event_type="regulatory_action",
        summary="PayU received RBI approval.",
        why_it_matters="This supports regulated operations.",
        evidence=evidence,
        potential_impact="PayU can expand operations.",
        urgency="high",
        confidence=0.9,
    )


def test_grounding_accepts_supported_evidence():
    validate_triage_grounding(
        article_content=(
            "PayU received final approval from the RBI "
            "to operate as an online payment aggregator."
        ),
        triage=make_triage(
            [
                "PayU received final approval from RBI."
            ]
        ),
    )


def test_grounding_rejects_unrelated_evidence():
    with pytest.raises(
        ValueError,
        match="not sufficiently grounded",
    ):
        validate_triage_grounding(
            article_content=(
                "PayU received final approval from RBI."
            ),
            triage=make_triage(
                [
                    "The company acquired a bank in Europe."
                ]
            ),
        )


def test_grounding_accepts_one_grounded_item():
    validate_triage_grounding(
        article_content=(
            "PayU received final RBI approval "
            "for payment aggregator operations."
        ),
        triage=make_triage(
            [
                "PayU received final RBI approval.",
                "The company launched a satellite.",
            ]
        ),
    )


def test_grounding_rejects_empty_article():
    with pytest.raises(
        ValueError,
        match="Article content is required",
    ):
        validate_triage_grounding(
            article_content="   ",
            triage=make_triage(
                [
                    "PayU received RBI approval."
                ]
            ),
        )
