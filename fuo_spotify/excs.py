class SpotifyIOError(IOError):
    pass

class SpotifyAuthError(SpotifyIOError):
    pass

class SpotifyAPIError(SpotifyIOError):
    pass

class SpotifyTrackError(SpotifyIOError):
    pass
