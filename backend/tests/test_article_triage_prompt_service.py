from types import SimpleNamespace

import pytest

from app.services.article_triage_prompt_service import (
    build_article_triage_prompt,
)
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)
from app.services.rag_context_service import RAGContext
from app.services.semantic_search_service import (
    SemanticSearchResult,
)


def make_article():
    return SimpleNamespace(
        id=8,
        title="PayU receives RBI approval",
        source_name="test-source",
        cleaned_content=(
            "PayU received final RBI approval "
            "to operate as a payment aggregator."
        ),
    )


def make_company_context():
    return CompanySemanticContext(
        company_id=1,
        company_name="PayU",
        text=(
            "Company: PayU\n"
            "Industry: Fintech / Payments\n"
            "Regulators: RBI"
        ),
    )


def make_rag_context():
    return RAGContext(
        query="PayU: PayU receives RBI approval",
        related_articles=[
            SemanticSearchResult(
                article_id=5,
                title="PayU India growth strategy",
                source_name="source-a",
                url="https://example.com/5",
                published_at=None,
                distance=0.2,
                similarity=0.8,
            ),
            SemanticSearchResult(
                article_id=3,
                title="PayU RBI compliant checkout",
                source_name="source-b",
                url="https://example.com/3",
                published_at=None,
                distance=0.3,
                similarity=0.7,
            ),
        ],
    )


def test_prompt_contains_primary_context_and_rag():
    article = make_article()
    company_context = make_company_context()
    rag_context = make_rag_context()

    prompt = build_article_triage_prompt(
        article,
        company_context,
        rag_context,
    )

    assert "Company: PayU" in prompt
    assert article.title in prompt
    assert article.cleaned_content in prompt

    assert "RETRIEVED RELATED ARTICLES:" in prompt
    assert "Article ID 5" in prompt
    assert "Article ID 3" in prompt
    assert "similarity=0.8000" in prompt
    assert "similarity=0.7000" in prompt

    assert "Do not invent facts." in prompt
    assert "Return ONLY valid JSON" in prompt


def test_prompt_handles_no_related_articles():
    prompt = build_article_triage_prompt(
        make_article(),
        make_company_context(),
        RAGContext(
            query="test",
            related_articles=[],
        ),
    )

    assert (
        "No related articles retrieved."
        in prompt
    )


def test_prompt_works_without_rag_context():
    prompt = build_article_triage_prompt(
        make_article(),
        make_company_context(),
    )

    assert (
        "No related articles retrieved."
        in prompt
    )


def test_prompt_rejects_empty_article_content():
    article = make_article()
    article.cleaned_content = "   "

    with pytest.raises(
        ValueError,
        match="Article cleaned content is required",
    ):
        build_article_triage_prompt(
            article,
            make_company_context(),
        )


def test_prompt_rejects_empty_company_context():
    context = CompanySemanticContext(
        company_id=1,
        company_name="PayU",
        text="   ",
    )

    with pytest.raises(
        ValueError,
        match="Company semantic context is required",
    ):
        build_article_triage_prompt(
            make_article(),
            context,
        )
