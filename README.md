# feeluown-spotify

[English](README.md) | [中文](README_zh.md)

[![Tests](https://github.com/BruceZhang1993/feeluown-spotify/actions/workflows/test.yml/badge.svg)](https://github.com/BruceZhang1993/feeluown-spotify/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/BruceZhang1993/feeluown-spotify/branch/main/graph/badge.svg)](https://codecov.io/gh/BruceZhang1993/feeluown-spotify)
[![PyPI](https://img.shields.io/pypi/v/feeluown-spotify)](https://pypi.org/project/feeluown-spotify/)
[![Python](https://img.shields.io/pypi/pyversions/feeluown-spotify)](https://pypi.org/project/feeluown-spotify/)
[![License](https://img.shields.io/github/license/BruceZhang1993/feeluown-spotify)](LICENSE)

Spotify provider for [FeelUOwn](https://github.com/feeluown/feeluown) player.

## ⚠️ Legal Disclaimer

**This project uses unofficial Spotify APIs and is NOT affiliated with, endorsed by, or connected to Spotify AB or any of its subsidiaries.**

By using this software, you acknowledge and agree to the following:

1. **Terms of Service violation**: This plugin relies on [spotapi](https://pypi.org/project/spotapi/), which interacts with Spotify's private/internal APIs in ways that are **not authorized by Spotify**. Using this software may violate [Spotify's Terms of Service](https://www.spotify.com/legal/end-user-agreement/) and could result in **suspension or termination of your Spotify account**.

2. **No warranty**: This software is provided "as is" without warranty of any kind, express or implied. The authors and contributors are **not responsible** for any damages, including but not limited to loss of data, account suspension, or any other consequences arising from the use of this software.

3. **Educational purpose only**: This project is developed for **educational and research purposes**. It is intended to demonstrate how to build a music player plugin and explore music platform APIs. It is not intended for commercial use or to circumvent any digital rights management (DRM) protections.

4. **User responsibility**: You are solely responsible for your use of this software. **Use it at your own risk.** The developers strongly recommend using a **secondary or disposable Spotify account** rather than your primary account.

5. **Compliance**: This project does **not** store, redistribute, or modify any copyrighted music content. It does **not** bypass DRM or enable unauthorized downloading of copyrighted material.

6. **Spotify Premium**: Some features of this plugin may require a **Spotify Premium** subscription. Free-tier users may experience limited functionality.

If you do not agree with these terms, **do not use this software**.

## Features

- 🔍 Search songs, artists, albums, playlists
- 🎵 Song details, playback, lyrics
- 📀 Album details and track listing
- 🎤 Artist details, songs and albums
- 📋 Playlist management (view, add, remove songs)
- 🔐 User authentication (username/password + Cookie)
- ❤️ Favorites management
- 🎧 Daily recommendations
- 🔀 Similar songs (based on Spotify radio)

## Installation

```bash
pip install feeluown-spotify
```

Or using uv:

```bash
uv pip install feeluown-spotify
```

## Usage

### Login

After launching FeelUOwn, log in to Spotify via:

1. **Username/Password**: Open the Spotify login dialog in the GUI, enter your credentials
2. **Cookie**: Copy Spotify cookies from your browser and paste into the login dialog

Login credentials are automatically saved to `~/.feeluown/spotify_credentials.json` and restored on next launch.

### Search

Use the `spotify` prefix in FeelUOwn to search:

```
spotify: song name
```

## Development

### Setup

```bash
# Clone the project
git clone https://github.com/BruceZhang1993/feeluown-spotify.git
cd feeluown-spotify

# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=fuo_spotify --cov-report=html
```

### Project Structure

```
fuo_spotify/
├── __init__.py       # Plugin entry point, enable/disable lifecycle
├── api.py            # SpotifyApi class, wraps spotapi modules
├── schemas.py        # Pydantic data models, Spotify JSON → FeelUOwn models
├── provider.py       # SpotifyProvider(ProviderV2), core functionality
├── provider_ui.py    # GUI login dialog
├── login.py          # Login management, password and Cookie authentication
├── excs.py           # Custom exceptions
└── consts.py         # Constants
```

## Tech Stack

- [FeelUOwn](https://github.com/feeluown/feeluown) — Music player framework
- [spotapi](https://pypi.org/project/spotapi/) — Spotify API client
- [Pydantic](https://docs.pydantic.dev/) — Data serialization

## License

This project is licensed under the [GNU General Public License v3.0 or later](LICENSE).

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
