from unittest.mock import MagicMock, patch
import pytest
from feeluown.library import SearchType, SimpleSearchResult


@pytest.fixture
def mock_api():
    api = MagicMock()
    return api


def test_search_songs(mock_api):
    mock_api.search_songs.return_value = [
        {
            "id": "track1",
            "name": "Test Song",
            "duration_ms": 210000,
            "artists": [{"id": "ar1", "name": "Artist 1"}],
            "album": {"id": "al1", "name": "Album 1"},
        }
    ]
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.so)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.songs) == 1
    assert result.songs[0].identifier == "track1"


def test_search_artists(mock_api):
    mock_api.search_artists.return_value = iter([
        {"id": "ar1", "name": "Artist 1"},
    ])
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.ar)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.artists) == 1


def test_search_albums(mock_api):
    mock_api.search_albums.return_value = [
        {"id": "al1", "name": "Album 1"},
    ]
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.al)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.albums) == 1


def test_search_playlists(mock_api):
    mock_api.search_playlists.return_value = [
        {"id": "pl1", "name": "Playlist 1"},
    ]
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", mock_api):
        result = search("test", type_=SearchType.pl)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.playlists) == 1


def test_search_with_no_api():
    from fuo_spotify.provider import search
    with patch("fuo_spotify.provider.provider._api", None):
        result = search("test", type_=SearchType.so)
    assert isinstance(result, SimpleSearchResult)
    assert len(result.songs) == 0
