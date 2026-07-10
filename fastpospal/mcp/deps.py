from __future__ import annotations

import os
from functools import lru_cache

from fastpospal.client import PospalClient
from fastpospal.openapi import PospalOpenApiClient
from fastpospal.service import PospalService
from fastpospal.semantic.service import PospalSemanticService


@lru_cache(maxsize=1)
def get_service() -> PospalService:
    account = os.environ.get("POSPAL_ACCOUNT", "")
    password = os.environ.get("POSPAL_PASSWORD", "")
    if not account or not password:
        raise RuntimeError("请设置环境变量 POSPAL_ACCOUNT 和 POSPAL_PASSWORD")
    client = PospalClient(account=account, password=password)
    client.login()
    return PospalService(client)


@lru_cache(maxsize=1)
def get_semantic() -> PospalSemanticService:
    return PospalSemanticService(get_service())


@lru_cache(maxsize=1)
def get_openapi() -> PospalOpenApiClient | None:
    app_id = os.environ.get("POSPAL_APP_ID")
    app_key = os.environ.get("POSPAL_APP_KEY")
    if not app_id or not app_key:
        return None
    host = os.environ.get("POSPAL_OPENAPI_HOST", "https://area-openapi.pospal.cn")
    return PospalOpenApiClient(app_id, app_key, host=host)
