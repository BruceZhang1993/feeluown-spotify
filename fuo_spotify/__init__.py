# fuo_spotify/__init__.py
import logging

from fuo_spotify.provider import SpotifyProvider

__alias__ = 'Spotify'
__desc__ = 'Spotify 音乐源'
__version__ = '0.1.0'
__feeluown_version__ = '1.1.0'

logger = logging.getLogger(__name__)


def enable(app):
    provider = SpotifyProvider()
    app.library.register(provider)

    if app.mode & app.GuiMode:
        from fuo_spotify.provider_ui import ProviderUI
        provider_ui = ProviderUI(app, provider)
        app.pvd_ui_mgr.register(provider_ui)


def disable(app):
    from fuo_spotify.provider import provider
    app.library.deregister(provider)
    app.providers.remove(provider.identifier)
