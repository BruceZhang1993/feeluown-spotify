PROVIDER_ID = 'spotify'
PROVIDER_NAME = 'Spotify'

# Spotify 音频质量等级映射
# Spotify Premium: 128k (aac), 256k (aac), 320k (ogg)
# Spotify Free: 128k (aac), 160k (ogg)
QUALITY_MAP = {
    'lq': {'bitrate': 128, 'format': 'aac'},
    'sq': {'bitrate': 160, 'format': 'ogg'},
    'hq': {'bitrate': 256, 'format': 'aac'},
    'shq': {'bitrate': 320, 'format': 'ogg'},
}
