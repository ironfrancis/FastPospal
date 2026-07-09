from __future__ import annotations

from typing import Any


def ok(data: Any, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": True, "data": data, "source": "semantic"}
    payload.update(extra)
    return payload


def fail(error: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": False, "error": error, "source": "semantic"}
    payload.update(extra)
    return payload


def compact_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"headers": [], "data": [], "total": 0}
    headers = list(rows[0].keys())
    data = [[row.get(header) for header in headers] for row in rows]
    return {"headers": headers, "data": data, "total": len(rows)}
