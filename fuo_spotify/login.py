import json
import logging
from pathlib import Path
from typing import Optional

import spotapi
from spotapi.utils.logger import Logger as SpotapiLogger

from fuo_spotify.excs import SpotifyAuthError

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = Path.home() / ".feeluown" / "spotify_credentials.json"


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


class LoginManager:
    def __init__(self):
        self._cfg: Optional[spotapi.Config] = None
        self._save_path = CREDENTIALS_PATH

    @property
    def config(self) -> Optional[spotapi.Config]:
        return self._cfg

    @property
    def is_logged_in(self) -> bool:
        return self._cfg is not None

    def login_with_password(self, username: str, password: str) -> spotapi.Config:
        try:
            cfg = _make_config()
            login = spotapi.Login(cfg, password, username=username)
            login.login()
            self._cfg = cfg
            self._save_credentials(cfg)
            return cfg
        except Exception as e:
            raise SpotifyAuthError(f"Login failed: {e}") from e

    def login_with_cookies(self, cookies: dict) -> spotapi.Config:
        try:
            cfg = _make_config()
            spotapi.Login.from_cookies(cookies, cfg)
            self._cfg = cfg
            self._save_credentials(cfg)
            return cfg
        except Exception as e:
            raise SpotifyAuthError(f"Cookie login failed: {e}") from e

    def restore_session(self) -> Optional[spotapi.Config]:
        if not self._save_path.exists():
            return None
        try:
            with open(self._save_path, "r") as f:
                data = json.load(f)
            cfg = _make_config()
            spotapi.Login.from_cookies(data, cfg)
            self._cfg = cfg
            return cfg
        except Exception as e:
            logger.warning(f"Restore session failed: {e}")
            return None

    def _save_credentials(self, cfg: spotapi.Config):
        self._save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            cookies = cfg.client.get_cookies()
            with open(self._save_path, "w") as f:
                json.dump(cookies, f, indent=2)
        except Exception as e:
            logger.warning(f"Save credentials failed: {e}")

    def logout(self):
        self._cfg = None
        if self._save_path.exists():
            self._save_path.unlink()
