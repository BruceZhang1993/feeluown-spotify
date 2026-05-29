from unittest.mock import MagicMock, patch, mock_open
import json

import pytest

from fuo_spotify.excs import SpotifyAuthError
from fuo_spotify.login import LoginManager


@pytest.fixture
def login_manager():
    return LoginManager()


def test_initial_state(login_manager):
    assert login_manager.is_logged_in is False
    assert login_manager.config is None


# --- login_with_password ---

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


# --- login_with_cookies ---

@patch('fuo_spotify.login.spotapi')
def test_login_with_cookies_success(mock_spotapi, login_manager):
    mock_cfg = MagicMock()
    mock_spotapi.Config.return_value = mock_cfg

    with patch.object(login_manager, '_save_credentials'):
        result = login_manager.login_with_cookies({"session": "abc123"})

    assert result == mock_cfg
    assert login_manager.is_logged_in is True


@patch('fuo_spotify.login.spotapi')
def test_login_with_cookies_failure(mock_spotapi, login_manager):
    mock_spotapi.Config.return_value = MagicMock()
    mock_spotapi.Login.from_cookies.side_effect = Exception("Bad cookies")

    with pytest.raises(SpotifyAuthError, match="Cookie login failed"):
        login_manager.login_with_cookies({"session": "bad"})


# --- restore_session ---

def test_restore_session_no_file(login_manager):
    with patch('fuo_spotify.login.CREDENTIALS_PATH') as mock_path:
        mock_path.exists.return_value = False
        result = login_manager.restore_session()
    assert result is None


def test_restore_session_success(login_manager):
    import spotapi
    cookies_data = {"session": "abc123"}
    mock_cfg = MagicMock()
    spotapi.Config.return_value = mock_cfg

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    login_manager._save_path = mock_path

    with patch('builtins.open', mock_open(read_data=json.dumps(cookies_data))):
        result = login_manager.restore_session()

    assert result is mock_cfg
    assert login_manager.is_logged_in is True


@patch('fuo_spotify.login.spotapi')
def test_restore_session_corrupt_file(mock_spotapi, login_manager):
    mock_spotapi.Config.return_value = MagicMock()
    mock_spotapi.Login.from_cookies.side_effect = Exception("bad data")

    with patch('fuo_spotify.login.CREDENTIALS_PATH') as mock_path:
        mock_path.exists.return_value = True
        with patch('builtins.open', mock_open(read_data="not json")):
            result = login_manager.restore_session()

    assert result is None
    assert login_manager.is_logged_in is False


# --- _save_credentials ---

@patch('fuo_spotify.login.spotapi')
def test_save_credentials_success(mock_spotapi, login_manager):
    mock_cfg = MagicMock()
    mock_spotapi.Config.return_value = mock_cfg
    mock_cfg.client.get_cookies.return_value = {"session": "saved"}

    with patch.object(login_manager, '_save_path') as mock_save_path:
        mock_save_path.parent = MagicMock()
        with patch('builtins.open', mock_open()) as m:
            login_manager._save_credentials(mock_cfg)

    mock_save_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


@patch('fuo_spotify.login.spotapi')
def test_save_credentials_failure(mock_spotapi, login_manager):
    mock_cfg = MagicMock()
    mock_cfg.client.get_cookies.side_effect = Exception("cannot get cookies")

    with patch.object(login_manager, '_save_path') as mock_save_path:
        mock_save_path.parent = MagicMock()
        # 不应抛出异常，内部捕获
        login_manager._save_credentials(mock_cfg)


# --- logout ---

def test_logout(login_manager):
    login_manager._cfg = MagicMock()
    with patch('fuo_spotify.login.CREDENTIALS_PATH') as mock_path:
        mock_path.exists.return_value = True
        login_manager.logout()
    assert login_manager.is_logged_in is False


def test_logout_no_file(login_manager):
    login_manager._cfg = MagicMock()
    with patch('fuo_spotify.login.CREDENTIALS_PATH') as mock_path:
        mock_path.exists.return_value = False
        login_manager.logout()
    assert login_manager.is_logged_in is False
