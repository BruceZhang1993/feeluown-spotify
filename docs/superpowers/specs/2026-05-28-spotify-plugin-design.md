# FeelUOwn Spotify 插件设计文档

## 概述

为 FeelUOwn 音乐播放器开发 Spotify 音频源插件，完整对标 feeluown-qqmusic 插件的功能能力。使用 spotapi 库作为 Spotify API 客户端，采用 pydantic 进行数据序列化（所有字段允许为空），遵循 FeelUOwn 的 ProviderV2 接口规范。

## 目标

- 完整对标 QQ 音乐插件的全部功能
- 支持 Spotify 用户名/密码登录和 Cookie 导入两种认证方式
- 本地播放模式：获取流 URL 后由 FeelUOwn 播放后端播放
- 数据持久化使用 JSON 文件存储
- 支持歌词显示
- 相似歌曲使用 Spotify 歌曲电台数据实现
- 音频质量跟随 Spotify 账户等级（Free/Premium）

## 架构

采用三层架构：API 层 → Schemas 层 → Provider 层，与 QQ 音乐插件保持一致。

```
fuo_spotify/
├── __init__.py       # 插件入口：enable/disable，元数据声明
├── api.py            # SpotifyApi 类：封装 spotapi 各模块，统一 API 调用
├── schemas.py        # Pydantic models：Spotify JSON → FeelUOwn 模型（所有字段 Optional）
├── provider.py       # SpotifyProvider(ProviderV2)：实现所有资源的 get/search/list
├── provider_ui.py    # ProviderUI：GUI 侧栏、登录对话框
├── login.py          # 登录管理：用户名密码 + cookie 两种方式
├── excs.py           # 自定义异常
└── consts.py         # 常量（provider ID、名称、质量映射等）
```

## 模块设计

### 1. 插件入口（__init__.py）

声明插件元数据：
- `__alias__` = `'Spotify'`
- `__desc__` = `'Spotify 音乐源'`
- `__version__` = `'0.1.0'`
- `__feeluown_version__` = `'1.1.0'`

实现生命周期方法：
- `enable(app)`：注册 provider 到 library，GUI 模式下注册 ProviderUI
- `disable(app)`：注销 provider 和 UI

### 2. API 层（api.py）

`SpotifyApi` 类是所有 Spotify 数据访问的统一入口，持有 spotapi 的各模块实例：

```python
class SpotifyApi:
    def __init__(self, cfg: spotapi.Config):
        self._song = spotapi.Song(cfg)
        self._artist = spotapi.Artist(cfg)
        self._album = spotapi.PublicAlbum(cfg)
        self._playlist = spotapi.PublicPlaylist(cfg)
        self._user = spotapi.User(cfg)
        self._public = spotapi.Public
        self._client = cfg
```

#### 核心方法

| 方法 | spotapi 调用 | 返回 |
|------|-------------|------|
| `search_songs(query, limit)` | `Song.query_songs()` | `list[dict]` |
| `search_artists(query)` | `Public.artist_search()` | `Generator` |
| `search_albums(query)` | 自定义实现 | `list[dict]` |
| `search_playlists(query)` | 自定义实现 | `list[dict]` |
| `get_track(track_id)` | `Song.get_track_info()` | `dict` |
| `get_artist(artist_id)` | `Artist.get_artist()` | `dict` |
| `get_album(album_id)` | `Public.album_info()` | `dict` |
| `get_playlist(playlist_id)` | `PublicPlaylist.get_playlist_info()` | `dict` |
| `get_lyrics(track_id)` | 自定义请求 Spotify `/color-lyrics` | `dict` |
| `get_song_url(track_id)` | 通过 track info 中的流地址 | `str` |
| `get_user_info()` | `User.get_user_info()` | `dict` |
| `like_song(track_id)` | `Song.like_song()` | `bool` |
| `add_to_playlist(playlist_id, track_id)` | `Song.add_song_to_playlist()` | `bool` |
| `remove_from_playlist(playlist_id, track_id)` | `Song.remove_song_from_playlist()` | `bool` |
| `get_radio_tracks(track_id)` | `Song.playlist()` | `list[dict]` |

#### 歌词获取

spotapi 没有内置歌词 API。通过已认证的 client 直接请求 Spotify 内部端点：
`https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}`

#### 搜索限制

spotapi 的 `Public` 只有 `song_search` 和 `artist_search`。专辑和播放列表搜索需要自行实现：
- 通过已认证的 client 请求 Spotify 的 `/v1/search` 端点，设置 `type=album` 或 `type=playlist`
- 或通过用户播放列表/收藏列表间接获取

### 3. Schemas 层（schemas.py）

使用 pydantic BaseModel 将 spotapi 返回的 JSON 映射为 FeelUOwn 模型。所有字段定义为 `Optional`，以容忍 Spotify API 返回数据的不完整性。

```python
from pydantic import BaseModel
from typing import Optional

class SpotifySong(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    artists: Optional[list] = None
    album: Optional[dict] = None
    duration_ms: Optional[int] = None
```

#### 核心 Schemas

| Schema | 目标模型 | 关键字段映射 |
|--------|---------|-------------|
| `SpotifySong` | `SongModel` | `id→identifier`, `name→title`, `artists→BriefArtistModel[]`, `album→BriefAlbumModel`, `duration_ms→duration` |
| `SpotifyArtist` | `ArtistModel` | `id→identifier`, `name→name`, `images[0].url→pic_url` |
| `SpotifyAlbum` | `AlbumModel` | `id→identifier`, `name→name`, `images[0].url→cover`, `tracks→SongModel[]` |
| `SpotifyPlaylist` | `PlaylistModel` | `id→identifier`, `name→name`, `images[0].url→cover`, `tracks→SongModel[]` |
| `SpotifyUser` | `UserModel` | `id→identifier`, `display_name→name`, `images[0].url→avatar_url` |

#### 辅助 Schemas

| Schema | 用途 |
|--------|------|
| `SpotifyBriefTrack` | 嵌套在播放列表/专辑中的简要歌曲信息 |

#### Spotify ID 特点

Spotify 使用字符串 ID（如 `3QwiidVHfeE9y5jl4n2MTC`），与 QQ 音乐的数字 ID 不同。FeelUOwn 的 `identifier` 字段支持字符串，无需特殊处理。

#### 封面 URL

Spotify 的图片是数组结构 `images[{url, width, height}]`，取第一张（最大）作为封面。

### 4. Provider 层（provider.py）

`SpotifyProvider` 实现 `ProviderV2` 接口。

#### 搜索

- `search(keyword, type)` — 支持歌曲、歌手、专辑、播放列表四种类型

#### 歌曲

- `song_get(identifier)` — 获取歌曲详情
- `song_get_media(song, quality)` — 获取播放 URL（通过 track info 中的流地址）
- `song_list_quality(song)` — 返回可用质量列表（跟随 Spotify 账户等级）
- `song_get_lyric(song)` — 获取歌词
- `song_get_mv(song)` — Spotify 不支持 MV，返回 None
- `song_list_similar(song)` — 通过 Spotify 歌曲电台获取相似歌曲

#### 播放列表

- `playlist_get(identifier)` — 获取播放列表详情及歌曲列表
- `playlist_create_songs_rd(playlist)` — 创建歌曲读取器
- `playlist_add_song(playlist, song)` / `playlist_remove_song` — 增删歌曲

#### 专辑

- `album_get(identifier)` — 获取专辑详情
- `album_create_songs_rd(album)` — 创建专辑歌曲读取器

#### 歌手

- `artist_get(identifier)` — 获取歌手详情
- `artist_create_songs_rd(artist)` — 分页获取歌手歌曲
- `artist_create_albums_rd(artist)` — 分页获取歌手专辑

#### 用户

- `has_current_user()` / `get_current_user()` — 当前登录用户
- `current_user_list_playlists()` — 用户播放列表列表
- `current_user_fav_create_songs_rd()` — 用户喜欢的歌曲

#### 推荐

- `rec_list_daily_songs()` — 每日推荐歌曲
- `rec_list_daily_playlists()` — 每日推荐播放列表

#### 不支持的功能（Spotify 平台限制）

- MV 播放
- 热评
- 电台
- 不喜欢列表

### 5. 认证与登录（login.py）

#### 方式一：用户名 + 密码登录

```python
class LoginManager:
    def login_with_password(self, username: str, password: str):
        cfg = spotapi.Config()
        login = spotapi.Login(cfg, password, username=username)
        login.login()
        self._save_credentials(cfg)
```

#### 方式二：Cookie 导入

```python
    def login_with_cookies(self, cookies: dict):
        cfg = spotapi.Config()
        login = spotapi.Login.from_cookies(cfg, cookies)
        self._save_credentials(cfg)
```

#### 凭据持久化

- 使用 `spotapi.JSONSaver` 将登录状态保存到 `~/.feeluown/spotify_credentials.json`
- 启动时自动尝试恢复登录状态
- 登录失败时提示用户重新认证

#### GUI 登录对话框（provider_ui.py）

- 提供用户名/密码输入框
- 提供 Cookie 导入文本框
- 登录状态显示（已登录/未登录/登录过期）

### 6. GUI 组件（provider_ui.py）

- 侧栏显示 Spotify 信息
- 登录对话框（用户名/密码输入、Cookie 导入）
- 登录状态显示

### 7. 异常处理（excs.py）

定义 `SpotifyIOError` 基类，派生：
- `SpotifyAuthError` — 认证失败
- `SpotifyAPIError` — API 请求失败
- `SpotifyTrackError` — 歌曲不可用

Provider 层捕获 spotapi 的异常，转换为 FeelUOwn 的 `ModelNotFound` 或自定义异常。歌词获取失败时返回空而非抛异常（优雅降级）。

### 8. 常量（consts.py）

- `PROVIDER_ID = 'spotify'`
- `PROVIDER_NAME = 'Spotify'`
- 质量等级映射常量

## 缓存策略

- 歌曲详情：使用 `model.cache_set()` 缓存 `track_id`、`preview_url` 等不变字段（与 QQ 音乐插件的 `mid` 缓存一致）
- 播放 URL：缓存到 `model.cache`，因为 Spotify 的流 URL 有时效性，设置合理 TTL

## 测试策略

- 使用 pytest（项目已有 .venv）
- Mock spotapi 调用，测试 schemas 的数据转换
- Mock API 响应，测试 provider 方法的逻辑
- 集成测试：实际调用 spotapi（需要 Spotify 账户）

## 依赖

当前 `pyproject.toml` 中的依赖：
- `feeluown>=4.1.16` — 播放器框架
- `spotapi>=1.2.7` — Spotify API 客户端
- `websockets>=16.0` — WebSocket 支持（spotapi 依赖）

可移除的依赖：
- `pymongo>=4.16.0` — 当前未使用
- `redis>=7.1.0` — 当前未使用

需要新增：
- `pydantic` — 数据序列化（所有字段 Optional，容忍 API 数据不完整）

## 实施顺序

1. 基础框架：__init__.py、consts.py、excs.py
2. API 层：api.py（封装 spotapi）
3. Schemas 层：schemas.py（数据转换）
4. 认证：login.py（登录管理）
5. Provider 层：provider.py（核心功能实现）
6. GUI：provider_ui.py（登录对话框、侧栏）
7. 测试：tests/（单元测试和集成测试）
