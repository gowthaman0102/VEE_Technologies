from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.company_semantic_context_service import (
    build_company_semantic_context,
)


@pytest.mark.asyncio
async def test_build_company_semantic_context(
    monkeypatch,
):
    company = SimpleNamespace(
        id=1,
        name="PayU",
        industry="Financial Technology",
    )

    context = {
        "company_id": 1,
        "aliases": [
            SimpleNamespace(alias="PayU India"),
            SimpleNamespace(alias="PayU Payments"),
        ],
        "geographies": [
            SimpleNamespace(geography="India"),
            SimpleNamespace(geography="APAC"),
        ],
        "regulators": [
            SimpleNamespace(regulator="RBI"),
        ],
        "relationships": [
            SimpleNamespace(
                related_company_name="Prosus",
                relationship_type="parent",
            ),
            SimpleNamespace(
                related_company_name="Razorpay",
                relationship_type="competitor",
            ),
            SimpleNamespace(
                related_company_name="PhonePe",
                relationship_type="competitor",
            ),
        ],
        "monitoring_topics": [
            SimpleNamespace(
                topic="Regulatory Action",
                priority="high",
            ),
            SimpleNamespace(
                topic="Fraud and Security",
                priority="high",
            ),
            SimpleNamespace(
                topic="Leadership Change",
                priority="medium",
            ),
            SimpleNamespace(
                topic="Product Launch",
                priority="low",
            ),
        ],
    }

    company_mock = AsyncMock(
        return_value=company
    )

    context_mock = AsyncMock(
        return_value=context
    )

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company",
        company_mock,
    )

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company_context",
        context_mock,
    )

    result = await build_company_semantic_context(
        AsyncMock(),
        company_id=1,
    )

    assert result is not None
    assert result.company_id == 1
    assert result.company_name == "PayU"

    assert "Company: PayU" in result.text
    assert (
        "Industry: Financial Technology"
        in result.text
    )
    assert (
        "Aliases: PayU India, PayU Payments"
        in result.text
    )
    assert (
        "Geographies: India, APAC"
        in result.text
    )
    assert "Regulators: RBI" in result.text
    assert "parent: Prosus" in result.text
    assert "competitor: Razorpay" in result.text
    assert "competitor: PhonePe" in result.text
    assert (
        "Regulatory Action [high]"
        in result.text
    )
    assert (
        "Leadership Change [medium]"
        in result.text
    )
    assert (
        "Product Launch [low]"
        in result.text
    )

    company_mock.assert_awaited_once()
    context_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_build_company_semantic_context_missing_company(
    monkeypatch,
):
    company_mock = AsyncMock(
        return_value=None
    )

    context_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company",
        company_mock,
    )

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company_context",
        context_mock,
    )

    result = await build_company_semantic_context(
        AsyncMock(),
        company_id=999,
    )

    assert result is None
    context_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_build_company_context_handles_empty_optional_data(
    monkeypatch,
):
    company = SimpleNamespace(
        id=2,
        name="Minimal Company",
        industry=None,
    )

    context = {
        "company_id": 2,
        "aliases": [],
        "geographies": [],
        "regulators": [],
        "relationships": [],
        "monitoring_topics": [],
    }

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company",
        AsyncMock(
            return_value=company
        ),
    )

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company_context",
        AsyncMock(
            return_value=context
        ),
    )

    result = await build_company_semantic_context(
        AsyncMock(),
        company_id=2,
    )

    assert result is not None
    assert result.text == (
        "Company: Minimal Company"
    )


@pytest.mark.asyncio
async def test_build_company_context_ignores_blank_values(
    monkeypatch,
):
    company = SimpleNamespace(
        id=3,
        name="PayU",
        industry="   ",
    )

    context = {
        "company_id": 3,
        "aliases": [
            SimpleNamespace(alias=" "),
        ],
        "geographies": [
            SimpleNamespace(geography=" "),
        ],
        "regulators": [
            SimpleNamespace(regulator=" "),
        ],
        "relationships": [
            SimpleNamespace(
                related_company_name=" ",
                relationship_type="competitor",
            ),
        ],
        "monitoring_topics": [
            SimpleNamespace(
                topic=" ",
                priority="high",
            ),
        ],
    }

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company",
        AsyncMock(
            return_value=company
        ),
    )

    monkeypatch.setattr(
        "app.services.company_semantic_context_service."
        "get_company_context",
        AsyncMock(
            return_value=context
        ),
    )

    result = await build_company_semantic_context(
        AsyncMock(),
        company_id=3,
    )

    assert result is not None
    assert result.text == "Company: PayU"
