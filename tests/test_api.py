from unittest.mock import MagicMock, patch
import pytest
from fuo_spotify.api import SpotifyApi
from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError


@pytest.fixture
def mock_login():
    login = MagicMock()
    login.client = MagicMock()
    return login


@pytest.fixture
def api(mock_login):
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_song = MagicMock()
        mock_song.base.part_hash.return_value = "test_hash"
        mock_song.base.client = MagicMock()
        mock_spotapi.Song.return_value = mock_song
        mock_spotapi.Artist.return_value = MagicMock()
        mock_spotapi.User.return_value = MagicMock()
        api = SpotifyApi(mock_login)
        return api


# --- search_songs ---

def test_search_songs_parses_response(api):
    api._song.query_songs.return_value = {
        "data": {
            "searchV2": {
                "tracksV2": {
                    "items": [
                        {"item": {"data": {"id": "track1", "name": "Song 1"}}},
                        {"item": {"data": {"id": "track2", "name": "Song 2"}}},
                    ]
                }
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


def test_search_songs_non_mapping_result(api):
    api._song.query_songs.return_value = "unexpected"
    results = api.search_songs("test query")
    assert results == []


def test_search_songs_filters_items_without_id(api):
    api._song.query_songs.return_value = {
        "data": {
            "searchV2": {
                "tracksV2": {
                    "items": [
                        {"item": {"data": {"name": "No ID"}}},
                        {"item": {"data": {"id": "track1", "name": "Song 1"}}},
                    ]
                }
            }
        }
    }
    results = api.search_songs("test query")
    assert len(results) == 1
    assert results[0]["id"] == "track1"


def test_search_songs_api_error(api):
    api._song.query_songs.side_effect = Exception("network down")
    with pytest.raises(SpotifyAPIError, match="Search songs failed"):
        api.search_songs("test query")


# --- search_artists ---

def test_search_artists(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "searchV2": {
                "artists": {
                    "items": [
                        {"data": {"id": "ar1", "profile": {"name": "Artist 1"}}},
                    ]
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    results = api.search_artists("test")
    assert len(results) == 1
    assert results[0]["id"] == "ar1"


def test_search_artists_api_error(api):
    api._song.base.client.post.side_effect = Exception("fail")
    with pytest.raises(SpotifyAPIError, match="Search artists failed"):
        api.search_artists("test")


# --- search_albums ---

def test_search_albums(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "searchV2": {
                "albumsV2": {
                    "items": [
                        {"data": {"id": "al1", "name": "Album 1"}},
                        {"data": {"name": "No ID"}},
                    ]
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    results = api.search_albums("test")
    assert len(results) == 1
    assert results[0]["id"] == "al1"


def test_search_albums_api_fail(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "bad request"
    api._song.base.client.post.return_value = mock_resp
    with pytest.raises(SpotifyAPIError, match="Search albums failed"):
        api.search_albums("test")


def test_search_albums_unexpected_error(api):
    api._song.base.client.post.side_effect = Exception("timeout")
    with pytest.raises(SpotifyAPIError, match="Search albums failed"):
        api.search_albums("test")


# --- search_playlists ---

def test_search_playlists(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "searchV2": {
                "playlistsV2": {
                    "items": [
                        {"data": {"id": "pl1", "name": "Playlist 1"}},
                    ]
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    results = api.search_playlists("test")
    assert len(results) == 1
    assert results[0]["id"] == "pl1"


def test_search_playlists_api_fail(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "bad request"
    api._song.base.client.post.return_value = mock_resp
    with pytest.raises(SpotifyAPIError, match="Search playlists failed"):
        api.search_playlists("test")


def test_search_playlists_unexpected_error(api):
    api._song.base.client.post.side_effect = Exception("timeout")
    with pytest.raises(SpotifyAPIError, match="Search playlists failed"):
        api.search_playlists("test")


# --- get_track ---

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


def test_get_track_unexpected_error(api):
    api._song.get_track_info.side_effect = Exception("timeout")
    with pytest.raises(SpotifyTrackError, match="Get track failed"):
        api.get_track("track1")


# --- get_artist ---

def test_get_artist(api):
    api._artist.get_artist.return_value = {
        "data": {"artistUnion": {"id": "ar1", "name": "Artist"}}
    }
    result = api.get_artist("ar1")
    assert result["id"] == "ar1"


def test_get_artist_error(api):
    api._artist.get_artist.side_effect = Exception("fail")
    with pytest.raises(SpotifyAPIError, match="Get artist failed"):
        api.get_artist("ar1")


# --- get_album ---

def test_get_album(api):
    mock_public_album = MagicMock()
    mock_public_album.get_album_info.return_value = {
        "data": {"album": {"id": "al1", "name": "Album"}}
    }
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_spotapi.PublicAlbum.return_value = mock_public_album
        result = api.get_album("al1")
    assert result["id"] == "al1"


def test_get_album_error(api):
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_spotapi.PublicAlbum.return_value.get_album_info.side_effect = Exception("fail")
        with pytest.raises(SpotifyAPIError, match="Get album failed"):
            api.get_album("al1")


# --- get_playlist ---

def test_get_playlist(api):
    mock_public_playlist = MagicMock()
    mock_public_playlist.get_playlist_info.return_value = {
        "data": {"playlistV2": {"id": "pl1", "name": "Playlist"}}
    }
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_spotapi.PublicPlaylist.return_value = mock_public_playlist
        result = api.get_playlist("pl1")
    assert result["id"] == "pl1"


def test_get_playlist_error(api):
    with patch('fuo_spotify.api.spotapi') as mock_spotapi:
        mock_spotapi.PublicPlaylist.return_value.get_playlist_info.side_effect = Exception("fail")
        with pytest.raises(SpotifyAPIError, match="Get playlist failed"):
            api.get_playlist("pl1")


# --- get_lyrics ---

def test_get_lyrics_returns_none_on_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Not found"
    api._song.base.client.get.return_value = mock_resp
    result = api.get_lyrics("track1")
    assert result is None


def test_get_lyrics_returns_data_on_success(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {"lyrics": {"lines": []}}
    api._song.base.client.get.return_value = mock_resp
    result = api.get_lyrics("track1")
    assert result == {"lyrics": {"lines": []}}


def test_get_lyrics_returns_none_on_exception(api):
    api._song.base.client.get.side_effect = Exception("network error")
    result = api.get_lyrics("track1")
    assert result is None


# --- get_user_info ---

def test_get_user_info(api):
    api._user.get_user_info.return_value = {"id": "u1", "display_name": "User"}
    result = api.get_user_info()
    assert result["id"] == "u1"


def test_get_user_info_error(api):
    api._user.get_user_info.side_effect = Exception("fail")
    with pytest.raises(SpotifyAPIError, match="Get user info failed"):
        api.get_user_info()


# --- like_song ---

def test_like_song_returns_true_on_success(api):
    result = api.like_song("track1")
    assert result is True


def test_like_song_returns_false_on_failure(api):
    api._song.like_song.side_effect = Exception("Network error")
    result = api.like_song("track1")
    assert result is False


# --- add_to_playlist ---

def test_add_to_playlist_success(api):
    api._song.add_song_to_playlist.return_value = None
    result = api.add_to_playlist("pl1", "track1")
    assert result is True


def test_add_to_playlist_failure(api):
    api._song.add_song_to_playlist.side_effect = Exception("fail")
    result = api.add_to_playlist("pl1", "track1")
    assert result is False


# --- remove_from_playlist ---

def test_remove_from_playlist_success(api):
    api._song.remove_song_from_playlist.return_value = None
    result = api.remove_from_playlist("pl1", "track1")
    assert result is True


def test_remove_from_playlist_failure(api):
    api._song.remove_song_from_playlist.side_effect = Exception("fail")
    result = api.remove_from_playlist("pl1", "track1")
    assert result is False


# --- get_radio_tracks ---

def test_get_radio_tracks(api):
    api._song.playlist.return_value = {
        "content": {
            "items": [
                {"item": {"id": "track2", "name": "Radio Song"}},
                {"item": {"name": "No ID"}},
            ]
        }
    }
    result = api.get_radio_tracks("track1")
    assert len(result) == 1
    assert result[0]["id"] == "track2"


def test_get_radio_tracks_empty(api):
    api._song.playlist.return_value = None
    result = api.get_radio_tracks("track1")
    assert result == []


def test_get_radio_tracks_error(api):
    api._song.playlist.side_effect = Exception("fail")
    result = api.get_radio_tracks("track1")
    assert result == []


# --- get_current_user_profile ---

def test_get_current_user_profile_success(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "me": {
                "profile": {
                    "name": "Test User",
                    "username": "testuser",
                    "avatar": {
                        "sources": [
                            {"height": 64, "url": "https://example.com/avatar_64.jpg", "width": 64},
                            {"height": 300, "url": "https://example.com/avatar_300.jpg", "width": 300},
                        ]
                    },
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    result = api.get_current_user_profile()
    assert result["name"] == "Test User"
    assert result["username"] == "testuser"
    assert result["avatar"]["sources"][0]["url"] == "https://example.com/avatar_64.jpg"


def test_get_current_user_profile_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Unauthorized"
    api._song.base.client.post.return_value = mock_resp
    result = api.get_current_user_profile()
    assert result == {}


def test_get_current_user_profile_exception(api):
    api._song.base.client.post.side_effect = Exception("Network error")
    result = api.get_current_user_profile()
    assert result == {}


# --- get_home_sections ---

# --- get_user_top_content ---

def test_get_user_top_content_success(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "me": {
                "profile": {
                    "topTracks": {
                        "items": [
                            {"data": {"uri": "spotify:track:t1", "name": "Song 1"}},
                        ]
                    },
                    "topArtists": {
                        "items": [
                            {"data": {"uri": "spotify:artist:a1", "profile": {"name": "Artist 1"}}},
                        ]
                    },
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    result = api.get_user_top_content()
    assert result["topTracks"]["items"][0]["data"]["name"] == "Song 1"


def test_get_user_top_content_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Error"
    api._song.base.client.post.return_value = mock_resp
    result = api.get_user_top_content()
    assert result == {}


# --- get_top_tracks ---

def test_get_top_tracks_success(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "me": {
                "profile": {
                    "topTracks": {
                        "items": [
                            {"data": {"uri": "spotify:track:t1", "name": "Song 1"}},
                            {"data": {"uri": "spotify:track:t2", "name": "Song 2"}},
                        ]
                    },
                    "topArtists": {"items": []},
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    result = api.get_top_tracks()
    assert len(result) == 2
    assert result[0]["name"] == "Song 1"


def test_get_top_tracks_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Error"
    api._song.base.client.post.return_value = mock_resp
    result = api.get_top_tracks()
    assert result == []


# --- get_saved_albums ---

def test_get_saved_albums_success(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "me": {
                "libraryV3": {
                    "items": [
                        {
                            "item": {
                                "_uri": "spotify:album:al1",
                                "data": {
                                    "name": "Test Album",
                                    "artists": {"items": [{"profile": {"name": "Artist 1"}}]},
                                    "coverArt": {"sources": [{"url": "https://example.com/cover.jpg"}]},
                                },
                            }
                        }
                    ]
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    result = api.get_saved_albums()
    assert len(result) == 1
    assert result[0]["id"] == "al1"
    assert result[0]["name"] == "Test Album"
    assert result[0]["artist"] == "Artist 1"


def test_get_saved_albums_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Error"
    api._song.base.client.post.return_value = mock_resp
    with pytest.raises(SpotifyAPIError):
        api.get_saved_albums()


# --- get_saved_artists ---

def test_get_saved_artists_success(api):
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = {
        "data": {
            "me": {
                "libraryV3": {
                    "items": [
                        {
                            "item": {
                                "_uri": "spotify:artist:ar1",
                                "data": {
                                    "profile": {"name": "Test Artist"},
                                    "visuals": {
                                        "avatarImage": {
                                            "sources": [{"url": "https://example.com/artist.jpg"}]
                                        }
                                    },
                                },
                            }
                        }
                    ]
                }
            }
        }
    }
    api._song.base.client.post.return_value = mock_resp
    result = api.get_saved_artists()
    assert len(result) == 1
    assert result[0]["id"] == "ar1"
    assert result[0]["name"] == "Test Artist"
    assert result[0]["pic_url"] == "https://example.com/artist.jpg"


def test_get_saved_artists_failure(api):
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Error"
    api._song.base.client.post.return_value = mock_resp
    with pytest.raises(SpotifyAPIError):
        api.get_saved_artists()
