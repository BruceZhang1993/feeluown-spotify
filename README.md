# feeluown-spotify

[![Tests](https://github.com/BruceZhang1993/feeluown-spotify/actions/workflows/test.yml/badge.svg)](https://github.com/BruceZhang1993/feeluown-spotify/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/BruceZhang1993/feeluown-spotify/branch/main/graph/badge.svg)](https://codecov.io/gh/BruceZhang1993/feeluown-spotify)
[![PyPI](https://img.shields.io/pypi/v/feeluown-spotify)](https://pypi.org/project/feeluown-spotify/)
[![Python](https://img.shields.io/pypi/pyversions/feeluown-spotify)](https://pypi.org/project/feeluown-spotify/)
[![License](https://img.shields.io/github/license/BruceZhang1993/feeluown-spotify)](LICENSE)

Spotify provider for [FeelUOwn](https://github.com/feeluown/feeluown) player.

## 功能

- 🔍 搜索歌曲、歌手、专辑、播放列表
- 🎵 歌曲详情、播放、歌词
- 📀 专辑详情和歌曲列表
- 🎤 歌手详情、歌曲和专辑
- 📋 播放列表管理（查看、添加、移除歌曲）
- 🔐 用户认证（用户名/密码 + Cookie 两种方式）
- ❤️ 收藏管理
- 🎧 每日推荐
- 🔀 相似歌曲推荐（基于 Spotify 电台）

## 安装

```bash
pip install feeluown-spotify
```

或使用 uv：

```bash
uv pip install feeluown-spotify
```

## 使用

### 登录

启动 FeelUOwn 后，通过以下方式登录 Spotify：

1. **用户名/密码登录**：在 GUI 中打开 Spotify 登录对话框，输入用户名和密码
2. **Cookie 登录**：从浏览器复制 Spotify Cookie，粘贴到登录对话框

登录凭据会自动保存到 `~/.feeluown/spotify_credentials.json`，下次启动时自动恢复。

### 搜索

在 FeelUOwn 中使用 `spotify` 前缀搜索：

```
spotify: 歌曲名
```

## 开发

### 环境准备

```bash
# 克隆项目
git clone https://github.com/BruceZhang1993/feeluown-spotify.git
cd feeluown-spotify

# 安装依赖
uv sync

# 运行测试
uv run pytest tests/ -v

# 运行测试并生成覆盖率报告
uv run pytest tests/ --cov=fuo_spotify --cov-report=html
```

### 项目结构

```
fuo_spotify/
├── __init__.py       # 插件入口，enable/disable 生命周期
├── api.py            # SpotifyApi 类，封装 spotapi 各模块
├── schemas.py        # Pydantic 数据模型，Spotify JSON → FeelUOwn 模型
├── provider.py       # SpotifyProvider(ProviderV2)，核心功能实现
├── provider_ui.py    # GUI 登录对话框
├── login.py          # 登录管理，支持密码和 Cookie 两种方式
├── excs.py           # 自定义异常类
└── consts.py         # 常量定义
```

## 技术栈

- [FeelUOwn](https://github.com/feeluown/feeluown) — 音乐播放器框架
- [spotapi](https://pypi.org/project/spotapi/) — Spotify API 客户端
- [Pydantic](https://docs.pydantic.dev/) — 数据序列化

## 许可证

[GPL-3.0-or-later](LICENSE)
