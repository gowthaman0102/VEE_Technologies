from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.monitoring_priority_service import (
    resolve_monitoring_priority,
)


@pytest.mark.asyncio
async def test_resolves_configured_priority():
    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = (
        SimpleNamespace(
            topic="Regulatory Action",
            priority="high",
        )
    )

    db.execute.return_value = execute_result

    result = await resolve_monitoring_priority(
        db,
        company_id=1,
        event_type="regulatory_action",
    )

    assert result.company_id == 1
    assert result.event_type == "regulatory_action"
    assert result.monitoring_topic == (
        "Regulatory Action"
    )
    assert result.priority == "high"
    assert result.source == "configured"

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_uses_fallback_for_unmapped_event():
    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    result = await resolve_monitoring_priority(
        db,
        company_id=1,
        event_type="financial_performance",
    )

    assert result.monitoring_topic == (
        "Financial Performance"
    )
    assert result.priority == "medium"
    assert result.source == "fallback"

    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_uses_fallback_when_topic_missing():
    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None

    db.execute.return_value = execute_result

    result = await resolve_monitoring_priority(
        db,
        company_id=1,
        event_type="service_outage",
    )

    assert result.monitoring_topic == (
        "Service Outage"
    )
    assert result.priority == "medium"
    assert result.source == "fallback"


@pytest.mark.asyncio
async def test_normalizes_configured_priority():
    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = (
        SimpleNamespace(
            topic="Leadership Change",
            priority="  HIGH  ",
        )
    )

    db.execute.return_value = execute_result

    result = await resolve_monitoring_priority(
        db,
        company_id=1,
        event_type="leadership_change",
    )

    assert result.priority == "high"
    assert result.source == "configured"
