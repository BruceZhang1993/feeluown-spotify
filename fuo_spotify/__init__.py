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
    login = login_manager.restore_session()
    provider.set_login_manager(login_manager)
    provider.set_app(app)

    if login is None:
        logger.info("No saved Spotify session found")
    else:
        api = SpotifyApi(login)
        provider.set_api(api)
        try:
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
