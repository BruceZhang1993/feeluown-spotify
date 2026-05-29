from unittest.mock import MagicMock, patch
import pytest
from feeluown.library import SearchType, SimpleSearchResult, SongModel, LyricModel
from feeluown.media import Media, Quality


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


def test_song_get(mock_api):
    mock_api.get_track.return_value = {
        "id": "track1",
        "name": "Test Song",
        "duration_ms": 210000,
        "artists": [{"id": "ar1", "name": "Artist 1"}],
        "album": {"id": "al1", "name": "Album 1"},
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = provider.song_get("track1")
    assert isinstance(song, SongModel)
    assert song.identifier == "track1"
    assert song.title == "Test Song"


def test_song_get_not_found(mock_api):
    from fuo_spotify.excs import SpotifyTrackError
    mock_api.get_track.side_effect = SpotifyTrackError("Not found")
    from fuo_spotify.provider import provider
    provider._api = mock_api
    from feeluown.excs import ModelNotFound
    with pytest.raises(ModelNotFound):
        provider.song_get("nonexistent")


def test_song_get_media(mock_api):
    mock_api.get_track.return_value = {
        "id": "track1",
        "preview_url": "https://example.com/preview.mp3",
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    media = provider.song_get_media(song, Quality.Audio("lq"))
    assert isinstance(media, Media)
    assert "preview.mp3" in media.url


def test_song_get_lyric(mock_api):
    mock_api.get_lyrics.return_value = {
        "lyrics": {
            "lines": [
                {"startTimeMs": "0", "words": "Hello"},
                {"startTimeMs": "1000", "words": "World"},
            ]
        }
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    lyric = provider.song_get_lyric(song)
    assert isinstance(lyric, LyricModel)
    assert "Hello" in lyric.content
    assert "World" in lyric.content


def test_song_get_lyric_no_lyrics(mock_api):
    mock_api.get_lyrics.return_value = None
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    lyric = provider.song_get_lyric(song)
    assert lyric is None


def test_song_list_similar(mock_api):
    mock_api.get_radio_tracks.return_value = [
        {"id": "track2", "name": "Similar Song", "duration_ms": 180000},
    ]
    from fuo_spotify.provider import provider
    provider._api = mock_api
    song = MagicMock()
    song.identifier = "track1"
    similar = provider.song_list_similar(song)
    assert len(similar) == 1
    assert similar[0].identifier == "track2"
