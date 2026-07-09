from __future__ import annotations

from fastpospal.semantic.categories import (
    build_categorys_json,
    flatten_categories,
    match_categories_by_keyword,
)
from fastpospal.semantic.shops import resolve_shop_id, shop_name_to_id


def test_shop_name_to_id():
    assert shop_name_to_id("关天培店") == "4151410"
    assert shop_name_to_id("") == "4151410"


def test_resolve_shop_id():
    assert resolve_shop_id("山阳湖店") == 4455361


def test_flatten_categories_flat_list():
    nodes = [
        {"uid": "1", "name": "冷饮", "parentUid": ""},
        {"uid": "2", "name": "雪糕", "parentUid": "1"},
    ]
    flat = flatten_categories(nodes)
    assert len(flat) == 2
    assert flat[1]["parent_name"] == "冷饮"


def test_match_categories_by_keyword():
    categories = [
        {"id": "1", "name": "冷饮", "parent_name": ""},
        {"id": "2", "name": "雪糕", "parent_name": "冷饮"},
    ]
    matches = match_categories_by_keyword(categories, "雪糕")
    assert len(matches) == 1
    assert matches[0]["id"] == "2"


def test_build_categorys_json():
    assert build_categorys_json([]) == "[]"
    payload = build_categorys_json(["abc"])
    assert "abc" in payload
    assert "-12345" in payload
