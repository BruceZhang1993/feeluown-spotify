# feeluown-spotify

[English](README.md) | [中文](README_zh.md)

[![Tests](https://github.com/BruceZhang1993/feeluown-spotify/actions/workflows/test.yml/badge.svg)](https://github.com/BruceZhang1993/feeluown-spotify/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/BruceZhang1993/feeluown-spotify/branch/main/graph/badge.svg)](https://codecov.io/gh/BruceZhang1993/feeluown-spotify)
[![PyPI](https://img.shields.io/pypi/v/feeluown-spotify)](https://pypi.org/project/feeluown-spotify/)
[![Python](https://img.shields.io/pypi/pyversions/feeluown-spotify)](https://pypi.org/project/feeluown-spotify/)
[![License](https://img.shields.io/github/license/BruceZhang1993/feeluown-spotify)](LICENSE)

[FeelUOwn](https://github.com/feeluown/feeluown) 音乐播放器的 Spotify 音频源插件。

## ⚠️ 法律声明

**本项目使用非官方 Spotify API，与 Spotify AB 及其任何子公司无关联、无背书、无合作关系。**

使用本软件即表示您理解并同意以下条款：

1. **违反服务条款的风险**：本插件依赖 [spotapi](https://pypi.org/project/spotapi/)，该库通过 **Spotify 未授权的方式** 与 Spotify 的私有/内部 API 进行交互。使用本软件可能违反 [Spotify 服务条款](https://www.spotify.com/legal/end-user-agreement/)，并可能导致您的 **Spotify 账户被暂停或永久封禁**。

2. **免责声明**：本软件按"原样"提供，不附带任何形式的明示或暗示担保。作者和贡献者 **不对任何损害承担责任**，包括但不限于数据丢失、账户封禁或因使用本软件而产生的任何其他后果。

3. **仅限教育和研究目的**：本项目仅用于 **教育和研究目的**，旨在演示如何构建音乐播放器插件以及探索音乐平台 API。不应用于商业用途或绕过任何数字版权管理（DRM）保护措施。

4. **用户责任**：您需对使用本软件的行为 **负全部责任**，**使用风险自担**。开发者强烈建议使用 **备用或临时 Spotify 账户**，而非您的主账户。

5. **合规声明**：本项目 **不会** 存储、再分发或修改任何受版权保护的音乐内容。本项目 **不会** 绕过 DRM 或允许未经授权下载受版权保护的材料。

6. **Spotify Premium**：本插件的部分功能可能需要 **Spotify Premium** 订阅。免费用户可能功能受限。

如果您不同意以上条款，**请勿使用本软件**。

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

本项目基于 [GNU 通用公共许可证 v3.0 或更高版本](LICENSE) 授权。

```
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```
