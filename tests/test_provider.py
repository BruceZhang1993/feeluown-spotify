from unittest.mock import MagicMock, patch
import pytest
from feeluown.library import SearchType, SimpleSearchResult, SongModel, LyricModel, AlbumModel, ArtistModel, PlaylistModel
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


def test_album_get(mock_api):
    mock_api.get_album.return_value = {
        "id": "al1",
        "name": "Test Album",
        "cover": {"sources": [{"url": "https://example.com/cover.jpg"}]},
        "artists": [{"id": "ar1", "name": "Artist 1"}],
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    album = provider.album_get("al1")
    assert isinstance(album, AlbumModel)
    assert album.identifier == "al1"
    assert album.name == "Test Album"


def test_album_get_not_found(mock_api):
    mock_api.get_album.return_value = {}
    from fuo_spotify.provider import provider
    provider._api = mock_api
    from feeluown.excs import ModelNotFound
    with pytest.raises(ModelNotFound):
        provider.album_get("nonexistent")


def test_artist_get(mock_api):
    mock_api.get_artist.return_value = {
        "id": "ar1",
        "name": "Test Artist",
        "visuals": {
            "avatarImage": {
                "sources": [{"url": "https://example.com/artist.jpg"}]
            }
        },
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    artist = provider.artist_get("ar1")
    assert isinstance(artist, ArtistModel)
    assert artist.identifier == "ar1"
    assert artist.name == "Test Artist"


def test_artist_get_not_found(mock_api):
    mock_api.get_artist.return_value = {}
    from fuo_spotify.provider import provider
    provider._api = mock_api
    from feeluown.excs import ModelNotFound
    with pytest.raises(ModelNotFound):
        provider.artist_get("nonexistent")


def test_playlist_get(mock_api):
    mock_api.get_playlist.return_value = {
        "identifier": {"id": "pl1"},
        "name": "Test Playlist",
        "description": "A test playlist",
        "images": {"items": [{"sources": [{"url": "https://example.com/cover.jpg"}]}]},
        "content": {
            "items": [
                {"item": {"data": {"id": "track1", "name": "Song 1", "duration_ms": 180000}}},
                {"item": {"data": {"id": "track2", "name": "Song 2", "duration_ms": 210000}}},
            ]
        },
    }
    from fuo_spotify.provider import provider
    provider._api = mock_api
    playlist = provider.playlist_get("pl1")
    assert isinstance(playlist, PlaylistModel)
    assert playlist.identifier == "pl1"
    assert playlist.name == "Test Playlist"
    assert playlist.description == "A test playlist"
    assert "cover.jpg" in playlist.cover


def test_playlist_add_song(mock_api):
    mock_api.add_to_playlist.return_value = True
    from fuo_spotify.provider import provider
    provider._api = mock_api
    playlist = MagicMock()
    playlist.identifier = "pl1"
    playlist._cache = {"songs": []}
    song = MagicMock()
    song.identifier = "track1"
    result = provider.playlist_add_song(playlist, song)
    assert result is True
    assert "songs" not in playlist._cache


def test_has_current_user_false():
    from fuo_spotify.provider import provider
    provider._user = None
    assert provider.has_current_user() is False


def test_has_current_user_true():
    from fuo_spotify.provider import provider
    provider._user = MagicMock()
    assert provider.has_current_user() is True


def test_current_user_list_playlists_no_user():
    from fuo_spotify.provider import provider
    provider._user = None
    result = provider.current_user_list_playlists()
    assert result == []


def test_rec_list_daily_songs_no_user():
    from fuo_spotify.provider import provider
    provider._user = None
    result = provider.rec_list_daily_songs()
    assert result == []
