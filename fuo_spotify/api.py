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

    def get_playlist(self, playlist_id: str) -> dict:
        logger.debug("Getting playlist: %s", playlist_id)
        try:
            public_playlist = spotapi.PublicPlaylist(playlist_id, client=self._client)
            data = public_playlist.get_playlist_info()
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

    def get_user_playlists(self, limit: int = 50) -> list[dict]:
        logger.debug("Getting user playlists: limit=%d", limit)
        try:
            url = "https://api-partner.spotify.com/pathfinder/v1/query"
            params = {
                "operationName": "queryUserPlaylists",
                "variables": json.dumps({
                    "limit": limit,
                    "offset": 0,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": self._song.base.part_hash(
                            "queryUserPlaylists"
                        ),
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
            playlists = data.get("me", {}).get(
                "playlistsV2", {}
            ).get("items", [])
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
