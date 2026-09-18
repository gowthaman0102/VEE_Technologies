from app.services.article_relevance_gate import (
    contains_company_alias,
)


def test_openai_aliases_accept_verified_company_signals():
    assert contains_company_alias(
        aliases=["OpenAI", "OpenAI, Inc.", "OpenAI LP", "ChatGPT"],
        title="OpenAI announces a new research model",
    )
    assert contains_company_alias(
        aliases=["OpenAI", "ChatGPT"],
        title="OpenAI expands ChatGPT enterprise capabilities",
    )


def test_generic_gpt_and_ai_mentions_are_rejected():
    aliases = ["OpenAI", "OpenAI, Inc.", "OpenAI LP", "ChatGPT"]

    assert not contains_company_alias(
        aliases=aliases,
        title="A new GPT tool launches for developers",
    )
    assert not contains_company_alias(
        aliases=aliases,
        title="AI startup raises a new funding round",
    )
    assert not contains_company_alias(
        aliases=["ChatGPT"],
        title="ChatGPT update announced by an unrelated publisher",
    )