from fuo_spotify.schemas import (
    SpotifySong,
    SpotifyArtist,
    SpotifyAlbum,
    SpotifyPlaylist,
    SpotifyUser,
)


def test_spotify_song_from_dict():
    data = {
        "id": "3QwiidVHfeE9y5jl4n2MTC",
        "name": "Test Song",
        "duration_ms": 210000,
        "artists": [{"id": "artist1", "name": "Test Artist"}],
        "album": {
            "id": "album1",
            "name": "Test Album",
            "images": [{"url": "https://example.com/cover.jpg", "width": 640, "height": 640}]
        },
        "preview_url": "https://example.com/preview.mp3",
    }
    song = SpotifySong.model_validate(data)
    assert song.id == "3QwiidVHfeE9y5jl4n2MTC"
    assert song.name == "Test Song"
    assert song.duration_ms == 210000
    assert len(song.artists) == 1
    assert song.artists[0].name == "Test Artist"
    assert song.album.cover == "https://example.com/cover.jpg"


def test_spotify_song_missing_fields():
    data = {"id": "abc123"}
    song = SpotifySong.model_validate(data)
    assert song.id == "abc123"
    assert song.name is None
    assert song.artists is None
    assert song.album is None


def test_spotify_artist_cover():
    data = {
        "id": "artist1",
        "name": "Test Artist",
        "images": [
            {"url": "https://example.com/large.jpg", "width": 640, "height": 640},
            {"url": "https://example.com/small.jpg", "width": 64, "height": 64},
        ]
    }
    artist = SpotifyArtist.model_validate(data)
    assert artist.pic_url == "https://example.com/large.jpg"


def test_spotify_artist_no_images():
    data = {"id": "artist1", "name": "Test Artist"}
    artist = SpotifyArtist.model_validate(data)
    assert artist.pic_url is None


def test_spotify_album_from_dict():
    data = {
        "id": "album1",
        "name": "Test Album",
        "images": [{"url": "https://example.com/cover.jpg", "width": 640, "height": 640}],
        "artists": [{"id": "artist1", "name": "Test Artist"}],
        "release_date": "2024-01-01",
        "total_tracks": 12,
    }
    album = SpotifyAlbum.model_validate(data)
    assert album.id == "album1"
    assert album.cover == "https://example.com/cover.jpg"
    assert album.total_tracks == 12


def test_spotify_playlist_from_dict():
    data = {
        "id": "playlist1",
        "name": "Test Playlist",
        "description": "A test playlist",
        "images": [{"url": "https://example.com/cover.jpg", "width": 640, "height": 640}],
        "owner": {"id": "user1", "name": "Test User"},
    }
    playlist = SpotifyPlaylist.model_validate(data)
    assert playlist.id == "playlist1"
    assert playlist.name == "Test Playlist"
    assert playlist.cover == "https://example.com/cover.jpg"


def test_spotify_user_from_dict():
    data = {
        "id": "user1",
        "display_name": "Test User",
        "images": [{"url": "https://example.com/avatar.jpg", "width": 300, "height": 300}],
        "email": "test@example.com",
    }
    user = SpotifyUser.model_validate(data)
    assert user.id == "user1"
    assert user.display_name == "Test User"
    assert user.avatar_url == "https://example.com/avatar.jpg"


def test_spotify_user_no_images():
    data = {"id": "user1", "display_name": "Test User"}
    user = SpotifyUser.model_validate(data)
    assert user.avatar_url is None


def test_spotify_brief_album_no_images():
    from fuo_spotify.schemas import SpotifyBriefAlbum
    album = SpotifyBriefAlbum(id="al1")
    assert album.cover is None


def test_spotify_brief_album_with_images():
    from fuo_spotify.schemas import SpotifyBriefAlbum, SpotifyImage
    album = SpotifyBriefAlbum(
        id="al1",
        images=[SpotifyImage(url="https://example.com/cover.jpg")],
    )
    assert album.cover == "https://example.com/cover.jpg"


def test_spotify_album_no_images():
    data = {"id": "album1", "name": "Album"}
    album = SpotifyAlbum.model_validate(data)
    assert album.cover is None


def test_spotify_playlist_no_images():
    data = {"id": "pl1", "name": "Playlist"}
    playlist = SpotifyPlaylist.model_validate(data)
    assert playlist.cover is None


def test_spotify_image_fields():
    from fuo_spotify.schemas import SpotifyImage
    img = SpotifyImage(url="https://example.com/img.jpg", width=640, height=480)
    assert img.url == "https://example.com/img.jpg"
    assert img.width == 640
    assert img.height == 480


def test_spotify_song_all_fields():
    data = {
        "id": "track1",
        "name": "Song",
        "duration_ms": 180000,
        "artists": [{"id": "ar1", "name": "Artist"}],
        "album": {
            "id": "al1",
            "name": "Album",
            "images": [{"url": "https://example.com/cover.jpg"}],
        },
        "preview_url": "https://example.com/preview.mp3",
        "external_urls": {"spotify": "https://open.spotify.com/track/track1"},
    }
    song = SpotifySong.model_validate(data)
    assert song.preview_url == "https://example.com/preview.mp3"
    assert song.external_urls == {"spotify": "https://open.spotify.com/track/track1"}


def test_spotify_lyrics():
    from fuo_spotify.schemas import SpotifyLyrics
    lyrics = SpotifyLyrics(lyrics={"lines": [{"words": "hello"}]})
    assert lyrics.lyrics["lines"][0]["words"] == "hello"
    empty = SpotifyLyrics()
    assert empty.lyrics is None
