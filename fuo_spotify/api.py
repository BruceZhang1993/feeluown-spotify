import json
import logging
import requests
from typing import List, Mapping, Optional, Tuple

import spotapi

from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError

logger = logging.getLogger(__name__)

_BASE62 = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Accept": "*/*",
    "Referer": "https://open.spotify.com/",
    "Origin": "https://open.spotify.com",
}

STORAGE_RESOLVE_URL = (
    "https://spclient.wg.spotify.com"
    "/storage-resolve/v2/files/audio/interactive/10/{file_id}"
    "?version=10000000&product=9&platform=39&alt=json"
)

# 格式优先级（数字越小越优先），来自 librespot AudioFileFormat 枚举
# OGG 类型（0, 1, 2）已排除
_FORMAT_PRIORITY = {
    16: 0,  # FLAC
    4: 1,   # MP3_320
    3: 2,   # MP3_256
    5: 3,   # MP3_160
    11: 4,  # AAC_320
    10: 5,  # AAC_160
    6: 6,   # MP3_96
    8: 7,   # AAC_48
}


def _base62_to_hex(s: str) -> str:
    """将 base62 编码的 Spotify ID 转为 128 位 hex UUID。"""
    n = 0
    for c in s:
        n = n * 62 + _BASE62.index(c)
    return format(n, '032x')


def _parse_audio_files(data: bytes) -> List[Tuple[bytes, int]]:
    """从 TRACK_V4 protobuf 响应中解析 AudioFile 条目。

    AudioFile 的 protobuf 结构：
      field 1 (tag 0x0a): file_id, bytes, 20 字节
      field 2 (tag 0x10): format, varint enum

    Returns:
        [(file_id_bytes, format_enum), ...] 列表
    """
    results = []
    i = 0
    while i < len(data) - 22:
        # 搜索 AudioFile 模式: 0x0a 0x14 + 20 bytes file_id + 0x10 + format
        if data[i] == 0x0a and data[i + 1] == 0x14:
            file_id = data[i + 2:i + 22]
            # 检查后面是否紧跟 format 字段 (0x10 + varint)
            if i + 22 < len(data) and data[i + 22] == 0x10:
                fmt = data[i + 23] if i + 23 < len(data) else -1
                results.append((file_id, fmt))
                i += 24
                continue
        i += 1
    return results


class SpotifyApi:
    def __init__(self, login: spotapi.Login):
        self._login = login
        self._client = login.client
        self._user = spotapi.User(login)
        self._artist = spotapi.Artist(login)
        self._song = spotapi.Song(client=login.client)

    def search_songs(self, query: str, limit: int = 10, offset: int = 0) -> list[dict]:
        logger.debug("Searching songs: query=%s, limit=%d, offset=%d", query, limit, offset)
        try:
            result = self._song.query_songs(query, limit=limit, offset=offset)
            if isinstance(result, Mapping):
                data = result.get("data", result)
                tracks = data.get("searchV2", {}).get("tracksV2", {}).get("items", [])
                songs = []
                for item in tracks:
                    track_data = item.get("item", {}).get("data", {})
                    if track_data.get("id"):
                        songs.append(track_data)
                logger.info("Search songs: query=%s, found=%d", query, len(songs))
                return songs
            return []
        except Exception as e:
            raise SpotifyAPIError(f"Search songs failed: {e}") from e

    def search_artists(self, query: str, limit: int = 10) -> list[dict]:
        logger.debug("Searching artists: query=%s", query)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "searchDesktop",
                "variables": json.dumps({
                    "searchTerm": query,
                    "offset": 0,
                    "limit": limit,
                    "numberOfTopResults": 5,
                    "includeAudiobooks": False,
                    "includeArtistHasConcertsField": False,
                    "includePreReleases": False,
                    "includeLocalConcertsField": False,
                    "searchReturnConstructEntity": False,
                    "includeAuthors": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search artists failed: {resp.error.string}")
            data = resp.response.get("data", {})
            artists = data.get("searchV2", {}).get("artists", {}).get("items", [])
            result = [a.get("data", a) for a in artists]
            logger.info("Search artists: query=%s, found=%d", query, len(result))
            return result
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search artists failed: {e}") from e

    def search_albums(self, query: str, limit: int = 10) -> list[dict]:
        logger.debug("Searching albums: query=%s, limit=%d", query, limit)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "searchDesktop",
                "variables": json.dumps({
                    "searchTerm": query,
                    "offset": 0,
                    "limit": limit,
                    "numberOfTopResults": 5,
                    "includeAudiobooks": False,
                    "includeArtistHasConcertsField": False,
                    "includePreReleases": False,
                    "includeLocalConcertsField": False,
                    "searchReturnConstructEntity": False,
                    "includeAuthors": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search albums failed: {resp.error.string}")
            data = resp.response.get("data", {})
            albums = data.get("searchV2", {}).get("albumsV2", {}).get("items", [])
            result = [album.get("data", {}) for album in albums if album.get("data", {}).get("id")]
            logger.info("Search albums: query=%s, found=%d", query, len(result))
            return result
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search albums failed: {e}") from e

    def search_playlists(self, query: str, limit: int = 10) -> list[dict]:
        logger.debug("Searching playlists: query=%s, limit=%d", query, limit)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "searchDesktop",
                "variables": json.dumps({
                    "searchTerm": query,
                    "offset": 0,
                    "limit": limit,
                    "numberOfTopResults": 5,
                    "includeAudiobooks": False,
                    "includeArtistHasConcertsField": False,
                    "includePreReleases": False,
                    "includeLocalConcertsField": False,
                    "searchReturnConstructEntity": False,
                    "includeAuthors": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search playlists failed: {resp.error.string}")
            data = resp.response.get("data", {})
            playlists = data.get("searchV2", {}).get("playlistsV2", {}).get("items", [])
            result = [pl.get("data", {}) for pl in playlists if pl.get("data", {}).get("id")]
            logger.info("Search playlists: query=%s, found=%d", query, len(result))
            return result
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search playlists failed: {e}") from e

    def get_track(self, track_id: str) -> dict:
        logger.debug("Getting track: %s", track_id)
        try:
            data = self._song.get_track_info(track_id)
            track = data.get("data", {}).get("trackUnion", {})
            if not track:
                raise SpotifyTrackError(f"Track {track_id} not found")
            logger.info("Got track: %s, name=%s", track_id, track.get("name", ""))
            return track
        except SpotifyTrackError:
            raise
        except Exception as e:
            raise SpotifyTrackError(f"Get track failed: {e}") from e

    def get_artist(self, artist_id: str) -> dict:
        logger.debug("Getting artist: %s", artist_id)
        try:
            data = self._artist.get_artist(artist_id)
            result = data.get("data", {}).get("artistUnion", {})
            logger.info("Got artist: %s, name=%s", artist_id, result.get("profile", {}).get("name", ""))
            return result
        except Exception as e:
            raise SpotifyAPIError(f"Get artist failed: {e}") from e

    def get_album(self, album_id: str) -> dict:
        logger.debug("Getting album: %s", album_id)
        try:
            public_album = spotapi.PublicAlbum(album_id, client=self._client)
            data = public_album.get_album_info()
            result = data.get("data", {}).get("album", {})
            logger.info("Got album: %s, name=%s", album_id, result.get("name", ""))
            return result
        except Exception as e:
            raise SpotifyAPIError(f"Get album failed: {e}") from e

    def get_playlist(self, playlist_id: str, limit: int = 25, offset: int = 0) -> dict:
        """获取播放列表元数据及歌曲（单页）。"""
        logger.debug("Getting playlist: %s, limit=%d, offset=%d",
                      playlist_id, limit, offset)
        try:
            public_playlist = spotapi.PublicPlaylist(playlist_id, client=self._client)
            data = public_playlist.get_playlist_info(limit=limit, offset=offset)
            result = data.get("data", {}).get("playlistV2", {})
            logger.info("Got playlist: %s, name=%s", playlist_id, result.get("name", ""))
            return result
        except Exception as e:
            raise SpotifyAPIError(f"Get playlist failed: {e}") from e

    def get_lyrics(self, track_id: str) -> Optional[dict]:
        logger.debug("Getting lyrics: %s", track_id)
        try:
            url = f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}"
            resp = self._song.base.client.get(url, authenticate=True)
            if resp.fail:
                logger.warning(f"Get lyrics failed for {track_id}: {resp.error.string}")
                return None
            logger.info("Got lyrics: %s", track_id)
            return resp.response
        except Exception as e:
            logger.warning(f"Get lyrics failed for {track_id}: {e}")
            return None

    def get_track_stream_url(self, track_id: str) -> Optional[str]:
        """获取 track 的完整音频 CDN URL（仅未加密文件）。"""
        logger.debug("Getting stream URL: %s", track_id)
        try:
            file_id = self._get_best_file_id(track_id)
            if not file_id:
                logger.warning("No usable FileId found for %s", track_id)
                return None

            file_id_hex = file_id.hex()
            logger.debug("Using FileId %s for %s", file_id_hex, track_id)

            url = STORAGE_RESOLVE_URL.format(file_id=file_id_hex)
            headers = self._get_auth_headers()
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            urls = data.get("cdnurl", [])
            if not urls:
                raise RuntimeError(f"No CDN URL for file_id={file_id}")
            return urls[1]
        except Exception as e:
            logger.warning(f"Get stream URL failed for {track_id}: {e}")
            return None

    def get_encrypted_file_id(self, track_id: str) -> Optional[bytes]:
        """获取 track 的最佳 FileId（用于 Widevine 解密）。"""
        return self._get_best_file_id(track_id)

    def get_auth_and_client_token(self) -> tuple[str, str]:
        """返回 (access_token, client_token)。"""
        self._ensure_auth()
        base = self._song.base
        token = base.access_token if isinstance(base.access_token, str) else ""
        client_token = base.client_token if isinstance(base.client_token, str) else ""
        return token, client_token

    def _ensure_auth(self):
        """确保 spotapi base client 已完成认证初始化（获取 access_token 等）。"""
        base = self._song.base
        if type(base.access_token).__name__ == "_UndefinedType":
            # 触发一次 authenticate 请求来初始化 tokens
            try:
                base.client.get(
                    "https://spclient.wg.spotify.com/",
                    authenticate=True,
                )
            except Exception:
                pass  # 可能 404，但认证 token 已初始化

    def _get_auth_headers(self) -> dict:
        """获取 Spotify API 认证头（需先调 _ensure_auth）。"""
        base = self._song.base
        headers = {
            "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64; rv:151.0) "
                           "Gecko/20100101 Firefox/151.0"),
            "Accept": "application/protobuf",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "https://open.spotify.com/",
            "Origin": "https://open.spotify.com",
        }
        token = base.access_token
        if isinstance(token, str):
            headers["authorization"] = f"Bearer {token}"
        client_token = base.client_token
        if isinstance(client_token, str):
            headers["client-token"] = client_token
        return headers

    def _get_best_file_id(self, track_id: str) -> Optional[bytes]:
        """从 track-playback API 获取用于 seektable/widevine 的 FileId。

        Args:
            track_id: Spotify track ID

        Returns:
            20 字节的 FileId bytes，或 None
        """
        import requests as _requests

        try:
            self._ensure_auth()

            track_uri = f"spotify:track:{track_id}"
            url = ("https://gue1-spclient.spotify.com"
                   f"/track-playback/v1/media/{track_uri}")
            params = {
                "manifestFileFormat": "file_ids_mp4",
            }

            for attempt in range(2):
                headers = self._get_auth_headers()
                cookies = dict(self._song.base.client.cookies)
                resp = _requests.get(
                    url, params=params, headers=headers,
                    cookies=cookies, timeout=10)
                if resp.status_code == 401 and attempt == 0:
                    logger.debug("Token expired, refreshing...")
                    base = self._song.base
                    base.get_session()
                    base.get_client_token()
                    continue
                break

            if resp.status_code != 200:
                logger.warning("Get track-playback failed for %s: HTTP %d",
                               track_id, resp.status_code)
                return None

            data = resp.json()
            media = data.get("media", {})
            track_data = media.get(track_uri, {})
            manifest = track_data.get("item", {}).get("manifest", {})
            mp4_files = manifest.get("file_ids_mp4", [])

            if not mp4_files:
                logger.warning("No file_ids_mp4 entries for %s", track_id)
                return None

            file_id_str = mp4_files[0].get("file_id", "")
            if not file_id_str:
                logger.warning("Empty file_id for %s", track_id)
                return None

            file_id = bytes.fromhex(file_id_str)
            logger.info("Selected file_id for %s: %s", track_id, file_id_str)
            return file_id

        except Exception as e:
            logger.warning(f"Get best file_id failed for {track_id}: {e}")
            return None

    def get_user_info(self) -> dict:
        logger.debug("Getting user info")
        try:
            result = self._user.get_user_info()
            logger.info("Got user info: %s", result.get("display_name", ""))
            return result
        except Exception as e:
            raise SpotifyAPIError(f"Get user info failed: {e}") from e

    def get_user_playlists(self, limit: int = 50) -> list[dict]:
        """通过 libraryV3 操作获取用户播放列表。"""
        logger.debug("Getting user playlists: limit=%d", limit)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "libraryV3",
                "variables": json.dumps({
                    "filters": [],
                    "order": None,
                    "textFilter": "",
                    "features": ["LIKED_SONGS", "YOUR_EPISODES", "PRERELEASES"],
                    "limit": limit,
                    "offset": 0,
                    "flatten": False,
                    "expandedFolders": [],
                    "folderUri": None,
                    "includeFoldersWhenFlattening": True,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("libraryV3"),
                    }
                }),
            }
            resp = self._song.base.client.post(
                url, params=params, authenticate=True,
            )
            if resp.fail:
                raise SpotifyAPIError(
                    f"Get user playlists failed: {resp.error.string}"
                )
            data = resp.response.get("data", {})
            items = data.get("me", {}).get(
                "libraryV3", {}
            ).get("items", [])
            # libraryV3 返回的 items 包含多种类型（Playlist、Album、Artist 等），
            # 只提取播放列表类型的 item
            playlists = []
            for item in items:
                wrapper = item.get("item", {})
                uri = wrapper.get("_uri", "")
                if not uri.startswith("spotify:playlist:"):
                    continue
                data = wrapper.get("data", {})
                pid = uri.rsplit(":", 1)[-1]
                name = data.get("name", "")
                if pid and name:
                    playlists.append({"id": pid, "name": name})
            logger.info(
                "Got user playlists: count=%d", len(playlists),
            )
            return playlists
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(
                f"Get user playlists failed: {e}"
            ) from e

    def like_song(self, track_id: str) -> bool:
        logger.debug("Liking song: %s", track_id)
        try:
            self._song.like_song(track_id)
            logger.info("Liked song: %s", track_id)
            return True
        except Exception as e:
            logger.error(f"Like song failed: {e}")
            return False

    def add_to_playlist(self, playlist_id: str, track_id: str) -> bool:
        logger.debug("Adding to playlist: track=%s, playlist=%s", track_id, playlist_id)
        try:
            self._song.add_song_to_playlist(playlist_id, track_id)
            logger.info("Added to playlist: track=%s, playlist=%s", track_id, playlist_id)
            return True
        except Exception as e:
            logger.error(f"Add to playlist failed: {e}")
            return False

    def remove_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        logger.debug("Removing from playlist: track=%s, playlist=%s", track_id, playlist_id)
        try:
            self._song.remove_song_from_playlist(playlist_id, track_id)
            logger.info("Removed from playlist: track=%s, playlist=%s", track_id, playlist_id)
            return True
        except Exception as e:
            logger.error(f"Remove from playlist failed: {e}")
            return False

    def get_radio_tracks(self, track_id: str) -> list[dict]:
        logger.debug("Getting radio tracks: %s", track_id)
        try:
            data = self._song.playlist(track_id)
            if not data:
                return []
            items = data.get("content", {}).get("items", [])
            tracks = []
            for item in items:
                track = item.get("item", {})
                if track.get("id"):
                    tracks.append(track)
            logger.info("Got radio tracks: %s, count=%d", track_id, len(tracks))
            return tracks
        except Exception as e:
            logger.error(f"Get radio tracks failed: {e}")
            return []
