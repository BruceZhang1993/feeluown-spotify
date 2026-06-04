import logging
from typing import List, Optional, Protocol

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
    SupportsCurrentUserFavAlbumsReader,
    SupportsCurrentUserFavArtistsReader,
    SupportsRecListDailySongs,
    SupportsRecListDailyPlaylists,
    SupportsRecListCollections,
    SupportsRecACollectionOfSongs,
    SimpleSearchResult,
    SearchType,
    ModelType,
    UserModel,
    LyricModel,
    Collection,
    CollectionType,
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
    SupportsCurrentUserFavAlbumsReader,
    SupportsCurrentUserFavArtistsReader,
    SupportsRecListDailySongs,
    SupportsRecListDailyPlaylists,
    SupportsRecListCollections,
    SupportsRecACollectionOfSongs,
    Protocol,
):
    pass


class SpotifyProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = PROVIDER_ID
        name = PROVIDER_NAME
        flags = {
            ModelType.song: PF.similar | PF.get | PF.model_v2,
            ModelType.none: PF.current_user,
            ModelType.album: PF.get | PF.songs_rd | PF.albums_rd | PF.model_v2 | PF.web_url,
            ModelType.artist: PF.get | PF.artists_rd | PF.model_v2 | PF.web_url,
            ModelType.playlist: PF.get | PF.songs_rd | PF.model_v2 | PF.web_url,
        }

    def __init__(self):
        super().__init__()
        self._api = None
        self._login_manager = None

    def _(self) -> Supports:
        return self
    
    def auto_login(self):
        from fuo_spotify.login import LoginManager
        from fuo_spotify.api import SpotifyApi

        login_manager = LoginManager()
        login = login_manager.restore_session()
        self.set_login_manager(login_manager)

        if login is None:
            logger.info("No saved Spotify session found")
        else:
            api = SpotifyApi(login)
            self.set_api(api)
            try:
                user = self.user_info()
                self.auth(user)
                logger.info(f"Spotify user logged in: {user.name}")
            except Exception as e:
                logger.warning(f"Auto login failed: {e}")

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

    def user_info(self) -> UserModel:
        """获取当前用户信息（含头像），参考 feeluown-bilibili 的实现模式。"""
        if self._api is None:
            raise SpotifyAPIError("API not initialized")

        # 通过 profileAttributes GraphQL 获取用户名和头像
        display_name = ""
        avatar_url = ""
        identifier = ""
        try:
            profile = self._api.get_current_user_profile()
            # profileAttributes 返回: {"name": "...", "username": "...", "avatar": {"sources": [...]}}
            display_name = profile.get("name", "")
            identifier = profile.get("username", "")
            avatar_sources = profile.get("avatar", {}).get("sources", [])
            if avatar_sources:
                # 取最大尺寸的头像
                avatar_url = max(avatar_sources, key=lambda s: s.get("width", 0)).get("url", "")
        except Exception as e:
            logger.debug(f"Get user profile from profileAttributes failed (non-fatal): {e}")

        # 回退：从 account-settings API 获取 identifier
        if not identifier:
            try:
                user_info = self._api.get_user_info()
                identifier = user_info.get("profile", {}).get("username", "")
            except Exception:
                pass

        logger.info(f"User info: id={identifier}, name={display_name}, avatar={'yes' if avatar_url else 'no'}")

        return UserModel(
            identifier=identifier,
            source=SOURCE,
            name=display_name,
            avatar_url=avatar_url,
        )

    def has_current_user(self):
        return self._user is not None

    def get_current_user(self):
        return self._user

    def song_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Song {identifier} not found")
        try:
            track_data = self._api.get_track(identifier)
            return _track_to_model(track_data)
        except SpotifyTrackError:
            raise ModelNotFound(f"Song {identifier} not found")

    def song_get_media(self, song, quality: Quality.Audio) -> Optional[Media]:
        return None

    def song_list_quality(self, song) -> List[Quality.Audio]:
        return [Quality.Audio("lq")]

    def song_get_lyric(self, song):
        if self._api is None:
            return None
        try:
            lyrics_data = self._api.get_lyrics(song.identifier)
            if lyrics_data and lyrics_data.get("lyrics"):
                lines = lyrics_data["lyrics"].get("lines", [])
                content = "\n".join(
                    f"[{line.get('startTimeMs', '0')}]"
                    f"{line.get('words', '')}"
                    for line in lines
                )
                return LyricModel(
                    identifier=song.identifier,
                    source=SOURCE,
                    content=content,
                )
            return None
        except Exception as e:
            logger.warning(f"Get song lyric failed: {e}")
            return None

    def song_list_similar(self, song):
        if self._api is None:
            return []
        try:
            tracks = self._api.get_radio_tracks(song.identifier)
            return [_track_to_model(t) for t in tracks]
        except Exception as e:
            logger.warning(f"Get similar songs failed: {e}")
            return []

    def album_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Album {identifier} not found")
        try:
            data = self._api.get_album(identifier)
            if not data:
                raise ModelNotFound(f"Album {identifier} not found")
            album = _album_model_from_data(data)
            if not album.identifier:
                album.identifier = identifier
            return album
        except ModelNotFound:
            raise
        except Exception as e:
            raise ModelNotFound(f"Album {identifier} not found: {e}")

    def album_create_songs_rd(self, album):
        if self._api is None:
            return create_reader([])
        try:
            data = self._api.get_album(album.identifier)
            tracks = data.get("tracks", {}).get("items", []) if data else []
            songs = []
            for track in tracks:
                try:
                    songs.append(_track_to_model(track))
                except Exception:
                    continue
            return create_reader(songs)
        except Exception as e:
            logger.warning(f"Get album songs failed: {e}")
            return create_reader([])

    def artist_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Artist {identifier} not found")
        try:
            data = self._api.get_artist(identifier)
            if not data:
                raise ModelNotFound(f"Artist {identifier} not found")
            artist = _artist_model_from_data(data)
            if not artist.identifier:
                artist.identifier = identifier
            return artist
        except ModelNotFound:
            raise
        except Exception as e:
            raise ModelNotFound(f"Artist {identifier} not found: {e}")

    def artist_create_songs_rd(self, artist):
        return create_reader([])

    def artist_create_albums_rd(self, artist):
        return create_reader([])

    def playlist_get(self, identifier):
        if self._api is None:
            raise ModelNotFound(f"Playlist {identifier} not found")
        try:
            data = self._api.get_playlist(identifier)
            if not data:
                raise ModelNotFound(f"Playlist {identifier} not found")
            tracks_data = data.get("content", {}).get("items", [])
            songs = []
            for item in tracks_data:
                track = item.get("itemV2", {}).get("data", {})
                if track.get("uri", "").startswith("spotify:track:"):
                    try:
                        songs.append(_track_to_model(track))
                    except Exception:
                        continue
            from feeluown.library import PlaylistModel
            uri = data.get("uri", "")
            pid = uri.rsplit(":", 1)[-1] if uri else identifier
            images_items = data.get("images", {}).get("items", [])
            cover_sources = images_items[0].get("sources", []) if images_items else []
            return PlaylistModel(
                identifier=pid,
                source=SOURCE,
                name=data.get("name", ""),
                cover=_get_image_url(cover_sources),
                description=data.get("description", "") or "",
            )
        except ModelNotFound:
            raise
        except Exception as e:
            raise ModelNotFound(f"Playlist {identifier} not found: {e}")

    def playlist_create_songs_rd(self, playlist):
        from feeluown.utils.reader import SequentialReader

        if self._api is None:
            return create_reader([])

        api = self._api
        pid = playlist.identifier
        page_size = 100

        def _extract_tracks(data):
            content = data.get("content", {})
            for item in content.get("items", []):
                track = item.get("itemV2", {}).get("data", {})
                if track.get("uri", "").startswith("spotify:track:"):
                    try:
                        yield _track_to_model(track)
                    except Exception:
                        continue

        def _gen():
            offset = 0
            total = None
            while total is None or offset < total:
                data = api.get_playlist(pid, limit=page_size, offset=offset)
                content = data.get("content", {})
                if total is None:
                    total = content.get("totalCount", 0)
                items = content.get("items", [])
                if not items:
                    break
                yield from _extract_tracks(data)
                offset += len(items)

        try:
            # 预取第一页以获取 totalCount
            first = api.get_playlist(pid, limit=page_size, offset=0)
            total = first.get("content", {}).get("totalCount", 0)

            def _gen_from_first():
                yield from _extract_tracks(first)
                offset = len(first.get("content", {}).get("items", []))
                while offset < total:
                    data = api.get_playlist(pid, limit=page_size, offset=offset)
                    items = data.get("content", {}).get("items", [])
                    if not items:
                        break
                    yield from _extract_tracks(data)
                    offset += len(items)

            return SequentialReader(_gen_from_first(), total)
        except Exception as e:
            logger.warning(f"Get playlist songs failed: {e}")
            return create_reader([])

    def playlist_add_song(self, playlist, song):
        if self._api is None:
            return False
        playlist._cache.pop("songs", None)
        return self._api.add_to_playlist(playlist.identifier, song.identifier)

    def playlist_remove_song(self, playlist, song):
        if self._api is None:
            return False
        playlist._cache.pop("songs", None)
        return self._api.remove_from_playlist(playlist.identifier, song.identifier)

    def current_user_list_playlists(self):
        user = self.get_current_user()
        if user is None or self._api is None:
            return []
        cached = user.cache_get("playlists")
        if cached[1]:
            return cached[0]
        try:
            raw = self._api.get_user_playlists()
            playlists = []
            for item in raw:
                pl = item.get("data", item)
                pid = pl.get("uri", "").rsplit(":", 1)[-1] or pl.get("id", "")
                name = pl.get("name", "")
                if pid and name:
                    playlists.append(BriefPlaylistModel(
                        identifier=pid,
                        source=SOURCE,
                        name=name,
                    ))
            user.cache_set("playlists", playlists)
            return playlists
        except Exception as e:
            logger.warning(f"List playlists failed: {e}")
            return []

    def current_user_fav_create_songs_rd(self):
        user = self.get_current_user()
        if user is None or self._api is None:
            return create_reader([])
        try:
            # 通过 libraryV3 获取收藏的歌曲
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            import json
            params = {
                "operationName": "libraryV3",
                "variables": json.dumps({
                    "filters": ["Tracks"],
                    "order": None,
                    "textFilter": "",
                    "features": ["LIKED_SONGS", "YOUR_EPISODES", "PRERELEASES"],
                    "limit": 50,
                    "offset": 0,
                    "flatten": False,
                    "expandedFolders": [],
                    "folderUri": None,
                    "includeFoldersWhenFlattening": True,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._api._song.base.part_hash("libraryV3"),
                    }
                }),
            }
            resp = self._api._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                logger.warning(f"Get saved tracks failed: {resp.error.string}")
                return create_reader([])
            data = resp.response.get("data", {})
            items = data.get("me", {}).get("libraryV3", {}).get("items", [])
            songs = []
            for item in items:
                wrapper = item.get("item", {})
                uri = wrapper.get("_uri", "")
                if not uri.startswith("spotify:track:"):
                    continue
                track_data = wrapper.get("data", {})
                if track_data.get("id") or uri:
                    try:
                        songs.append(_track_to_model(track_data))
                    except Exception:
                        continue
            return create_reader(songs)
        except Exception as e:
            logger.warning(f"Get saved tracks failed: {e}")
            return create_reader([])

    def current_user_fav_create_playlists_rd(self):
        # Spotify 没有独立的"收藏歌单"概念，libraryV3 已包含全部歌单
        user = self.get_current_user()
        if user is None:
            return create_reader([])
        return create_reader([])

    def current_user_fav_create_albums_rd(self):
        user = self.get_current_user()
        if user is None or self._api is None:
            return create_reader([])
        try:
            albums_data = self._api.get_saved_albums()
            albums = []
            for album_data in albums_data:
                try:
                    albums.append(BriefAlbumModel(
                        identifier=album_data.get("id", ""),
                        source=SOURCE,
                        name=album_data.get("name", ""),
                        artists_name=album_data.get("artist", ""),
                    ))
                except Exception:
                    continue
            return create_reader(albums)
        except Exception as e:
            logger.warning(f"Get saved albums failed: {e}")
            return create_reader([])

    def current_user_fav_create_artists_rd(self):
        user = self.get_current_user()
        if user is None or self._api is None:
            return create_reader([])
        try:
            artists_data = self._api.get_saved_artists()
            artists = []
            for artist_data in artists_data:
                try:
                    artists.append(BriefArtistModel(
                        identifier=artist_data.get("id", ""),
                        source=SOURCE,
                        name=artist_data.get("name", ""),
                    ))
                except Exception:
                    continue
            return create_reader(artists)
        except Exception as e:
            logger.warning(f"Get saved artists failed: {e}")
            return create_reader([])

    def rec_list_daily_songs(self):
        if self._api is None:
            return []
        try:
            user = self.get_current_user()
            if user is None:
                return []
            # 通过 userTopContent 获取热门歌曲作为每日推荐
            tracks = self._api.get_top_tracks(limit=30)
            songs = []
            for track in tracks:
                try:
                    songs.append(_track_to_model(track))
                except Exception:
                    continue
            return songs
        except Exception as e:
            logger.warning(f"Get daily songs failed: {e}")
            return []

    def rec_list_daily_playlists(self):
        if self._api is None:
            return []
        try:
            user = self.get_current_user()
            if user is None:
                return []
            # 获取推荐歌单
            rec_playlists = self._api.get_recommendation_playlists()
            playlists = []
            for pl_data in rec_playlists:
                try:
                    playlists.append(BriefPlaylistModel(
                        identifier=pl_data.get("id", ""),
                        source=SOURCE,
                        name=pl_data.get("name", ""),
                    ))
                except Exception:
                    continue
            return playlists
        except Exception as e:
            logger.warning(f"Get daily playlists failed: {e}")
            return []

    def rec_list_collections(self, limit: int = None) -> list:
        """返回推荐集合（每日推荐、排行榜、红心雷达等）。"""
        if self._api is None:
            return []
        try:
            user = self.get_current_user()
            if user is None:
                return []
            collections = []

            # 1. 每日推荐歌曲
            try:
                daily_songs = self.rec_list_daily_songs()
                if daily_songs:
                    collections.append(Collection(
                        name="每日推荐",
                        type_=CollectionType.only_songs,
                        models=daily_songs,
                        description="根据你的收听习惯生成的每日推荐歌曲",
                    ))
            except Exception as e:
                logger.warning(f"Get daily songs collection failed: {e}")

            # 2. 推荐歌单
            try:
                daily_playlists = self.rec_list_daily_playlists()
                if daily_playlists:
                    collections.append(Collection(
                        name="推荐歌单",
                        type_=CollectionType.only_playlists,
                        models=daily_playlists,
                        description="为你精选的个性化歌单",
                    ))
            except Exception as e:
                logger.warning(f"Get daily playlists collection failed: {e}")

            # 3. 排行榜
            try:
                charts = self._api.get_charts()
                chart_playlists = []
                for chart_data in charts:
                    try:
                        chart_playlists.append(BriefPlaylistModel(
                            identifier=chart_data.get("id", ""),
                            source=SOURCE,
                            name=chart_data.get("name", ""),
                        ))
                    except Exception:
                        continue
                if chart_playlists:
                    collections.append(Collection(
                        name="排行榜",
                        type_=CollectionType.only_playlists,
                        models=chart_playlists,
                        description="热门排行榜歌单",
                    ))
            except Exception as e:
                logger.warning(f"Get charts collection failed: {e}")

            if limit is not None:
                collections = collections[:limit]
            return collections
        except Exception as e:
            logger.warning(f"Get collections failed: {e}")
            return []

    def rec_a_collection_of_songs(self) -> Optional[Collection]:
        """返回红心雷达（基于 Daily Mix 的推荐歌曲）。"""
        if self._api is None:
            return None
        try:
            user = self.get_current_user()
            if user is None:
                return None
            heart_radar_tracks = self._api.get_heart_radar_tracks()
            if not heart_radar_tracks:
                return None
            songs = []
            for track in heart_radar_tracks:
                try:
                    songs.append(_track_to_model(track))
                except Exception:
                    continue
            if not songs:
                return None
            return Collection(
                name="红心雷达",
                type_=CollectionType.only_songs,
                models=songs,
                description="基于你喜欢的歌曲生成的推荐",
            )
        except Exception as e:
            logger.warning(f"Get heart radar failed: {e}")
            return None


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


def _normalize_track_data(data: dict) -> dict:
    """将 GraphQL 返回的 track 数据规范化为 SpotifySong 可接受的格式。"""
    result = dict(data)
    # uri → id（歌单中的 track 用 uri 而非 id）
    if "id" not in result and "uri" in result:
        result["id"] = result["uri"].rsplit(":", 1)[-1]
    # trackDuration.totalMilliseconds → duration_ms
    duration = result.pop("trackDuration", None)
    if isinstance(duration, dict) and "duration_ms" not in result:
        result["duration_ms"] = duration.get("totalMilliseconds")
    # artists: {"items": [{"profile": {"name": ...}, "uri": ...}]} → [{"id": ..., "name": ...}]
    artists = result.get("artists")
    if isinstance(artists, dict):
        items = artists.get("items", [])
        result["artists"] = [
            {
                "id": a.get("uri", "").rsplit(":", 1)[-1],
                "name": a.get("profile", {}).get("name", ""),
            }
            for a in items
        ]
    # albumOfTrack → album，coverArt.sources → images
    album = result.pop("albumOfTrack", None)
    if isinstance(album, dict) and "album" not in result:
        result["album"] = {
            "id": album.get("uri", "").rsplit(":", 1)[-1],
            "name": album.get("name", ""),
            "images": album.get("coverArt", {}).get("sources", []),
        }
    return result


def _track_to_model(track_data: dict) -> "SongModel":
    from fuo_spotify.schemas import SpotifySong
    from feeluown.library import SongModel

    normalized = _normalize_track_data(track_data)
    song_data = SpotifySong.model_validate(normalized)
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


def _album_model_from_data(data: dict) -> "AlbumModel":
    from feeluown.library import AlbumModel
    artists = []
    for a in data.get("artists", []):
        artists.append(BriefArtistModel(
            identifier=a.get("id", ""),
            source=SOURCE,
            name=a.get("name", ""),
        ))
    return AlbumModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
        cover=_get_image_url(data.get("cover", {}).get("sources", [])),
        artists=artists,
        description="",
        songs=[],
    )


def _artist_model_from_data(data: dict) -> "ArtistModel":
    from feeluown.library import ArtistModel
    return ArtistModel(
        identifier=data.get("id", ""),
        source=SOURCE,
        name=data.get("name", ""),
        pic_url=_get_image_url(data.get("visuals", {}).get("avatarImage", {}).get("sources", [])),
        description="",
        hot_songs=[],
        aliases=[],
    )
