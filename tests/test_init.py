from unittest.mock import MagicMock, patch


def test_module_attributes():
    import fuo_spotify
    assert fuo_spotify.__alias__ == "Spotify"
    assert fuo_spotify.__desc__ == "Spotify 音乐源"
    assert fuo_spotify.__version__ == "0.1.0"


def test_enable_no_saved_session():
    with patch("fuo_spotify.login.LoginManager") as mock_login_cls, \
         patch("fuo_spotify.api.SpotifyApi") as mock_api_cls, \
         patch("fuo_spotify.provider.provider") as mock_provider:
        mock_login = MagicMock()
        mock_login.restore_session.return_value = None
        mock_login_cls.return_value = mock_login

        mock_app = MagicMock()
        mock_app.mode = 0
        mock_app.GuiMode = 1

        from fuo_spotify import enable
        enable(mock_app)

        mock_app.library.register.assert_called_once()


def test_enable_with_saved_session():
    with patch("fuo_spotify.login.LoginManager") as mock_login_cls, \
         patch("fuo_spotify.api.SpotifyApi") as mock_api_cls, \
         patch("fuo_spotify.provider.provider") as mock_provider:
        mock_login = MagicMock()
        mock_cfg = MagicMock()
        mock_login.restore_session.return_value = mock_cfg
        mock_login_cls.return_value = mock_login

        mock_api = MagicMock()
        mock_api.get_user_info.return_value = {"id": "u1", "display_name": "User"}
        mock_api_cls.return_value = mock_api

        mock_app = MagicMock()
        mock_app.mode = 0
        mock_app.GuiMode = 1

        from fuo_spotify import enable
        enable(mock_app)

        mock_api_cls.assert_called_once_with(mock_cfg)
        mock_provider.set_api.assert_called_once_with(mock_api)
        mock_provider.set_login_manager.assert_called_once_with(mock_login)
        mock_app.library.register.assert_called_once()


def test_enable_with_session_api_fail():
    with patch("fuo_spotify.login.LoginManager") as mock_login_cls, \
         patch("fuo_spotify.api.SpotifyApi") as mock_api_cls, \
         patch("fuo_spotify.provider.provider") as mock_provider:
        mock_login = MagicMock()
        mock_cfg = MagicMock()
        mock_login.restore_session.return_value = mock_cfg
        mock_login_cls.return_value = mock_login

        mock_api = MagicMock()
        mock_api.get_user_info.side_effect = Exception("API down")
        mock_api_cls.return_value = mock_api

        mock_app = MagicMock()
        mock_app.mode = 0
        mock_app.GuiMode = 1

        from fuo_spotify import enable
        # 不应抛出异常
        enable(mock_app)
        mock_app.library.register.assert_called_once()


def test_enable_gui_mode():
    import sys
    mock_provider_ui = MagicMock()
    with patch("fuo_spotify.login.LoginManager") as mock_login_cls, \
         patch("fuo_spotify.api.SpotifyApi") as mock_api_cls, \
         patch.dict(sys.modules, {"fuo_spotify.provider_ui": mock_provider_ui}), \
         patch("fuo_spotify.provider.provider") as mock_provider:
        mock_login = MagicMock()
        mock_login.restore_session.return_value = None
        mock_login_cls.return_value = mock_login

        mock_app = MagicMock()
        mock_app.mode = 1
        mock_app.GuiMode = 1

        from fuo_spotify import enable
        enable(mock_app)

        mock_provider_ui.ProviderUI.assert_called_once()
        mock_app.pvd_ui_mgr.register.assert_called_once()


def test_disable():
    with patch("fuo_spotify.provider.provider") as mock_provider:
        mock_app = MagicMock()
        from fuo_spotify import disable
        disable(mock_app)
        mock_app.library.deregister.assert_called_once_with(mock_provider)
        mock_app.providers.remove.assert_called_once_with(mock_provider.identifier)
