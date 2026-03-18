"""
Shared timestamp helpers for schema validation.

ASAR stores timestamps as timezone-aware UTC datetimes at every typed boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def _normalize_utc_timestamp(value: datetime) -> datetime:
    """Reject naive timestamps and normalize aware timestamps to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware and in UTC")
    return value.astimezone(timezone.utc)


UTCDateTime = Annotated[datetime, AfterValidator(_normalize_utc_timestamp)]
