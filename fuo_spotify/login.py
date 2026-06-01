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
            dump = {"identifier": identifier, "cookies": cookies}
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
