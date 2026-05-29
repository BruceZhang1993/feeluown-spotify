import logging
from typing import List, Optional, Protocol, Tuple

from feeluown.excs import ModelNotFound
from feeluown.library import (
    AbstractProvider,
    BriefAlbumModel,
    BriefArtistModel,
    BriefPlaylistModel,
    ProviderV2,
    ProviderFlags as PF,
    SupportsSongGet,
    SupportsSongMultiQuality,
    SupportsSongLyric,
    SupportsSongSimilar,
    SupportsAlbumGet,
    SupportsAlbumSongsReader,
    SupportsArtistGet,
    SupportsPlaylistGet,
    SupportsPlaylistSongsReader,
    SupportsCurrentUser,
    SupportsCurrentUserListPlaylists,
    SupportsCurrentUserFavSongsReader,
    SupportsRecListDailySongs,
    SupportsRecListDailyPlaylists,
    SimpleSearchResult,
    SearchType,
    ModelType,
    UserModel,
    LyricModel,
)
from feeluown.media import Media, Quality
from feeluown.utils.reader import create_reader

from fuo_spotify.consts import PROVIDER_ID, PROVIDER_NAME
from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError

logger = logging.getLogger(__name__)

SOURCE = PROVIDER_ID


class Supports(
    SupportsSongGet,
    SupportsSongMultiQuality,
    SupportsSongLyric,
    SupportsSongSimilar,
    SupportsAlbumGet,
    SupportsAlbumSongsReader,
    SupportsArtistGet,
    SupportsPlaylistGet,
    SupportsPlaylistSongsReader,
    SupportsCurrentUser,
    SupportsCurrentUserListPlaylists,
    SupportsCurrentUserFavSongsReader,
    SupportsRecListDailySongs,
    SupportsRecListDailyPlaylists,
    Protocol,
):
    pass


class SpotifyProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = PROVIDER_ID
        name = PROVIDER_NAME
        flags = {
            ModelType.song: PF.similar,
            ModelType.none: PF.current_user,
        }

    def __init__(self):
        super().__init__()
        self._api = None
        self._login_manager = None

    def _(self) -> Supports:
        return self

    @property
    def identifier(self):
        return PROVIDER_ID

    @property
    def name(self):
        return PROVIDER_NAME

    def use_model_v2(self, mtype):
        return mtype in (
            ModelType.song,
            ModelType.album,
            ModelType.artist,
            ModelType.playlist,
        )

    def set_api(self, api):
        self._api = api

    def set_login_manager(self, login_manager):
        self._login_manager = login_manager

    def has_current_user(self):
        return self._user is not None

    def get_current_user(self):
        return self._user


provider = SpotifyProvider()


def search(keyword, **kwargs):
    type_ = SearchType.parse(kwargs["type_"])
    api = provider._api
    if api is None:
        return SimpleSearchResult(q=keyword)

    try:
        if type_ == SearchType.so:
            tracks = api.search_songs(keyword)
            songs = [_track_to_model(t) for t in tracks]
            return SimpleSearchResult(q=keyword, songs=songs)
        elif type_ == SearchType.ar:
            artists_data = list(api.search_artists(keyword))
            artists = [_artist_brief_model(a) for a in artists_data[:10]]
            return SimpleSearchResult(q=keyword, artists=artists)
        elif type_ == SearchType.al:
            albums = api.search_albums(keyword)
            album_models = [_album_brief_model(a) for a in albums]
            return SimpleSearchResult(q=keyword, albums=album_models)
        elif type_ == SearchType.pl:
            playlists = api.search_playlists(keyword)
            playlist_models = [_playlist_brief_model(p) for p in playlists]
            return SimpleSearchResult(q=keyword, playlists=playlist_models)
    except SpotifyAPIError as e:
        logger.error(f"Search failed: {e}")
        return SimpleSearchResult(q=keyword)

    return SimpleSearchResult(q=keyword)


provider.search = search


def _get_image_url(images: list) -> str:
    if images and isinstance(images, list) and len(images) > 0:
        return images[0].get("url", "")
    return ""


def _track_to_model(track_data: dict) -> "SongModel":
    from fuo_spotify.schemas import SpotifySong
    from feeluown.library import SongModel

    song_data = SpotifySong.model_validate(track_data)
    artists = []
    if song_data.artists:
        for a in song_data.artists:
            artists.append(BriefArtistModel(
                identifier=a.id or "",
                source=SOURCE,
                name=a.name or "",
            ))
    album = None
    if song_data.album:
        album = BriefAlbumModel(
            identifier=song_data.album.id or "",
            source=SOURCE,
            name=song_data.album.name or "",
        )
    return SongModel(
        identifier=song_data.id or "",
        source=SOURCE,
        title=song_data.name or "",
        duration=song_data.duration_ms or 0,
        artists=artists,
        album=album,
    )


def _artist_brief_model(data: dict) -> BriefArtistModel:
    return BriefArtistModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
    )


def _album_brief_model(data: dict) -> BriefAlbumModel:
    return BriefAlbumModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
    )


def _playlist_brief_model(data: dict) -> BriefPlaylistModel:
    return BriefPlaylistModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
    )
