from pydantic import BaseModel
from typing import Optional


SOURCE = 'spotify'


class SpotifyImage(BaseModel):
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class SpotifyBriefArtist(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class SpotifyBriefAlbum(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None

    @property
    def cover(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifySong(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    duration_ms: Optional[int] = None
    artists: Optional[list[SpotifyBriefArtist]] = None
    album: Optional[SpotifyBriefAlbum] = None
    preview_url: Optional[str] = None
    external_urls: Optional[dict] = None


class SpotifyArtist(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    genres: Optional[list[str]] = None

    @property
    def pic_url(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyAlbum(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    artists: Optional[list[SpotifyBriefArtist]] = None
    tracks: Optional[list[SpotifySong]] = None
    release_date: Optional[str] = None
    total_tracks: Optional[int] = None

    @property
    def cover(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyPlaylist(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    owner: Optional[SpotifyBriefArtist] = None
    tracks: Optional[list[SpotifySong]] = None
    public: Optional[bool] = None

    @property
    def cover(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyUser(BaseModel):
    id: Optional[str] = None
    display_name: Optional[str] = None
    images: Optional[list[SpotifyImage]] = None
    email: Optional[str] = None

    @property
    def avatar_url(self) -> Optional[str]:
        if self.images:
            return self.images[0].url
        return None


class SpotifyLyrics(BaseModel):
    lyrics: Optional[dict] = None
