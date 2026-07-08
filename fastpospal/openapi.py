from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx


class PospalOpenApiClient:
    """银豹官方开放平台 API 客户端（需 appId + appKey）。"""

    def __init__(
        self,
        app_id: str,
        app_key: str,
        *,
        host: str = "https://area-openapi.pospal.cn",
    ) -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.host = host.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def _sign_v1(self, body: str) -> tuple[str, str]:
        timestamp = str(int(time.time() * 1000))
        signature = hashlib.md5((self.app_key + body).encode()).hexdigest().upper()
        return timestamp, signature

    def _sign_v3(self, body: str) -> tuple[str, str]:
        timestamp = str(int(time.time() * 1000))
        source = self.app_id + self.app_key + timestamp + body
        signature = hashlib.md5(source.encode()).hexdigest().upper()
        return timestamp, signature

    def post(self, path: str, payload: dict[str, Any], *, v3: bool = False) -> dict[str, Any]:
        body_obj = {**payload, "appId": self.app_id}
        body = json.dumps(body_obj, ensure_ascii=False, separators=(",", ":"))
        timestamp, signature = self._sign_v3(body) if v3 else self._sign_v1(body)
        headers = {
            "User-Agent": "openApi",
            "Content-Type": "application/json; charset=utf-8",
            "time-stamp": timestamp,
        }
        headers["data-signature-v3" if v3 else "data-signature"] = signature
        response = self._client.post(f"{self.host}{path}", content=body, headers=headers)
        response.raise_for_status()
        return response.json()
