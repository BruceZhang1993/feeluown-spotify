from unittest.mock import MagicMock, patch

import pytest

from fuo_spotify.excs import SpotifyAuthError
from fuo_spotify.login import LoginManager


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
    mock_login_instance = MagicMock()
    mock_login_instance.login.side_effect = Exception("Auth failed")
    mock_spotapi.Login.return_value = mock_login_instance

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
