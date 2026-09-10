from app.models.article import Article
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)
from app.services.rag_context_service import RAGContext


def build_article_triage_prompt(
    article: Article,
    company_context: CompanySemanticContext,
    rag_context: RAGContext | None = None,
) -> str:
    article_text = (article.cleaned_content or "").strip()

    if not article_text:
        raise ValueError(
            "Article cleaned content is required for triage."
        )

    company_text = company_context.text.strip()

    if not company_text:
        raise ValueError(
            "Company semantic context is required for triage."
        )

    related_articles_text = "No related articles retrieved."

    if rag_context and rag_context.related_articles:
        related_articles_text = "\n".join(
            (
                f"- Article ID {item.article_id}: "
                f"{item.title} "
                f"(similarity={item.similarity:.4f})"
            )
            for item in rag_context.related_articles
        )

    return f"""
You are a media intelligence analyst.

Analyze the primary news article using only:
1. the supplied company context,
2. the supplied primary article,
3. the retrieved related article titles.

The primary article is the main source of truth.

Related articles provide supporting context only.
Do not claim details from related articles unless those details
are explicitly present in their supplied titles.

Do not invent facts.
Do not use outside knowledge.
If evidence is weak or incomplete, lower confidence.

COMPANY CONTEXT:
{company_text}

PRIMARY ARTICLE TITLE:
{article.title}

PRIMARY ARTICLE SOURCE:
{article.source_name}

PRIMARY ARTICLE CONTENT:
{article_text}

RETRIEVED RELATED ARTICLES:
{related_articles_text}

Return ONLY valid JSON with exactly these fields:

{{
  "company_name": "{company_context.company_name}",
  "event_type": "regulatory_action | fraud_security | service_outage | leadership_change | product_launch | financial_performance | market_competition | other",
  "summary": "Short factual summary of the primary article.",
  "why_it_matters": "Why this news matters to the monitored company.",
  "evidence": [
    "Specific factual evidence from the primary article."
  ],
  "potential_impact": "Possible business impact supported by the supplied information.",
  "urgency": "low | medium | high | critical",
  "confidence": 0.0
}}

Rules:
- company_name must be exactly "{company_context.company_name}".
- Choose exactly one event_type.
- Choose exactly one urgency level.
- confidence must be between 0.0 and 1.0.
- evidence must contain only claims supported by the primary article.
- Do not include Markdown.
- Do not include code fences.
- Do not include text before or after the JSON.
""".strip()
