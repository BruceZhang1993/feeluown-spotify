import json
import logging
from typing import Mapping, Optional

import spotapi

from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError

logger = logging.getLogger(__name__)


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

    def get_user_info(self) -> dict:
        logger.debug("Getting user info")
        try:
            result = self._user.get_user_info()
            logger.info("Got user info: %s", result.get("display_name", ""))
            return result
        except Exception as e:
            raise SpotifyAPIError(f"Get user info failed: {e}") from e

    def get_current_user_profile(self) -> dict:
        """通过 profileAttributes GraphQL 获取当前用户 profile（含头像和显示名）。"""
        logger.debug("Getting current user profile via profileAttributes")
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "profileAttributes",
                "variables": json.dumps({}),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("profileAttributes"),
                    }
                }),
            }
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                logger.warning(f"Get current user profile failed: {resp.error.string}")
                return {}
            profile = resp.response.get("data", {}).get("me", {}).get("profile", {})
            logger.info("Got current user profile: %s", profile.get("name", ""))
            return profile
        except Exception as e:
            logger.warning(f"Get current user profile failed: {e}")
            return {}

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

    # ---- 发现页面（使用 userTopContent 和 fetchPlaylistMetadata）----

    def get_user_top_content(self, limit: int = 20) -> dict:
        """通过 userTopContent 获取用户热门歌曲和歌手。"""
        logger.debug("Getting user top content: limit=%d", limit)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "userTopContent",
                "variables": json.dumps({
                    "topArtistsInput": {"limit": limit, "offset": 0},
                    "topTracksInput": {"limit": limit, "offset": 0},
                    "includeTopTracks": True,
                    "includeTopArtists": True,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("userTopContent"),
                    }
                }),
            }
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                logger.warning(f"Get user top content failed: {resp.error.string}")
                return {}
            data = resp.response.get("data", {}).get("me", {}).get("profile", {})
            logger.info("Got user top content")
            return data
        except Exception as e:
            logger.warning(f"Get user top content failed: {e}")
            return {}

    def get_top_tracks(self, limit: int = 20) -> list[dict]:
        """获取用户热门歌曲（用于每日推荐/红心雷达）。"""
        logger.debug("Getting top tracks")
        try:
            data = self.get_user_top_content(limit)
            items = data.get("topTracks", {}).get("items", [])
            tracks = []
            for item in items:
                track_data = item.get("data", {})
                if track_data.get("uri", "").startswith("spotify:track:"):
                    tracks.append(track_data)
            logger.info("Got top tracks: count=%d", len(tracks))
            return tracks
        except Exception as e:
            logger.warning(f"Get top tracks failed: {e}")
            return []

    def get_top_artists(self, limit: int = 20) -> list[dict]:
        """获取用户热门歌手。"""
        logger.debug("Getting top artists")
        try:
            data = self.get_user_top_content(limit)
            items = data.get("topArtists", {}).get("items", [])
            artists = []
            for item in items:
                artist_data = item.get("data", {})
                uri = artist_data.get("uri", "")
                if uri.startswith("spotify:artist:"):
                    aid = uri.rsplit(":", 1)[-1]
                    name = artist_data.get("profile", {}).get("name", "")
                    images = artist_data.get("visuals", {}).get("avatarImage", {}).get("sources", [])
                    pic_url = max(images, key=lambda s: s.get("width", 0)).get("url", "") if images else ""
                    if aid and name:
                        artists.append({"id": aid, "name": name, "pic_url": pic_url})
            logger.info("Got top artists: count=%d", len(artists))
            return artists
        except Exception as e:
            logger.warning(f"Get top artists failed: {e}")
            return []

    def get_fetch_playlist_metadata(self, playlist_uri: str) -> dict:
        """通过 fetchPlaylistMetadata 获取歌单元数据。"""
        logger.debug("Fetching playlist metadata: %s", playlist_uri)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "fetchPlaylistMetadata",
                "variables": json.dumps({
                    "uri": playlist_uri,
                    "enableWatchFeedEntrypoint": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash("fetchPlaylistMetadata"),
                    }
                }),
            }
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                logger.warning(f"Fetch playlist metadata failed: {resp.error.string}")
                return {}
            data = resp.response.get("data", {}).get("playlistV2", {})
            logger.info("Fetched playlist metadata: %s", data.get("name", ""))
            return data
        except Exception as e:
            logger.warning(f"Fetch playlist metadata failed: {e}")
            return {}

    # 已知的 Spotify 官方 Daily Mix / 推荐歌单 URI
    _DAILY_MIX_URIS = [
        "spotify:playlist:37i9dQZF1E3AFmNvSCnUvC",  # Daily Mix 1
        "spotify:playlist:37i9dQZF1E39CIPVz2JxSS",  # Daily Mix 2
        "spotify:playlist:37i9dQZF1E37CwNSRFKLRH",  # Daily Mix 3
        "spotify:playlist:37i9dQZF1E3A8XMpXkBWRU",  # Daily Mix 4
        "spotify:playlist:37i9dQZF1E35D2ZVOTNmEL",  # Daily Mix 5
        "spotify:playlist:37i9dQZF1E3aQV6H0TO1bI",  # Daily Mix 6
    ]

    def get_daily_mix_playlists(self) -> list[dict]:
        """获取 Daily Mix 系列歌单。"""
        logger.debug("Getting daily mix playlists")
        daily_mixes = []
        for uri in self._DAILY_MIX_URIS:
            try:
                data = self.get_fetch_playlist_metadata(uri)
                name = data.get("name", "")
                if not name:
                    continue
                pid = uri.rsplit(":", 1)[-1]
                images = data.get("images", {}).get("items", [])
                cover = images[0].get("sources", [{}])[0].get("url", "") if images else ""
                daily_mixes.append({
                    "id": pid,
                    "name": name,
                    "cover": cover,
                    "description": data.get("attributes", {}).get("description", ""),
                })
            except Exception:
                continue
        logger.info("Got daily mix playlists: count=%d", len(daily_mixes))
        return daily_mixes

    def get_recommendation_playlists(self) -> list[dict]:
        """获取推荐歌单（Discover Weekly, Release Radar 等）。"""
        logger.debug("Getting recommendation playlists")
        rec_uris = [
            "spotify:playlist:37i9dQZEVXcJjYFSYR3DjA",  # Discover Weekly
            "spotify:playlist:37i9dQZEVXcWwQ7d1FPXPh",  # Release Radar
            "spotify:playlist:37i9dQZEVXcMaGwUEMFBKQ",  # Repeat Rewind
            "spotify:playlist:37i9dQZEVXcNCKj7ZI5qfM",  # Time Capsule
        ]
        rec_playlists = []
        for uri in rec_uris:
            try:
                data = self.get_fetch_playlist_metadata(uri)
                name = data.get("name", "")
                if not name:
                    continue
                pid = uri.rsplit(":", 1)[-1]
                images = data.get("images", {}).get("items", [])
                cover = images[0].get("sources", [{}])[0].get("url", "") if images else ""
                rec_playlists.append({
                    "id": pid,
                    "name": name,
                    "cover": cover,
                    "description": data.get("attributes", {}).get("description", ""),
                })
            except Exception:
                continue
        logger.info("Got recommendation playlists: count=%d", len(rec_playlists))
        return rec_playlists

    def get_charts(self) -> list[dict]:
        """获取排行榜歌单。"""
        logger.debug("Getting charts")
        chart_uris = [
            "spotify:playlist:37i9dQZEVXbMDoHDwVN2tF",  # Top 50 - Global
            "spotify:playlist:37i9dQZEVXbKuaTI1Z1Afx",  # Viral 50 - Global
            "spotify:playlist:37i9dQZEVXbIPWwFssbupI",  # Top 50 - Japan
            "spotify:playlist:37i9dQZEVXbNFm4N5qvIqI",  # Viral 50 - Japan
        ]
        charts = []
        for uri in chart_uris:
            try:
                data = self.get_fetch_playlist_metadata(uri)
                name = data.get("name", "")
                if not name:
                    continue
                pid = uri.rsplit(":", 1)[-1]
                images = data.get("images", {}).get("items", [])
                cover = images[0].get("sources", [{}])[0].get("url", "") if images else ""
                charts.append({
                    "id": pid,
                    "name": name,
                    "cover": cover,
                    "description": data.get("attributes", {}).get("description", ""),
                })
            except Exception:
                continue
        logger.info("Got charts: count=%d", len(charts))
        return charts

    def get_heart_radar_tracks(self) -> list[dict]:
        """获取红心雷达推荐歌曲（基于用户热门歌曲）。"""
        logger.debug("Getting heart radar tracks")
        try:
            tracks = self.get_top_tracks(limit=20)
            logger.info("Got heart radar tracks: count=%d", len(tracks))
            return tracks
        except Exception as e:
            logger.warning(f"Get heart radar tracks failed: {e}")
            return []

    # ---- 我的收藏 ----

    def get_saved_albums(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """获取用户收藏的专辑。"""
        logger.debug("Getting saved albums: limit=%d, offset=%d", limit, offset)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "libraryV3",
                "variables": json.dumps({
                    "filters": ["Albums"],
                    "order": None,
                    "textFilter": "",
                    "features": ["LIKED_SONGS", "YOUR_EPISODES", "PRERELEASES"],
                    "limit": limit,
                    "offset": offset,
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
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Get saved albums failed: {resp.error.string}")
            data = resp.response.get("data", {})
            items = data.get("me", {}).get("libraryV3", {}).get("items", [])
            albums = []
            for item in items:
                wrapper = item.get("item", {})
                uri = wrapper.get("_uri", "")
                if not uri.startswith("spotify:album:"):
                    continue
                album_data = wrapper.get("data", {})
                aid = uri.rsplit(":", 1)[-1]
                name = album_data.get("name", "")
                artists = album_data.get("artists", {}).get("items", [])
                artist_name = artists[0].get("profile", {}).get("name", "") if artists else ""
                images = album_data.get("coverArt", {}).get("sources", [])
                cover = images[0].get("url", "") if images else ""
                if aid and name:
                    albums.append({
                        "id": aid,
                        "name": name,
                        "artist": artist_name,
                        "cover": cover,
                    })
            logger.info("Got saved albums: count=%d", len(albums))
            return albums
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Get saved albums failed: {e}") from e

    def get_saved_artists(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """获取用户关注的歌手。"""
        logger.debug("Getting saved artists: limit=%d, offset=%d", limit, offset)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "libraryV3",
                "variables": json.dumps({
                    "filters": ["Artists"],
                    "order": None,
                    "textFilter": "",
                    "features": ["LIKED_SONGS", "YOUR_EPISODES", "PRERELEASES"],
                    "limit": limit,
                    "offset": offset,
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
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Get saved artists failed: {resp.error.string}")
            data = resp.response.get("data", {})
            items = data.get("me", {}).get("libraryV3", {}).get("items", [])
            artists = []
            for item in items:
                wrapper = item.get("item", {})
                uri = wrapper.get("_uri", "")
                if not uri.startswith("spotify:artist:"):
                    continue
                artist_data = wrapper.get("data", {})
                aid = uri.rsplit(":", 1)[-1]
                name = artist_data.get("profile", {}).get("name", "")
                images = artist_data.get("visuals", {}).get("avatarImage", {}).get("sources", [])
                pic_url = images[0].get("url", "") if images else ""
                if aid and name:
                    artists.append({
                        "id": aid,
                        "name": name,
                        "pic_url": pic_url,
                    })
            logger.info("Got saved artists: count=%d", len(artists))
            return artists
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Get saved artists failed: {e}") from e

    def get_saved_tracks_count(self) -> int:
        """获取用户收藏的歌曲数量。"""
        logger.debug("Getting saved tracks count")
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "libraryV3",
                "variables": json.dumps({
                    "filters": ["Tracks"],
                    "order": None,
                    "textFilter": "",
                    "features": ["LIKED_SONGS", "YOUR_EPISODES", "PRERELEASES"],
                    "limit": 1,
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
            resp = self._song.base.client.post(url, params=params, authenticate=True)
            if resp.fail:
                logger.warning(f"Get saved tracks count failed: {resp.error.string}")
                return 0
            data = resp.response.get("data", {})
            total = data.get("me", {}).get("libraryV3", {}).get("totalCount", 0)
            logger.info("Got saved tracks count: %d", total)
            return total
        except Exception as e:
            logger.warning(f"Get saved tracks count failed: {e}")
            return 0
