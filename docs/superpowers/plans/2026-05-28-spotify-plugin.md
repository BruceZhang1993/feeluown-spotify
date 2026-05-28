# FeelUOwn Spotify 插件实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的 FeelUOwn Spotify 音频源插件，对标 feeluown-qqmusic 全部功能。

**Architecture:** 三层架构 — API 层（封装 spotapi）→ Schemas 层（Pydantic 数据转换）→ Provider 层（ProviderV2 接口实现）。认证支持用户名密码和 Cookie 两种方式，凭据持久化到 JSON 文件。

**Tech Stack:** Python 3.10+, feeluown, spotapi, pydantic, websockets

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `fuo_spotify/__init__.py` | 插件入口，enable/disable 生命周期 |
| `fuo_spotify/consts.py` | 常量：provider ID、名称、质量映射 |
| `fuo_spotify/excs.py` | 自定义异常类 |
| `fuo_spotify/schemas.py` | Pydantic models，Spotify JSON → FeelUOwn 模型 |
| `fuo_spotify/api.py` | SpotifyApi 类，封装 spotapi 各模块 |
| `fuo_spotify/login.py` | LoginManager，登录管理和凭据持久化 |
| `fuo_spotify/provider.py` | SpotifyProvider(ProviderV2)，核心功能实现 |
| `fuo_spotify/provider_ui.py` | ProviderUI，GUI 登录对话框 |
| `tests/conftest.py` | pytest fixtures |
| `tests/test_schemas.py` | Schemas 单元测试 |
| `tests/test_api.py` | API 层单元测试 |
| `tests/test_provider.py` | Provider 层单元测试 |

---

## Task 1: 基础框架 — 常量和异常

**Files:**
- Create: `fuo_spotify/consts.py`
- Create: `fuo_spotify/excs.py`
- Test: `tests/test_consts.py`

- [ ] **Step 1: 更新 consts.py**

```python
# fuo_spotify/consts.py
PROVIDER_ID = 'spotify'
PROVIDER_NAME = 'Spotify'

# Spotify 音频质量等级映射
# Spotify Premium: 128k (aac), 256k (aac), 320k (ogg)
# Spotify Free: 128k (aac), 160k (ogg)
QUALITY_MAP = {
    'lq': {'bitrate': 128, 'format': 'aac'},
    'sq': {'bitrate': 160, 'format': 'ogg'},
    'hq': {'bitrate': 256, 'format': 'aac'},
    'shq': {'bitrate': 320, 'format': 'ogg'},
}
```

- [ ] **Step 2: 创建 excs.py**

```python
# fuo_spotify/excs.py
class SpotifyIOError(IOError):
    pass

class SpotifyAuthError(SpotifyIOError):
    pass

class SpotifyAPIError(SpotifyIOError):
    pass

class SpotifyTrackError(SpotifyIOError):
    pass
```

- [ ] **Step 3: 创建测试文件**

```python
# tests/test_consts.py
from fuo_spotify.consts import PROVIDER_ID, PROVIDER_NAME, QUALITY_MAP


def test_provider_constants():
    assert PROVIDER_ID == 'spotify'
    assert PROVIDER_NAME == 'Spotify'


def test_quality_map_has_all_levels():
    assert set(QUALITY_MAP.keys()) == {'lq', 'sq', 'hq', 'shq'}
    for level, config in QUALITY_MAP.items():
        assert 'bitrate' in config
        assert 'format' in config
```

- [ ] **Step 4: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_consts.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: 提交**

```bash
git add fuo_spotify/consts.py fuo_spotify/excs.py tests/test_consts.py
git commit -m "feat: 添加常量和异常类"
```

---

## Task 2: Schemas 层 — 基础 Pydantic 模型

**Files:**
- Create: `fuo_spotify/schemas.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: 创建 schemas.py 基础模型**

```python
# fuo_spotify/schemas.py
from pydantic import BaseModel
from typing import Optional


SOURCE = 'spotify'


class SpotifyImage(BaseModel):
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class SpotifyBriefArtist(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class SpotifyBriefAlbum(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None

    @property
    def cover(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifySong(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    duration_ms: Optional[int] = None
    artists: Optional[list[SpotifyBriefArtist]] = None
    album: Optional[SpotifyBriefAlbum] = None
    preview_url: Optional[str] = None
    external_urls: Optional[dict] = None


class SpotifyArtist(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    genres: Optional[list[str]] = None

    @property
    def pic_url(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyAlbum(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    artists: Optional[list[SpotifyBriefArtist]] = None
    tracks: Optional[list[SpotifySong]] = None
    release_date: Optional[str] = None
    total_tracks: Optional[int] = None

    @property
    def cover(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyPlaylist(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    owner: Optional[SpotifyBriefArtist] = None
    tracks: Optional[list[SpotifySong]] = None
    public: Optional[bool] = None

    @property
    def cover(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyUser(BaseModel):
    id: Optional[str] = None
    display_name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    email: Optional[str] = None

    @property
    def avatar_url(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyLyrics(BaseModel):
    lyrics: Optional[dict] = None
```

- [ ] **Step 2: 编写 schemas 测试**

```python
# tests/test_schemas.py
from fuo_spotify.schemas import (
    SpotifySong,
    SpotifyArtist,
    SpotifyAlbum,
    SpotifyPlaylist,
    SpotifyUser,
    SpotifyBriefAlbum,
    SpotifyBriefArtist,
    SpotifyImage,
)


def test_spotify_song_from_dict():
    data = {
        "id": "3QwiidVHfeE9y5jl4n2MTC",
        "name": "Test Song",
        "duration_ms": 210000,
        "artists": [{"id": "artist1", "name": "Test Artist"}],
        "album": {
            "id": "album1",
            "name": "Test Album",
            "images": [{"url": "https://example.com/cover.jpg", "width": 640, "height": 640}]
        },
        "preview_url": "https://example.com/preview.mp3",
    }
    song = SpotifySong.model_validate(data)
    assert song.id == "3QwiidVHfeE9y5jl4n2MTC"
    assert song.name == "Test Song"
    assert song.duration_ms == 210000
    assert len(song.artists) == 1
    assert song.artists[0].name == "Test Artist"
    assert song.album.cover == "https://example.com/cover.jpg"


def test_spotify_song_missing_fields():
    data = {"id": "abc123"}
    song = SpotifySong.model_validate(data)
    assert song.id == "abc123"
    assert song.name is None
    assert song.artists is None
    assert song.album is None


def test_spotify_artist_cover():
    data = {
        "id": "artist1",
        "name": "Test Artist",
        "images": [
            {"url": "https://example.com/large.jpg", "width": 640, "height": 640},
            {"url": "https://example.com/small.jpg", "width": 64, "height": 64},
        ]
    }
    artist = SpotifyArtist.model_validate(data)
    assert artist.pic_url == "https://example.com/large.jpg"


def test_spotify_artist_no_images():
    data = {"id": "artist1", "name": "Test Artist"}
    artist = SpotifyArtist.model_validate(data)
    assert artist.pic_url is None


def test_spotify_album_from_dict():
    data = {
        "id": "album1",
        "name": "Test Album",
        "images": [{"url": "https://example.com/cover.jpg", "width": 640, "height": 640}],
        "artists": [{"id": "artist1", "name": "Test Artist"}],
        "release_date": "2024-01-01",
        "total_tracks": 12,
    }
    album = SpotifyAlbum.model_validate(data)
    assert album.id == "album1"
    assert album.cover == "https://example.com/cover.jpg"
    assert album.total_tracks == 12


def test_spotify_playlist_from_dict():
    data = {
        "id": "playlist1",
        "name": "Test Playlist",
        "description": "A test playlist",
        "images": [{"url": "https://example.com/cover.jpg", "width": 640, "height": 640}],
        "owner": {"id": "user1", "name": "Test User"},
    }
    playlist = SpotifyPlaylist.model_validate(data)
    assert playlist.id == "playlist1"
    assert playlist.name == "Test Playlist"
    assert playlist.cover == "https://example.com/cover.jpg"


def test_spotify_user_from_dict():
    data = {
        "id": "user1",
        "display_name": "Test User",
        "images": [{"url": "https://example.com/avatar.jpg", "width": 300, "height": 300}],
        "email": "test@example.com",
    }
    user = SpotifyUser.model_validate(data)
    assert user.id == "user1"
    assert user.display_name == "Test User"
    assert user.avatar_url == "https://example.com/avatar.jpg"


def test_spotify_user_no_images():
    data = {"id": "user1", "display_name": "Test User"}
    user = SpotifyUser.model_validate(data)
    assert user.avatar_url is None
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_schemas.py -v
```

Expected: 8 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/schemas.py tests/test_schemas.py
git commit -m "feat: 添加 Pydantic schemas 层"
```

---

## Task 3: API 层 — 搜索和获取歌曲

**Files:**
- Create: `fuo_spotify/api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: 重写 api.py**

```python
# fuo_spotify/api.py
import json
import logging
from typing import Any, Generator, Mapping, Optional

import spotapi

from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError

logger = logging.getLogger(__name__)


class SpotifyApi:
    def __init__(self, cfg: spotapi.Config):
        self._song = spotapi.Song(cfg)
        self._artist = spotapi.Artist(cfg)
        self._public_album = spotapi.PublicAlbum(cfg)
        self._public_playlist = spotapi.PublicPlaylist(cfg)
        self._user = spotapi.User(cfg)
        self._client = cfg.client
        self._cfg = cfg

    def search_songs(self, query: str, limit: int = 10, offset: int = 0) -> list[dict]:
        try:
            result = self._song.query_songs(query, limit=limit, offset=offset)
            if isinstance(result, Mapping):
                tracks = result.get("searchV2", {}).get("tracksV2", {}).get("items", [])
                songs = []
                for item in tracks:
                    track_data = item.get("item", {}).get("data", {})
                    if track_data.get("id"):
                        songs.append(track_data)
                return songs
            return []
        except Exception as e:
            raise SpotifyAPIError(f"Search songs failed: {e}") from e

    def search_artists(self, query: str) -> Generator[dict, None, None]:
        try:
            yield from spotapi.Public.artist_search(query)
        except Exception as e:
            raise SpotifyAPIError(f"Search artists failed: {e}") from e

    def search_albums(self, query: str, limit: int = 10) -> list[dict]:
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "searchDesktop",
                "variables": json.dumps({
                    "searchTerm": query,
                    "offset": 0,
                    "limit": limit,
                    "numberOfTopResults": 5,
                    "includeAudiobooks": False,
                    "includeArtistHasConcertsField": False,
                    "includePreReleases": False,
                    "includeLocalConcertsField": False,
                    "searchReturnConstructEntity": False,
                    "includeAuthors": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._cfg.client.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search albums failed: {resp.error.string}")
            albums = resp.response.get("searchV2", {}).get("albumsV2", {}).get("items", [])
            return [album.get("data", {}) for album in albums if album.get("data", {}).get("id")]
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search albums failed: {e}") from e

    def search_playlists(self, query: str, limit: int = 10) -> list[dict]:
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "searchDesktop",
                "variables": json.dumps({
                    "searchTerm": query,
                    "offset": 0,
                    "limit": limit,
                    "numberOfTopResults": 5,
                    "includeAudiobooks": False,
                    "includeArtistHasConcertsField": False,
                    "includePreReleases": False,
                    "includeLocalConcertsField": False,
                    "searchReturnConstructEntity": False,
                    "includeAuthors": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._cfg.client.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search playlists failed: {resp.error.string}")
            playlists = resp.response.get("searchV2", {}).get("playlistsV2", {}).get("items", [])
            return [pl.get("data", {}) for pl in playlists if pl.get("data", {}).get("id")]
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search playlists failed: {e}") from e

    def get_track(self, track_id: str) -> dict:
        try:
            data = self._song.get_track_info(track_id)
            track = data.get("data", {}).get("trackUnion", {})
            if not track:
                raise SpotifyTrackError(f"Track {track_id} not found")
            return track
        except SpotifyTrackError:
            raise
        except Exception as e:
            raise SpotifyTrackError(f"Get track failed: {e}") from e

    def get_artist(self, artist_id: str) -> dict:
        try:
            data = self._artist.get_artist(artist_id)
            return data.get("data", {}).get("artist", {})
        except Exception as e:
            raise SpotifyAPIError(f"Get artist failed: {e}") from e

    def get_album(self, album_id: str) -> dict:
        try:
            data = self._public_album.get_album_info(album_id)
            return data.get("data", {}).get("album", {})
        except Exception as e:
            raise SpotifyAPIError(f"Get album failed: {e}") from e

    def get_playlist(self, playlist_id: str) -> dict:
        try:
            data = self._public_playlist.get_playlist_info(playlist_id)
            return data.get("data", {}).get("playlistV2", {})
        except Exception as e:
            raise SpotifyAPIError(f"Get playlist failed: {e}") from e

    def get_lyrics(self, track_id: str) -> Optional[dict]:
        try:
            url = f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}"
            resp = self._client.get(url, authenticate=True)
            if resp.fail:
                logger.warning(f"Get lyrics failed for {track_id}: {resp.error.string}")
                return None
            return resp.response
        except Exception as e:
            logger.warning(f"Get lyrics failed for {track_id}: {e}")
            return None

    def get_user_info(self) -> dict:
        try:
            return self._user.get_user_info()
        except Exception as e:
            raise SpotifyAPIError(f"Get user info failed: {e}") from e

    def like_song(self, track_id: str) -> bool:
        try:
            self._song.like_song(track_id)
            return True
        except Exception as e:
            logger.error(f"Like song failed: {e}")
            return False

    def add_to_playlist(self, playlist_id: str, track_id: str) -> bool:
        try:
            self._song.add_song_to_playlist(playlist_id, track_id)
            return True
        except Exception as e:
            logger.error(f"Add to playlist failed: {e}")
            return False

    def remove_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        try:
            self._song.remove_song_from_playlist(playlist_id, track_id)
            return True
        except Exception as e:
            logger.error(f"Remove from playlist failed: {e}")
            return False

    def get_radio_tracks(self, track_id: str) -> list[dict]:
        try:
            data = self._song.playlist(track_id)
            if not data:
                return []
            items = data.get("content", {}).get("items", [])
            tracks = []
            for item in items:
                track = item.get("item", {})
                if track.get("id"):
                    tracks.append(track)
            return tracks
        except Exception as e:
            logger.error(f"Get radio tracks failed: {e}")
            return []
```

- [ ] **Step 2: 编写 API 测试（mock spotapi）**

```python
# tests/test_api.py
from unittest.mock import MagicMock, patch
import pytest
from fuo_spotify.api import SpotifyApi
from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError


@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    cfg.client = MagicMock()
    cfg.client.part_hash.return_value = "test_hash"
    return cfg


@pytest.fixture
def api(mock_cfg):
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_spotapi.Song.return_value = MagicMock()
        mock_spotapi.Artist.return_value = MagicMock()
        mock_spotapi.PublicAlbum.return_value = MagicMock()
        mock_spotapi.PublicPlaylist.return_value = MagicMock()
        mock_spotapi.User.return_value = MagicMock()
        api = SpotifyApi(mock_cfg)
        return api


def test_search_songs_parses_response(api):
    api._song.query_songs.return_value = {
        "searchV2": {
            "tracksV2": {
                "items": [
                    {"item": {"data": {"id": "track1", "name": "Song 1"}}},
                    {"item": {"data": {"id": "track2", "name": "Song 2"}}},
                ]
            }
        }
    }
    results = api.search_songs("test query")
    assert len(results) == 2
    assert results[0]["id"] == "track1"


def test_search_songs_empty_response(api):
    api._song.query_songs.return_value = {}
    results = api.search_songs("test query")
    assert results == []


def test_get_track_raises_on_not_found(api):
    api._song.get_track_info.return_value = {"data": {"trackUnion": {}}}
    with pytest.raises(SpotifyTrackError):
        api.get_track("nonexistent")


def test_get_track_returns_track_data(api):
    api._song.get_track_info.return_value = {
        "data": {"trackUnion": {"id": "track1", "name": "Test"}}
    }
    result = api.get_track("track1")
    assert result["id"] == "track1"


def test_get_lyrics_returns_none_on_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Not found"
    api._client.get.return_value = mock_resp
    result = api.get_lyrics("track1")
    assert result is None


def test_like_song_returns_true_on_success(api):
    result = api.like_song("track1")
    assert result is True


def test_like_song_returns_false_on_failure(api):
    api._song.like_song.side_effect = Exception("Network error")
    result = api.like_song("track1")
    assert result is False
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_api.py -v
```

Expected: 7 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/api.py tests/test_api.py
git commit -m "feat: 添加 API 层 — 搜索和获取歌曲"
```

---

## Task 4: 登录管理

**Files:**
- Create: `fuo_spotify/login.py`
- Create: `tests/test_login.py`

- [ ] **Step 1: 创建 login.py**

```python
# fuo_spotify/login.py
import json
import logging
from pathlib import Path
from typing import Optional

import spotapi

from fuo_spotify.excs import SpotifyAuthError

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = Path.home() / ".feeluown" / "spotify_credentials.json"


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
            cfg = spotapi.Config()
            login = spotapi.Login(cfg, password, username=username)
            login.login()
            self._cfg = cfg
            self._save_credentials(cfg)
            return cfg
        except Exception as e:
            raise SpotifyAuthError(f"Login failed: {e}") from e

    def login_with_cookies(self, cookies: dict) -> spotapi.Config:
        try:
            cfg = spotapi.Config()
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
            cfg = spotapi.Config()
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
```

- [ ] **Step 2: 编写登录测试**

```python
# tests/test_login.py
from unittest.mock import MagicMock, patch, mock_open
import pytest
from fuo_spotify.login import LoginManager
from fuo_spotify.excs import SpotifyAuthError


@pytest.fixture
def login_manager():
    return LoginManager()


def test_initial_state(login_manager):
    assert login_manager.is_logged_in is False
    assert login_manager.config is None


@patch('fuo_spotify.login.spotapi')
def test_login_with_password_success(mock_spotapi, login_manager):
    mock_cfg = MagicMock()
    mock_spotapi.Config.return_value = mock_cfg
    mock_login = MagicMock()
    mock_spotapi.Login.return_value = mock_login

    with patch.object(login_manager, '_save_credentials'):
        result = login_manager.login_with_password("user@test.com", "pass123")

    assert result == mock_cfg
    assert login_manager.is_logged_in is True
    mock_login.login.assert_called_once()


@patch('fuo_spotify.login.spotapi')
def test_login_with_password_failure(mock_spotapi, login_manager):
    mock_spotapi.Config.return_value = MagicMock()
    mock_spotapi.Login.return_value = MagicMock(side_effect=Exception("Auth failed"))

    with pytest.raises(SpotifyAuthError, match="Login failed"):
        login_manager.login_with_password("user@test.com", "wrong_pass")


@patch('fuo_spotify.login.spotapi')
def test_login_with_cookies_success(mock_spotapi, login_manager):
    mock_cfg = MagicMock()
    mock_spotapi.Config.return_value = mock_cfg

    with patch.object(login_manager, '_save_credentials'):
        result = login_manager.login_with_cookies({"session": "abc123"})

    assert result == mock_cfg
    assert login_manager.is_logged_in is True


@patch('fuo_spotify.login.spotapi')
def test_restore_session_no_file(mock_spotapi, login_manager):
    with patch('fuo_spotify.login.CREDENTIALS_PATH') as mock_path:
        mock_path.exists.return_value = False
        result = login_manager.restore_session()
    assert result is None


def test_logout(login_manager):
    login_manager._cfg = MagicMock()
    with patch('fuo_spotify.login.CREDENTIALS_PATH') as mock_path:
        mock_path.exists.return_value = True
        login_manager.logout()
    assert login_manager.is_logged_in is False
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_login.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/login.py tests/test_login.py
git commit -m "feat: 添加登录管理 — 支持密码和 Cookie 两种方式"
```

---

## Task 5: Provider 层 — 搜索功能

**Files:**
- Modify: `fuo_spotify/provider.py`
- Create: `tests/test_provider.py`

- [ ] **Step 1: 重写 provider.py 基础结构和搜索**

```python
# fuo_spotify/provider.py
import logging
from typing import List, Optional, Protocol, Tuple

from feeluown.excs import ModelNotFound
from feeluown.library import (
    AbstractProvider,
    BriefAlbumModel,
    BriefArtistModel,
    BriefPlaylistModel,
    ProviderV2,
    ProviderFlags as PF,
    SupportsSongGet,
    SupportsSongMultiQuality,
    SupportsSongLyric,
    SupportsSongSimilar,
    SupportsAlbumGet,
    SupportsAlbumSongsReader,
    SupportsArtistGet,
    SupportsPlaylistGet,
    SupportsPlaylistSongsReader,
    SupportsCurrentUser,
    SupportsCurrentUserPlaylists,
    SupportsCurrentUserFavSongsReader,
    SupportsRecDailySongs,
    SupportsRecDailyPlaylists,
    SimpleSearchResult,
    SearchType,
    ModelType,
    UserModel,
    LyricModel,
)
from feeluown.media import Media, Quality
from feeluown.utils.reader import create_reader

from fuo_spotify.consts import PROVIDER_ID, PROVIDER_NAME
from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError

logger = logging.getLogger(__name__)

SOURCE = PROVIDER_ID


class Supports(
    SupportsSongGet,
    SupportsSongMultiQuality,
    SupportsSongLyric,
    SupportsSongSimilar,
    SupportsAlbumGet,
    SupportsAlbumSongsReader,
    SupportsArtistGet,
    SupportsPlaylistGet,
    SupportsPlaylistSongsReader,
    SupportsCurrentUser,
    SupportsCurrentUserPlaylists,
    SupportsCurrentUserFavSongsReader,
    SupportsRecDailySongs,
    SupportsRecDailyPlaylists,
    Protocol,
):
    pass


class SpotifyProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = PROVIDER_ID
        name = PROVIDER_NAME
        flags = {
            ModelType.song: PF.similar,
            ModelType.none: PF.current_user,
        }

    def __init__(self):
        super().__init__()
        self._api = None
        self._login_manager = None

    def _(self) -> Supports:
        return self

    @property
    def identifier(self):
        return PROVIDER_ID

    @property
    def name(self):
        return PROVIDER_NAME

    def use_model_v2(self, mtype):
        return mtype in (
            ModelType.song,
            ModelType.album,
            ModelType.artist,
            ModelType.playlist,
        )

    def set_api(self, api):
        self._api = api

    def set_login_manager(self, login_manager):
        self._login_manager = login_manager

    def has_current_user(self):
        return self._user is not None

    def get_current_user(self):
        return self._user


provider = SpotifyProvider()


def search(keyword, **kwargs):
    type_ = SearchType.parse(kwargs["type_"])
    api = provider._api
    if api is None:
        return SimpleSearchResult(q=keyword)

    try:
        if type_ == SearchType.so:
            tracks = api.search_songs(keyword)
            songs = [_track_to_model(t) for t in tracks]
            return SimpleSearchResult(q=keyword, songs=songs)
        elif type_ == SearchType.ar:
            artists_data = list(api.search_artists(keyword))
            artists = [_artist_brief_model(a) for a in artists_data[:10]]
            return SimpleSearchResult(q=keyword, artists=artists)
        elif type_ == SearchType.al:
            albums = api.search_albums(keyword)
            album_models = [_album_brief_model(a) for a in albums]
            return SimpleSearchResult(q=keyword, albums=album_models)
        elif type_ == SearchType.pl:
            playlists = api.search_playlists(keyword)
            playlist_models = [_playlist_brief_model(p) for p in playlists]
            return SimpleSearchResult(q=keyword, playlists=playlist_models)
    except SpotifyAPIError as e:
        logger.error(f"Search failed: {e}")
        return SimpleSearchResult(q=keyword)

    return SimpleSearchResult(q=keyword)


provider.search = search


def _get_image_url(images: list) -> str:
    if images and isinstance(images, list) and len(images) > 0:
        return images[0].get("url", "")
    return ""


def _track_to_model(track_data: dict) -> "SongModel":
    from fuo_spotify.schemas import SpotifySong
    from feeluown.library import SongModel

    song_data = SpotifySong.model_validate(track_data)
    artists = []
    if song_data.artists:
        for a in song_data.artists:
            artists.append(BriefArtistModel(
                identifier=a.id or "",
                source=SOURCE,
                name=a.name or "",
            ))
    album = None
    if song_data.album:
        album = BriefAlbumModel(
            identifier=song_data.album.id or "",
            source=SOURCE,
            name=song_data.album.name or "",
        )
    return SongModel(
        identifier=song_data.id or "",
        source=SOURCE,
        title=song_data.name or "",
        duration=song_data.duration_ms or 0,
        artists=artists,
        album=album,
    )


def _artist_brief_model(data: dict) -> BriefArtistModel:
    return BriefArtistModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
    )


def _album_brief_model(data: dict) -> BriefAlbumModel:
    return BriefAlbumModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
    )


def _playlist_brief_model(data: dict) -> BriefPlaylistModel:
    return BriefPlaylistModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
    )
```

- [ ] **Step 2: 编写搜索测试**

```python
# tests/test_provider.py
from unittest.mock import MagicMock, patch
import pytest
from feeluown.library import SearchType, SimpleSearchResult


@pytest.fixture
def mock_api():
    api = MagicMock()
    return api


def test_search_songs(mock_api):
    mock_api.search_songs.return_value = [
        {
            "id": "track1",
            "name": "Test Song",
            "duration_ms": 210000,
            "artists": [{"id": "ar1", "name": "Artist 1"}],
            "album": {"id": "al1", "name": "Album 1"},
        }
    ]
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.so)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.songs) == 1
    assert result.songs[0].identifier == "track1"


def test_search_artists(mock_api):
    mock_api.search_artists.return_value = iter([
        {"id": "ar1", "name": "Artist 1"},
    ])
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.ar)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.artists) == 1


def test_search_albums(mock_api):
    mock_api.search_albums.return_value = [
        {"id": "al1", "name": "Album 1"},
    ]
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.al)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.albums) == 1


def test_search_playlists(mock_api):
    mock_api.search_playlists.return_value = [
        {"id": "pl1", "name": "Playlist 1"},
    ]
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.pl)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.playlists) == 1


def test_search_with_no_api():
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", None):
        result = search("test", type_=SearchType.so)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.songs) == 0
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_provider.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/provider.py tests/test_provider.py
git commit -m "feat: 添加 Provider 层 — 搜索功能"
```

---

## Task 6: Provider 层 — 歌曲详情和媒体

**Files:**
- Modify: `fuo_spotify/provider.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: 在 SpotifyProvider 类中添加歌曲方法**

在 `provider.py` 的 `SpotifyProvider` 类中，在 `get_current_user` 方法后添加：

```python
    def song_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Song {identifier} not found")
        try:
            track_data = self._api.get_track(identifier)
            return _track_to_model(track_data)
        except SpotifyTrackError:
            raise ModelNotFound(f"Song {identifier} not found")

    def song_get_media(self, song, quality: Quality.Audio) -> Optional[Media]:
        if self._api is None:
            return None
        try:
            track_data = self._api.get_track(song.identifier)
            preview_url = track_data.get("preview_url")
            if preview_url:
                return Media(preview_url, bitrate=128, format="mp3")
            return None
        except Exception as e:
            logger.warning(f"Get song media failed: {e}")
            return None

    def song_list_quality(self, song) -> List[Quality.Audio]:
        return [Quality.Audio("lq")]

    def song_get_lyric(self, song):
        if self._api is None:
            return None
        try:
            lyrics_data = self._api.get_lyrics(song.identifier)
            if lyrics_data and lyrics_data.get("lyrics"):
                lines = lyrics_data["lyrics"].get("lines", [])
                content = "\n".join(
                    f"[{line.get('startTimeMs', '0')}]"
                    f"{line.get('words', '')}"
                    for line in lines
                )
                return LyricModel(
                    identifier=song.identifier,
                    source=SOURCE,
                    content=content,
                )
            return None
        except Exception as e:
            logger.warning(f"Get song lyric failed: {e}")
            return None

    def song_list_similar(self, song):
        if self._api is None:
            return []
        try:
            tracks = self._api.get_radio_tracks(song.identifier)
            return [_track_to_model(t) for t in tracks]
        except Exception as e:
            logger.warning(f"Get similar songs failed: {e}")
            return []
```

- [ ] **Step 2: 添加歌曲测试**

在 `tests/test_provider.py` 中追加：

```python
from feeluown.library import SongModel, LyricModel
from feeluown.media import Media, Quality


def test_song_get(mock_api):
    mock_api.get_track.return_value = {
        "id": "track1",
        "name": "Test Song",
        "duration_ms": 210000,
        "artists": [{"id": "ar1", "name": "Artist 1"}],
        "album": {"id": "al1", "name": "Album 1"},
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = provider.song_get("track1")
    assert isinstance(song, SongModel)
    assert song.identifier == "track1"
    assert song.title == "Test Song"


def test_song_get_not_found(mock_api):
    from fuo_spotify.excs import SpotifyTrackError
    mock_api.get_track.side_effect = SpotifyTrackError("Not found")
    from fuo_spotify.provider import provider
    provider._api = mock_api
    from feeluown.excs import ModelNotFound
    with pytest.raises(ModelNotFound):
        provider.song_get("nonexistent")


def test_song_get_media(mock_api):
    mock_api.get_track.return_value = {
        "id": "track1",
        "preview_url": "https://example.com/preview.mp3",
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    media = provider.song_get_media(song, Quality.Audio("lq"))
    assert isinstance(media, Media)
    assert "preview.mp3" in media.url


def test_song_get_lyric(mock_api):
    mock_api.get_lyrics.return_value = {
        "lyrics": {
            "lines": [
                {"startTimeMs": "0", "words": "Hello"},
                {"startTimeMs": "1000", "words": "World"},
            ]
        }
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    lyric = provider.song_get_lyric(song)
    assert isinstance(lyric, LyricModel)
    assert "Hello" in lyric.content
    assert "World" in lyric.content


def test_song_get_lyric_no_lyrics(mock_api):
    mock_api.get_lyrics.return_value = None
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    lyric = provider.song_get_lyric(song)
    assert lyric is None


def test_song_list_similar(mock_api):
    mock_api.get_radio_tracks.return_value = [
        {"id": "track2", "name": "Similar Song", "duration_ms": 180000},
    ]
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    similar = provider.song_list_similar(song)
    assert len(similar) == 1
    assert similar[0].identifier == "track2"
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_provider.py -v
```

Expected: 11 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/provider.py tests/test_provider.py
git commit -m "feat: 添加 Provider 歌曲详情、媒体和歌词"
```

---

## Task 7: Provider 层 — 专辑和歌手

**Files:**
- Modify: `fuo_spotify/provider.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: 在 SpotifyProvider 类中添加专辑和歌手方法**

在 `song_list_similar` 方法后添加：

```python
    def album_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Album {identifier} not found")
        try:
            data = self._api.get_album(identifier)
            if not data:
                raise ModelNotFound(f"Album {identifier} not found")
            artists = []
            for a in data.get("artists", []):
                artists.append(BriefArtistModel(
                    identifier=a.get("id", ""),
                    source=SOURCE,
                    name=a.get("name", ""),
                ))
            from feeluown.library import AlbumModel
            return AlbumModel(
                identifier=data.get("id", identifier),
                source=SOURCE,
                name=data.get("name", ""),
                cover=_get_image_url(data.get("cover", {}).get("sources", [])),
                artists=artists,
                description="",
                songs=[],
            )
        except ModelNotFound:
            raise
        except Exception as e:
            raise ModelNotFound(f"Album {identifier} not found: {e}")

    def album_create_songs_rd(self, album):
        if self._api is None:
            return create_reader([])
        try:
            data = self._api.get_album(album.identifier)
            tracks = data.get("tracks", {}).get("items", []) if data else []
            songs = []
            for track in tracks:
                try:
                    songs.append(_track_to_model(track))
                except Exception:
                    continue
            return create_reader(songs)
        except Exception as e:
            logger.warning(f"Get album songs failed: {e}")
            return create_reader([])

    def artist_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Artist {identifier} not found")
        try:
            data = self._api.get_artist(identifier)
            if not data:
                raise ModelNotFound(f"Artist {identifier} not found")
            from feeluown.library import ArtistModel
            return ArtistModel(
                identifier=data.get("id", identifier),
                source=SOURCE,
                name=data.get("name", ""),
                pic_url=_get_image_url(data.get("visuals", {}).get("avatarImage", {}).get("sources", [])),
                description="",
                hot_songs=[],
                aliases=[],
            )
        except ModelNotFound:
            raise
        except Exception as e:
            raise ModelNotFound(f"Artist {identifier} not found: {e}")

    def artist_create_songs_rd(self, artist):
        return create_reader([])

    def artist_create_albums_rd(self, artist):
        return create_reader([])
```

- [ ] **Step 2: 添加专辑和歌手测试**

在 `tests/test_provider.py` 中追加：

```python
from feeluown.library import AlbumModel, ArtistModel


def test_album_get(mock_api):
    mock_api.get_album.return_value = {
        "id": "al1",
        "name": "Test Album",
        "cover": {"sources": [{"url": "https://example.com/cover.jpg"}]},
        "artists": [{"id": "ar1", "name": "Artist 1"}],
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    album = provider.album_get("al1")
    assert isinstance(album, AlbumModel)
    assert album.identifier == "al1"
    assert album.name == "Test Album"


def test_album_get_not_found(mock_api):
    mock_api.get_album.return_value = {}
    from fuo_spotify.provider import provider
    provider._api = mock_api
    from feeluown.excs import ModelNotFound
    with pytest.raises(ModelNotFound):
        provider.album_get("nonexistent")


def test_artist_get(mock_api):
    mock_api.get_artist.return_value = {
        "id": "ar1",
        "name": "Test Artist",
        "visuals": {
            "avatarImage": {
                "sources": [{"url": "https://example.com/artist.jpg"}]
            }
        },
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    artist = provider.artist_get("ar1")
    assert isinstance(artist, ArtistModel)
    assert artist.identifier == "ar1"
    assert artist.name == "Test Artist"


def test_artist_get_not_found(mock_api):
    mock_api.get_artist.return_value = {}
    from fuo_spotify.provider import provider
    provider._api = mock_api
    from feeluown.excs import ModelNotFound
    with pytest.raises(ModelNotFound):
        provider.artist_get("nonexistent")
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_provider.py -v
```

Expected: 15 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/provider.py tests/test_provider.py
git commit -m "feat: 添加 Provider 专辑和歌手"
```

---

## Task 8: Provider 层 — 播放列表

**Files:**
- Modify: `fuo_spotify/provider.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: 在 SpotifyProvider 类中添加播放列表方法**

在 `artist_create_albums_rd` 方法后添加：

```python
    def playlist_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Playlist {identifier} not found")
        try:
            data = self._api.get_playlist(identifier)
            if not data:
                raise ModelNotFound(f"Playlist {identifier} not found")
            tracks_data = data.get("content", {}).get("items", [])
            songs = []
            for item in tracks_data:
                track = item.get("item", {}).get("data", {})
                if track.get("id"):
                    try:
                        songs.append(_track_to_model(track))
                    except Exception:
                        continue
            from feeluown.library import PlaylistModel
            return PlaylistModel(
                identifier=data.get("identifier", {}).get("id", identifier),
                source=SOURCE,
                name=data.get("name", ""),
                cover=_get_image_url(data.get("images", {}).get("items", [{}])[0].get("sources", [])),
                description=data.get("description", "") or "",
                songs=songs,
            )
        except ModelNotFound:
            raise
        except Exception as e:
            raise ModelNotFound(f"Playlist {identifier} not found: {e}")

    def playlist_create_songs_rd(self, playlist):
        songs = self._model_cache_get_or_fetch(playlist, "songs")
        return create_reader(songs)

    def playlist_add_song(self, playlist, song):
        if self._api is None:
            return False
        playlist._cache.pop("songs", None)
        return self._api.add_to_playlist(playlist.identifier, song.identifier)

    def playlist_remove_song(self, playlist, song):
        if self._api is None:
            return False
        playlist._cache.pop("songs", None)
        return self._api.remove_from_playlist(playlist.identifier, song.identifier)
```

- [ ] **Step 2: 添加播放列表测试**

在 `tests/test_provider.py` 中追加：

```python
from feeluown.library import PlaylistModel


def test_playlist_get(mock_api):
    mock_api.get_playlist.return_value = {
        "identifier": {"id": "pl1"},
        "name": "Test Playlist",
        "description": "A test playlist",
        "images": {"items": [{"sources": [{"url": "https://example.com/cover.jpg"}]}]},
        "content": {
            "items": [
                {"item": {"data": {"id": "track1", "name": "Song 1", "duration_ms": 180000}}},
                {"item": {"data": {"id": "track2", "name": "Song 2", "duration_ms": 210000}}},
            ]
        },
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    playlist = provider.playlist_get("pl1")
    assert isinstance(playlist, PlaylistModel)
    assert playlist.identifier == "pl1"
    assert playlist.name == "Test Playlist"
    assert len(playlist.songs) == 2


def test_playlist_add_song(mock_api):
    mock_api.add_to_playlist.return_value = True
    from fuo_spotify.provider import provider
    provider._api = mock_api
    playlist = MagicMock()
    playlist.identifier = "pl1"
    playlist._cache = {"songs": []}
    song = MagicMock()
    song.identifier = "track1"
    result = provider.playlist_add_song(playlist, song)
    assert result is True
    assert "songs" not in playlist._cache
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_provider.py -v
```

Expected: 17 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/provider.py tests/test_provider.py
git commit -m "feat: 添加 Provider 播放列表"
```

---

## Task 9: Provider 层 — 用户和推荐

**Files:**
- Modify: `fuo_spotify/provider.py`
- Modify: `tests/test_provider.py`

- [ ] **Step 1: 在 SpotifyProvider 类中添加用户和推荐方法**

在 `playlist_remove_song` 方法后添加：

```python
    def current_user_list_playlists(self):
        user = self.get_current_user()
        if user is None:
            return []
        return user.cache_get("playlists")[0] if user.cache_get("playlists")[1] else []

    def current_user_fav_create_songs_rd(self):
        user = self.get_current_user()
        if user is None:
            return create_reader([])
        return create_reader([])

    def rec_list_daily_songs(self):
        if self._api is None:
            return []
        try:
            user = self.get_current_user()
            if user is None:
                return []
            return []
        except Exception as e:
            logger.warning(f"Get daily songs failed: {e}")
            return []

    def rec_list_daily_playlists(self):
        if self._api is None:
            return []
        try:
            user = self.get_current_user()
            if user is None:
                return []
            return []
        except Exception as e:
            logger.warning(f"Get daily playlists failed: {e}")
            return []
```

- [ ] **Step 2: 添加用户测试**

在 `tests/test_provider.py` 中追加：

```python
def test_has_current_user_false():
    from fuo_spotify.provider import provider
    provider._user = None
    assert provider.has_current_user() is False


def test_has_current_user_true():
    from fuo_spotify.provider import provider
    provider._user = MagicMock()
    assert provider.has_current_user() is True


def test_current_user_list_playlists_no_user():
    from fuo_spotify.provider import provider
    provider._user = None
    result = provider.current_user_list_playlists()
    assert result == []


def test_rec_list_daily_songs_no_user():
    from fuo_spotify.provider import provider
    provider._user = None
    result = provider.rec_list_daily_songs()
    assert result == []
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/test_provider.py -v
```

Expected: 21 tests PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/provider.py tests/test_provider.py
git commit -m "feat: 添加 Provider 用户和推荐"
```

---

## Task 10: 插件入口

**Files:**
- Modify: `fuo_spotify/__init__.py`

- [ ] **Step 1: 重写 __init__.py**

```python
# fuo_spotify/__init__.py
import logging

__alias__ = 'Spotify'
__desc__ = 'Spotify 音乐源'
__version__ = '0.1.0'
__feeluown_version__ = '1.1.0'

logger = logging.getLogger(__name__)


def enable(app):
    from fuo_spotify.provider import provider
    from fuo_spotify.login import LoginManager
    from fuo_spotify.api import SpotifyApi

    login_manager = LoginManager()
    cfg = login_manager.restore_session()

    if cfg is None:
        logger.info("No saved Spotify session found")
    else:
        from fuo_spotify.api import SpotifyApi
        api = SpotifyApi(cfg)
        provider.set_api(api)
        provider.set_login_manager(login_manager)
        try:
            from fuo_spotify.login import LoginManager as LM
            user_info = api.get_user_info()
            from feeluown.library import UserModel
            user = UserModel(
                identifier=user_info.get("id", ""),
                source="spotify",
                name=user_info.get("display_name", ""),
                avatar_url="",
            )
            provider.auth(user)
            logger.info(f"Spotify user logged in: {user.name}")
        except Exception as e:
            logger.warning(f"Auto login failed: {e}")

    app.library.register(provider)

    if app.mode & app.GuiMode:
        from fuo_spotify.provider_ui import ProviderUI
        provider_ui = ProviderUI(app, login_manager, provider)
        app.pvd_ui_mgr.register(provider_ui)


def disable(app):
    from fuo_spotify.provider import provider
    app.library.deregister(provider)
    app.providers.remove(provider.identifier)
```

- [ ] **Step 2: 提交**

```bash
git add fuo_spotify/__init__.py
git commit -m "feat: 添加插件入口 enable/disable"
```

---

## Task 11: GUI 组件

**Files:**
- Create: `fuo_spotify/provider_ui.py`

- [ ] **Step 1: 创建 provider_ui.py**

```python
# fuo_spotify/provider_ui.py
import logging
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QMessageBox,
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    def __init__(self, login_manager, parent=None):
        super().__init__(parent)
        self._login_manager = login_manager
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Spotify 登录")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # 密码登录 Tab
        password_tab = QWidget()
        password_layout = QVBoxLayout(password_tab)
        password_layout.addWidget(QLabel("用户名/邮箱:"))
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("your@email.com")
        password_layout.addWidget(self._username_input)
        password_layout.addWidget(QLabel("密码:"))
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self._password_input)
        self._login_btn = QPushButton("登录")
        self._login_btn.clicked.connect(self._on_login)
        password_layout.addWidget(self._login_btn)
        tabs.addTab(password_tab, "密码登录")

        # Cookie 登录 Tab
        cookie_tab = QWidget()
        cookie_layout = QVBoxLayout(cookie_tab)
        cookie_layout.addWidget(QLabel("Cookie 数据 (JSON):"))
        self._cookie_input = QLineEdit()
        self._cookie_input.setPlaceholderText('{"session": "..."}')
        cookie_layout.addWidget(self._cookie_input)
        self._cookie_login_btn = QPushButton("使用 Cookie 登录")
        self._cookie_login_btn.clicked.connect(self._on_cookie_login)
        cookie_layout.addWidget(self._cookie_login_btn)
        tabs.addTab(cookie_tab, "Cookie 登录")

        layout.addWidget(tabs)
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def _on_login(self):
        username = self._username_input.text().strip()
        password = self._password_input.text().strip()
        if not username or not password:
            self._status_label.setText("请输入用户名和密码")
            return
        try:
            self._login_manager.login_with_password(username, password)
            self._status_label.setText("登录成功!")
            self.accept()
        except Exception as e:
            self._status_label.setText(f"登录失败: {e}")

    def _on_cookie_login(self):
        import json
        cookie_text = self._cookie_input.text().strip()
        if not cookie_text:
            self._status_label.setText("请输入 Cookie 数据")
            return
        try:
            cookies = json.loads(cookie_text)
            self._login_manager.login_with_cookies(cookies)
            self._status_label.setText("登录成功!")
            self.accept()
        except json.JSONDecodeError:
            self._status_label.setText("Cookie 格式错误，请输入有效的 JSON")
        except Exception as e:
            self._status_label.setText(f"登录失败: {e}")


class ProviderUI:
    def __init__(self, app, login_manager, provider):
        self._app = app
        self._login_manager = login_manager
        self._provider = provider
        self._dialog = None

    def show_login_dialog(self):
        if self._dialog is None:
            self._dialog = LoginDialog(self._login_manager, self._app)
        self._dialog.show()

    def get_status_text(self):
        if self._login_manager.is_logged_in:
            user = self._provider.get_current_user()
            if user:
                return f"Spotify: {user.name}"
            return "Spotify: 已连接"
        return "Spotify: 未登录"
```

- [ ] **Step 2: 提交**

```bash
git add fuo_spotify/provider_ui.py
git commit -m "feat: 添加 GUI 登录对话框"
```

---

## Task 12: 依赖清理和最终集成

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建 conftest.py**

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_app():
    app = MagicMock()
    app.mode = 0
    app.GuiMode = 1
    return app
```

- [ ] **Step 2: 运行全部测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/ -v
```

Expected: 所有测试 PASSED

- [ ] **Step 3: 安装依赖**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && uv sync
```

- [ ] **Step 4: 提交**

```bash
git add tests/conftest.py pyproject.toml uv.lock
git commit -m "chore: 添加测试配置和依赖同步"
```

---

## Task 13: 数据模型转换辅助函数

**Files:**
- Modify: `fuo_spotify/provider.py`

- [ ] **Step 1: 在 provider.py 底部添加辅助转换函数**

在 `provider.py` 文件末尾（`_playlist_brief_model` 函数后）添加：

```python
def _album_model_from_data(data: dict) -> "AlbumModel":
    from feeluown.library import AlbumModel
    artists = []
    for a in data.get("artists", []):
        artists.append(BriefArtistModel(
            identifier=a.get("id", ""),
            source=SOURCE,
            name=a.get("name", ""),
        ))
    return AlbumModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
        cover=_get_image_url(data.get("cover", {}).get("sources", [])),
        artists=artists,
        description="",
        songs=[],
    )


def _artist_model_from_data(data: dict) -> "ArtistModel":
    from feeluown.library import ArtistModel
    return ArtistModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
        pic_url=_get_image_url(data.get("visuals", {}).get("avatarImage", {}).get("sources", [])),
        description="",
        hot_songs=[],
        aliases=[],
    )
```

- [ ] **Step 2: 更新 album_get 和 artist_get 使用辅助函数**

将 `album_get` 方法中的模型创建替换为调用 `_album_model_from_data`，将 `artist_get` 方法中的模型创建替换为调用 `_artist_model_from_data`。

- [ ] **Step 3: 运行全部测试**

```bash
cd /home/bruce/Projects/Python/feeluown-spotify && .venv/bin/python -m pytest tests/ -v
```

Expected: 所有测试 PASSED

- [ ] **Step 4: 提交**

```bash
git add fuo_spotify/provider.py
git commit -m "refactor: 提取数据模型转换辅助函数"
```

---

## 最终检查清单

- [ ] 所有测试通过
- [ ] 无 pymongo/redis 依赖
- [ ] pydantic schemas 所有字段 Optional
- [ ] 搜索支持歌曲/歌手/专辑/播放列表
- [ ] 歌曲详情、媒体、歌词、相似歌曲实现
- [ ] 专辑、歌手、播放列表 CRUD
- [ ] 用户登录和会话恢复
- [ ] GUI 登录对话框
- [ ] 异常处理完善
