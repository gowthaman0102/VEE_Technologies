from app.models.article import Article
from app.services.company_semantic_context_service import (
    CompanySemanticContext,
)


def build_article_business_impact_prompt(
    article: Article,
    company_context: CompanySemanticContext,
) -> str:
    article_text = (
        article.cleaned_content or ""
    ).strip()

    if not article_text:
        raise ValueError(
            "Article cleaned content is required "
            "for business impact analysis."
        )

    company_text = (
        company_context.text or ""
    ).strip()

    if not company_text:
        raise ValueError(
            "Company semantic context is required "
            "for business impact analysis."
        )

    return f"""
You are a media intelligence business impact analyst.

Analyze the supplied news article specifically for its
business impact on the monitored company.

Use only:
1. the supplied company context,
2. the supplied article.

Do not use outside knowledge.
Do not invent facts.

Allowed impact categories:

financial:
Revenue, profit, cost, funding, investment, valuation,
financial performance, or financial exposure.

operational:
Business operations, capacity, workforce, delivery,
facilities, processes, continuity, or execution.

legal:
Lawsuits, legal disputes, court matters, contracts,
legal liability, or legal obligations.

regulatory:
Government rules, regulator actions, compliance,
licenses, approvals, or regulatory exposure.

cybersecurity:
Security breaches, cyberattacks, data compromise,
vulnerabilities, or information-security concerns.

reputation:
Brand image, public trust, media perception,
credibility, or reputational consequences.

customer:
Customer experience, customer demand, retention,
service quality, satisfaction, or customer impact.

product:
Products, services, launches, features, quality,
innovation, or product/service changes.

market:
Market demand, expansion, industry conditions,
market share, geography, or sector developments.

competitive:
Competitor activity, competitive pressure,
relative positioning, differentiation,
or competitive advantage.

Choose all categories that are directly supported by
the supplied article.

primary_category must be the single most important
supported business impact category.

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
  "primary_category": "financial | operational | legal | regulatory | cybersecurity | reputation | customer | product | market | competitive",
  "categories": [
    "one or more supported categories"
  ],
  "impact_summary": "Concise factual explanation of the business impact on the monitored company.",
  "evidence": [
    "Specific factual evidence from the supplied article."
  ]
}}

Rules:
- Analyze impact specifically on
  "{company_context.company_name}".
- Include only categories directly supported by the article.
- primary_category must also appear in categories.
- Do not assign a numeric risk score.
- Do not infer unsupported financial or business metrics.
- evidence must contain factual claims from the article.
- Keep impact_summary concise and business-focused.
- Do not include Markdown.
- Do not include code fences.
- Do not include text before or after the JSON.
""".strip()
