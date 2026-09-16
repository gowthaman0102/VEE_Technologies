from datetime import datetime, timedelta, timezone

import pytest

from app.services.analytics_service import (
    validate_time_window,
)


def test_validate_time_window_rejects_invalid_range():
    start = datetime.now(timezone.utc)
    end = start - timedelta(days=1)

    with pytest.raises(ValueError, match="start.*end|end.*start"):
        validate_time_window(start, end)


def test_validate_time_window_accepts_valid_range():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    end = now - timedelta(days=2)

    validated_start, validated_end = validate_time_window(start, end)

    assert validated_start == start
    assert validated_end == end
