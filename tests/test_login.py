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
    assert login_manager.login is None


# --- login_with_cookies ---

@patch('fuo_spotify.login.spotapi')
def test_login_with_cookies_success(mock_spotapi, login_manager):
    mock_login = MagicMock()
    mock_spotapi.Login.from_cookies.return_value = mock_login

    with patch.object(login_manager, '_save_credentials'):
        result = login_manager.login_with_cookies("user@example.com", {"sp_dc": "abc123"})

    assert result == mock_login
    assert login_manager.is_logged_in is True


@patch('fuo_spotify.login.spotapi')
def test_login_with_cookies_failure(mock_spotapi, login_manager):
    mock_spotapi.Config.return_value = MagicMock()
    mock_spotapi.Login.from_cookies.side_effect = Exception("Bad cookies")

    with pytest.raises(SpotifyAuthError, match="Cookie login failed"):
        login_manager.login_with_cookies("user@example.com", {"sp_dc": "bad"})


# --- restore_session ---

def test_restore_session_no_file(login_manager):
    mock_path = MagicMock()
    mock_path.exists.return_value = False
    login_manager._save_path = mock_path
    result = login_manager.restore_session()
    assert result is None


@patch('fuo_spotify.login.spotapi')
def test_restore_session_success(mock_spotapi, login_manager):
    cookies_data = {"identifier": "user@example.com", "cookies": {"sp_dc": "abc123"}}
    mock_login = MagicMock()
    mock_spotapi.Login.from_cookies.return_value = mock_login

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    login_manager._save_path = mock_path

    with patch('builtins.open', mock_open(read_data=json.dumps(cookies_data))):
        result = login_manager.restore_session()

    assert result is mock_login
    assert login_manager.is_logged_in is True


@patch('fuo_spotify.login.spotapi')
def test_restore_session_corrupt_file(mock_spotapi, login_manager):
    mock_spotapi.Config.return_value = MagicMock()
    mock_spotapi.Login.from_cookies.side_effect = Exception("bad data")

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    login_manager._save_path = mock_path

    with patch('builtins.open', mock_open(read_data="not json")):
        result = login_manager.restore_session()

    assert result is None
    assert login_manager.is_logged_in is False


# --- _save_credentials ---

def test_save_credentials_success(login_manager):
    login_manager._identifier = "user@example.com"
    cookies = {"sp_dc": "saved", "sp_key": "key123"}
    with patch.object(login_manager, '_save_path') as mock_save_path:
        mock_save_path.parent = MagicMock()
        with patch('builtins.open', mock_open()):
            login_manager._save_credentials(cookies)

    mock_save_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_save_credentials_filters_non_auth_cookies(login_manager):
    login_manager._identifier = "user@example.com"
    cookies = {"sp_dc": "saved", "OptanonConsent": "non-ascii-\u4e2d\u6587"}
    written_data = []

    def capture_write(data, **kwargs):
        written_data.append(data)

    m = mock_open()
    with patch.object(login_manager, '_save_path') as mock_save_path:
        mock_save_path.parent = MagicMock()
        with patch('builtins.open', m):
            login_manager._save_credentials(cookies)

    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    saved = json.loads(written)
    assert "sp_dc" in saved["cookies"]
    assert "OptanonConsent" not in saved["cookies"]


# --- logout ---

def test_logout(login_manager):
    login_manager._login = MagicMock()
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    login_manager._save_path = mock_path
    login_manager.logout()
    assert login_manager.is_logged_in is False


def test_logout_no_file(login_manager):
    login_manager._login = MagicMock()
    mock_path = MagicMock()
    mock_path.exists.return_value = False
    login_manager._save_path = mock_path
    login_manager.logout()
    assert login_manager.is_logged_in is False
