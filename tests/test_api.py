from unittest.mock import MagicMock, patch
import pytest
from fuo_spotify.api import SpotifyApi
from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError


@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    cfg.client = MagicMock()
    cfg.client.part_hash.return_value = "test_hash"
    return cfg


@pytest.fixture
def api(mock_cfg):
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_spotapi.Song.return_value = MagicMock()
        mock_spotapi.Artist.return_value = MagicMock()
        mock_spotapi.PublicAlbum.return_value = MagicMock()
        mock_spotapi.PublicPlaylist.return_value = MagicMock()
        mock_spotapi.User.return_value = MagicMock()
        api = SpotifyApi(mock_cfg)
        return api


def test_search_songs_parses_response(api):
    api._song.query_songs.return_value = {
        "searchV2": {
            "tracksV2": {
                "items": [
                    {"item": {"data": {"id": "track1", "name": "Song 1"}}},
                    {"item": {"data": {"id": "track2", "name": "Song 2"}}},
                ]
            }
        }
    }
    results = api.search_songs("test query")
    assert len(results) == 2
    assert results[0]["id"] == "track1"


def test_search_songs_empty_response(api):
    api._song.query_songs.return_value = {}
    results = api.search_songs("test query")
    assert results == []


def test_get_track_raises_on_not_found(api):
    api._song.get_track_info.return_value = {"data": {"trackUnion": {}}}
    with pytest.raises(SpotifyTrackError):
        api.get_track("nonexistent")


def test_get_track_returns_track_data(api):
    api._song.get_track_info.return_value = {
        "data": {"trackUnion": {"id": "track1", "name": "Test"}}
    }
    result = api.get_track("track1")
    assert result["id"] == "track1"


def test_get_lyrics_returns_none_on_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Not found"
    api._client.get.return_value = mock_resp
    result = api.get_lyrics("track1")
    assert result is None


def test_like_song_returns_true_on_success(api):
    result = api.like_song("track1")
    assert result is True


def test_like_song_returns_false_on_failure(api):
    api._song.like_song.side_effect = Exception("Network error")
    result = api.like_song("track1")
    assert result is False
