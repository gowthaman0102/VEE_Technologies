import re

from app.schemas.article_triage import ArticleTriageResult


def _normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def validate_triage_grounding(
    *,
    article_content: str,
    triage: ArticleTriageResult,
) -> None:
    normalized_article = _normalize(
        article_content
    )

    if not normalized_article:
        raise ValueError(
            "Article content is required for grounding validation."
        )

    if not triage.evidence:
        raise ValueError(
            "Triage evidence cannot be empty."
        )

    grounded_count = 0

    for evidence in triage.evidence:
        normalized_evidence = _normalize(
            evidence
        )

        if not normalized_evidence:
            continue

        evidence_words = {
            word
            for word in re.findall(
                r"[a-z0-9]+",
                normalized_evidence,
            )
            if len(word) >= 4
        }

        article_words = set(
            re.findall(
                r"[a-z0-9]+",
                normalized_article,
            )
        )

        if not evidence_words:
            continue

        overlap = (
            len(
                evidence_words
                & article_words
            )
            / len(evidence_words)
        )

        if overlap >= 0.6:
            grounded_count += 1

    if grounded_count == 0:
        raise ValueError(
            "Triage evidence is not sufficiently grounded "
            "in the primary article."
        )
