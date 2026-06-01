import json
import logging
from pathlib import Path
from typing import Optional

import spotapi
from spotapi.utils.logger import Logger as SpotapiLogger

from fuo_spotify.excs import SpotifyAuthError

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = Path.home() / ".feeluown" / "spotify_credentials.json"

_AUTH_COOKIE_KEYS = {"sp_dc", "sp_key", "sp_t", "sp_gaid"}


class _NoopSolver:
    """占位 Solver，正常登录流程不需要验证码。"""

    def __init__(self, *args, **kwargs):
        pass

    def get_balance(self):
        return None

    def solve_captcha(self, *args, **kwargs):
        raise NotImplementedError("Captcha solving is not supported")


def _make_config() -> spotapi.Config:
    return spotapi.Config(solver=_NoopSolver, logger=SpotapiLogger)


# 浏览器名称 → 显示标签
BROWSER_LABELS: dict[str, str] = {
    "zen": "Zen Browser",
    "firefox": "Firefox",
    "chrome": "Chrome",
    "edge": "Edge",
    "brave": "Brave",
    "librewolf": "LibreWolf",
    "vivaldi": "Vivaldi",
}


def _get_browser_func(name: str):
    """返回指定浏览器的 cookie 提取函数（返回 CookieJar）。"""
    import browser_cookie3

    if name == "zen":
        # Zen 基于 Firefox，但配置目录在 ~/.zen
        class _Zen(browser_cookie3.FirefoxBased):
            def __init__(self, cookie_file=None,
                         domain_name="", key_file=None):
                args = {
                    "linux_data_dirs": ["~/.zen"],
                    "osx_data_dirs": [
                        "~/Library/Application Support/Zen"
                    ],
                    "windows_data_dirs": [
                        {"env": "APPDATA", "path": "Zen"},
                    ],
                }
                super().__init__(
                    "Zen", cookie_file,
                    domain_name, key_file, **args,
                )

        return lambda domain_name="": (
            _Zen(domain_name=domain_name).load()
        )
    return getattr(browser_cookie3, name, None)


def extract_browser_cookies(
    browser: Optional[str] = None,
) -> dict:
    """从本地浏览器提取 Spotify 认证 cookie。

    Args:
        browser: 浏览器名称，如 "firefox"、"zen"。
            为 None 时自动遍历常见浏览器。

    Returns:
        包含 sp_dc、sp_key、sp_t 等 key 的 dict。

    Raises:
        SpotifyAuthError: 所有浏览器均提取失败。
    """
    names = (
        [browser] if browser
        else list(BROWSER_LABELS.keys())
    )
    last_err: Optional[Exception] = None
    for name in names:
        func = _get_browser_func(name)
        if func is None:
            continue
        try:
            cj = func(domain_name=".spotify.com")
            cookies = {
                c.name: c.value
                for c in cj
                if c.name in _AUTH_COOKIE_KEYS
            }
            if "sp_dc" in cookies:
                logger.info(
                    "Extracted cookies from %s: keys=%s",
                    name,
                    list(cookies.keys()),
                )
                return cookies
        except Exception as e:
            last_err = e
            logger.debug("Extract from %s failed: %s", name, e)
            continue
    raise SpotifyAuthError(
        "无法从浏览器提取 cookie，请确认已在浏览器中登录 Spotify"
        + (f" ({last_err})" if last_err else "")
    )


def _filter_cookies(cookies: dict) -> dict:
    return {
        k: v for k, v in cookies.items()
        if k in _AUTH_COOKIE_KEYS and v.isascii()
    }


class LoginManager:
    def __init__(self):
        self._login: Optional[spotapi.Login] = None
        self._identifier: Optional[str] = None
        self._save_path = CREDENTIALS_PATH

    @property
    def login(self) -> Optional[spotapi.Login]:
        return self._login

    @property
    def is_logged_in(self) -> bool:
        return self._login is not None

    def login_with_cookies(self, identifier: str, cookies: dict) -> spotapi.Login:
        try:
            cfg = _make_config()
            filtered = _filter_cookies(cookies)
            dump = {"identifier": identifier, "cookies": filtered}
            login = spotapi.Login.from_cookies(dump, cfg)
            self._login = login
            self._identifier = identifier
            self._save_credentials(cookies)
            return login
        except Exception as e:
            raise SpotifyAuthError(f"Cookie login failed: {e}") from e

    def restore_session(self) -> Optional[spotapi.Login]:
        if not self._save_path.exists():
            return None
        try:
            with open(self._save_path, "r") as f:
                data = json.load(f)
            cfg = _make_config()
            if "cookies" in data:
                data["cookies"] = _filter_cookies(
                    data["cookies"]
                )
            else:
                # 旧格式：整个文件就是 cookies dict
                data = {
                    "identifier": "",
                    "cookies": _filter_cookies(data),
                }
            login = spotapi.Login.from_cookies(data, cfg)
            self._login = login
            self._identifier = data.get("identifier")
            return login
        except Exception as e:
            logger.warning(f"Restore session failed: {e}")
            return None

    def _save_credentials(self, cookies: dict):
        self._save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            filtered = _filter_cookies(cookies)
            data = {"identifier": self._identifier, "cookies": filtered}
            with open(self._save_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Save credentials failed: {e}")

    def logout(self):
        self._login = None
        if self._save_path.exists():
            self._save_path.unlink()
