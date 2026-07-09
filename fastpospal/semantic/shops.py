from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_SHOP_NAME_TO_ID: dict[str, str] = {
    "关天培店": "4151410",
    "4151410": "4151410",
    "山阳湖店": "4455361",
    "4455361": "4455361",
    "宙辉店": "5544638",
    "5544638": "5544638",
    "总店": "4456855",
    "4456855": "4456855",
}
DEFAULT_SHOP_ID = "4151410"


def _load_mapping() -> dict[str, str]:
    raw = os.environ.get("POSPAL_SHOP_NAME_TO_ID", "").strip()
    if not raw:
        return DEFAULT_SHOP_NAME_TO_ID
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except json.JSONDecodeError:
        pass
    return DEFAULT_SHOP_NAME_TO_ID


def shop_name_to_id(shop_name: str = "") -> str:
    mapping = _load_mapping()
    if not shop_name:
        return DEFAULT_SHOP_ID
    return mapping.get(shop_name.strip(), DEFAULT_SHOP_ID)


def resolve_shop_id(shop_names: str | None) -> int:
    shop = (shop_names or "关天培店").split(",")[0].strip()
    return int(shop_name_to_id(shop))


def resolve_shop_ids(shop_names: str | None) -> list[int]:
    if not shop_names:
        return [int(DEFAULT_SHOP_ID)]
    ids: list[int] = []
    for name in shop_names.split(","):
        name = name.strip()
        if name:
            ids.append(int(shop_name_to_id(name)))
    return ids or [int(DEFAULT_SHOP_ID)]
