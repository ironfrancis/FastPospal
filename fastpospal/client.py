from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx

LOGIN_HOST = "https://beta.pospal.cn"
DEFAULT_SCREEN_SIZE = "1920*1080"
SESSION_FILE = Path(".pospal_session.json")


class PospalAuthError(Exception):
    """登录或会话失效。"""


class PospalApiError(Exception):
    """API 返回业务错误。"""


class PospalClient:
    """银豹云后台 Web API 客户端（基于流量逆向）。"""

    def __init__(
        self,
        account: str,
        password: str,
        *,
        login_host: str = LOGIN_HOST,
        session_file: Path | None = SESSION_FILE,
    ) -> None:
        self.account = account
        self.password = password
        self.login_host = login_host.rstrip("/")
        self.session_file = session_file
        self.store_host: str | None = None
        self.user_id: int | None = None
        self._client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PospalClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def base_url(self) -> str:
        if not self.store_host:
            raise PospalAuthError("尚未登录，请先调用 login()")
        return self.store_host

    def _save_session(self) -> None:
        if not self.session_file:
            return
        payload = {
            "account": self.account,
            "store_host": self.store_host,
            "user_id": self.user_id,
            "cookies": dict(self._client.cookies),
        }
        self.session_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    def _load_session(self) -> bool:
        if not self.session_file or not self.session_file.exists():
            return False
        try:
            payload = json.loads(self.session_file.read_text())
        except json.JSONDecodeError:
            return False
        if payload.get("account") != self.account:
            return False
        self.store_host = payload.get("store_host")
        self.user_id = payload.get("user_id")
        for name, value in (payload.get("cookies") or {}).items():
            self._client.cookies.set(name, value, domain=".pospal.cn")
        return bool(self.store_host)

    def login(self, *, force: bool = False) -> dict[str, Any]:
        """登录银豹云后台，建立跨子域会话。"""
        if not force and self._load_session():
            if self._probe_session():
                return {
                    "successed": True,
                    "store_host": self.store_host,
                    "user_id": self.user_id,
                    "from_cache": True,
                }

        self._client.get(f"{self.login_host}/account/signin")
        response = self._client.post(
            f"{self.login_host}/account/SignIn?noLog=",
            data={
                "userName": self.account,
                "password": self.password,
                "returnUrl": "",
                "screenSize": DEFAULT_SCREEN_SIZE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        )
        result = response.json()
        if not result.get("successed"):
            raise PospalAuthError(result.get("msg") or "登录失败")

        redirect = result.get("msg", "")
        parsed = urlparse(redirect)
        self.store_host = f"{parsed.scheme}://{parsed.netloc}"

        home = self._client.get(f"{self.store_host}/Dashboard")
        match = re.search(r"var currentUserId\s*=\s*(\d+)", home.text)
        if match:
            self.user_id = int(match.group(1))
        else:
            match = re.search(r'userId="(\d+)"', home.text)
            if match:
                self.user_id = int(match.group(1))

        self._save_session()
        return {
            "successed": True,
            "store_host": self.store_host,
            "user_id": self.user_id,
            "from_cache": False,
        }

    def _probe_session(self) -> bool:
        if not self.store_host:
            return False
        try:
            response = self._client.post(
                f"{self.store_host}/Category/LoadCategoryDDLJson",
                data={"userId": self.user_id or ""},
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            )
            data = response.json()
            return bool(data.get("successed"))
        except (httpx.HTTPError, json.JSONDecodeError):
            return False

    def ensure_login(self) -> None:
        if not self.store_host or not self._probe_session():
            self.login(force=True)

    def ajax_form(self, path: str, form: list[tuple[str, str]]) -> dict[str, Any]:
        """POST form-urlencoded，支持重复 key（如 userIds=1&userIds=2）。"""
        self.ensure_login()
        response = self._client.post(
            f"{self.base_url}{path}",
            content=urlencode(form, doseq=True),
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        )
        text = response.text.strip()
        if text.startswith("<"):
            raise PospalApiError(f"非 JSON 响应 ({response.status_code}): {text[:200]}")
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise PospalApiError(f"JSON 解析失败: {text[:200]}") from exc

    def ajax(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """调用云后台 AJAX 接口（POST form-urlencoded）。"""
        self.ensure_login()
        response = self._client.post(
            f"{self.base_url}{path}",
            data=data or {},
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        )
        text = response.text.strip()
        if text.startswith("<"):
            if "website.account.login.js" in text or "/Account/Signin" in text:
                self.login(force=True)
                response = self._client.post(
                    f"{self.base_url}{path}",
                    data=data or {},
                    headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                )
                text = response.text.strip()
            if text.startswith("<"):
                raise PospalApiError(f"非 JSON 响应 ({response.status_code}): {text[:200]}")
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise PospalApiError(f"JSON 解析失败: {text[:200]}") from exc

    def session_info(self) -> dict[str, Any]:
        return {
            "account": self.account,
            "store_host": self.store_host,
            "user_id": self.user_id,
            "logged_in": bool(self.store_host and self._probe_session()),
        }
