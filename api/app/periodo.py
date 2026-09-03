"""Shared helper: the current usage period key (`usage.periodo`, 'YYYY-MM')."""

from datetime import UTC, datetime


def current_periodo() -> str:
    return datetime.now(UTC).strftime("%Y-%m")
