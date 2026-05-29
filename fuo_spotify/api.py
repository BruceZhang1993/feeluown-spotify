import json
import logging
from typing import Any, Generator, Mapping, Optional

import spotapi

from fuo_spotify.excs import SpotifyAPIError, SpotifyTrackError

logger = logging.getLogger(__name__)


class SpotifyApi:
    def __init__(self, cfg: spotapi.Config):
        self._song = spotapi.Song(cfg)
        self._artist = spotapi.Artist(cfg)
        self._public_album = spotapi.PublicAlbum(cfg)
        self._public_playlist = spotapi.PublicPlaylist(cfg)
        self._user = spotapi.User(cfg)
        self._client = cfg.client
        self._cfg = cfg

    def search_songs(self, query: str, limit: int = 10, offset: int = 0) -> list[dict]:
        try:
            result = self._song.query_songs(query, limit=limit, offset=offset)
            if isinstance(result, Mapping):
                tracks = result.get("searchV2", {}).get("tracksV2", {}).get("items", [])
                songs = []
                for item in tracks:
                    track_data = item.get("item", {}).get("data", {})
                    if track_data.get("id"):
                        songs.append(track_data)
                return songs
            return []
        except Exception as e:
            raise SpotifyAPIError(f"Search songs failed: {e}") from e

    def search_artists(self, query: str) -> Generator[dict, None, None]:
        try:
            yield from spotapi.Public.artist_search(query)
        except Exception as e:
            raise SpotifyAPIError(f"Search artists failed: {e}") from e

    def search_albums(self, query: str, limit: int = 10) -> list[dict]:
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
                        "sha256Hash": self._cfg.client.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search albums failed: {resp.error.string}")
            albums = resp.response.get("searchV2", {}).get("albumsV2", {}).get("items", [])
            return [album.get("data", {}) for album in albums if album.get("data", {}).get("id")]
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search albums failed: {e}") from e

    def search_playlists(self, query: str, limit: int = 10) -> list[dict]:
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
                        "sha256Hash": self._cfg.client.part_hash("searchDesktop"),
                    }
                }),
            }
            resp = self._client.post(url, params=params, authenticate=True)
            if resp.fail:
                raise SpotifyAPIError(f"Search playlists failed: {resp.error.string}")
            playlists = resp.response.get("searchV2", {}).get("playlistsV2", {}).get("items", [])
            return [pl.get("data", {}) for pl in playlists if pl.get("data", {}).get("id")]
        except SpotifyAPIError:
            raise
        except Exception as e:
            raise SpotifyAPIError(f"Search playlists failed: {e}") from e

    def get_track(self, track_id: str) -> dict:
        try:
            data = self._song.get_track_info(track_id)
            track = data.get("data", {}).get("trackUnion", {})
            if not track:
                raise SpotifyTrackError(f"Track {track_id} not found")
            return track
        except SpotifyTrackError:
            raise
        except Exception as e:
            raise SpotifyTrackError(f"Get track failed: {e}") from e

    def get_artist(self, artist_id: str) -> dict:
        try:
            data = self._artist.get_artist(artist_id)
            return data.get("data", {}).get("artist", {})
        except Exception as e:
            raise SpotifyAPIError(f"Get artist failed: {e}") from e

    def get_album(self, album_id: str) -> dict:
        try:
            data = self._public_album.get_album_info(album_id)
            return data.get("data", {}).get("album", {})
        except Exception as e:
            raise SpotifyAPIError(f"Get album failed: {e}") from e

    def get_playlist(self, playlist_id: str) -> dict:
        try:
            data = self._public_playlist.get_playlist_info(playlist_id)
            return data.get("data", {}).get("playlistV2", {})
        except Exception as e:
            raise SpotifyAPIError(f"Get playlist failed: {e}") from e

    def get_lyrics(self, track_id: str) -> Optional[dict]:
        try:
            url = f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}"
            resp = self._client.get(url, authenticate=True)
            if resp.fail:
                logger.warning(f"Get lyrics failed for {track_id}: {resp.error.string}")
                return None
            return resp.response
        except Exception as e:
            logger.warning(f"Get lyrics failed for {track_id}: {e}")
            return None

    def get_user_info(self) -> dict:
        try:
            return self._user.get_user_info()
        except Exception as e:
            raise SpotifyAPIError(f"Get user info failed: {e}") from e

    def like_song(self, track_id: str) -> bool:
        try:
            self._song.like_song(track_id)
            return True
        except Exception as e:
            logger.error(f"Like song failed: {e}")
            return False

    def add_to_playlist(self, playlist_id: str, track_id: str) -> bool:
        try:
            self._song.add_song_to_playlist(playlist_id, track_id)
            return True
        except Exception as e:
            logger.error(f"Add to playlist failed: {e}")
            return False

    def remove_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        try:
            self._song.remove_song_from_playlist(playlist_id, track_id)
            return True
        except Exception as e:
            logger.error(f"Remove from playlist failed: {e}")
            return False

    def get_radio_tracks(self, track_id: str) -> list[dict]:
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
            return tracks
        except Exception as e:
            logger.error(f"Get radio tracks failed: {e}")
            return []
