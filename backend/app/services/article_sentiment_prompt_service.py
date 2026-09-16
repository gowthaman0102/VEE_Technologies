from app.models.article import Article
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)


def build_article_sentiment_prompt(
    article: Article,
    company_context: CompanySemanticContext,
) -> str:
    article_text = (
        article.cleaned_content or ""
    ).strip()

    if not article_text:
        raise ValueError(
            "Article cleaned content is required "
            "for sentiment analysis."
        )

    company_text = (
        company_context.text or ""
    ).strip()

    if not company_text:
        raise ValueError(
            "Company semantic context is required "
            "for sentiment analysis."
        )

    return f"""
You are a media intelligence sentiment analyst.

Determine the sentiment of the supplied news article
specifically toward the monitored company.

Use only:
1. the supplied company context,
2. the supplied article.

Do not use outside knowledge.
Do not invent facts.

Sentiment definitions:

positive:
The article presents developments that are clearly
favorable to the monitored company, such as growth,
expansion, successful launches, partnerships,
recognition, financial improvement, or other
beneficial developments.

negative:
The article presents developments that are clearly
unfavorable to the monitored company, such as
security incidents, legal or regulatory problems,
financial losses, operational failures, layoffs,
reputational damage, or other harmful developments.

neutral:
The article is primarily factual, balanced,
uncertain, mixed, or does not clearly indicate
a positive or negative effect on the monitored company.

The score represents confidence in the selected
sentiment label:
0.0 = very uncertain
1.0 = extremely confident

COMPANY CONTEXT:
{company_text}

ARTICLE TITLE:
{article.title}

ARTICLE SOURCE:
{article.source_name}

ARTICLE CONTENT:
{article_text}

Return ONLY valid JSON with exactly these fields:

{{
  "label": "positive | neutral | negative",
  "score": 0.0,
  "reason": "Short factual explanation grounded in the article."
}}

Rules:
- Analyze sentiment specifically toward
  "{company_context.company_name}".
- Choose exactly one label.
- score must be between 0.0 and 1.0.
- Keep reason concise and factual.
- Do not include unsupported claims.
- Do not include Markdown.
- Do not include code fences.
- Do not include text before or after the JSON.
""".strip()
