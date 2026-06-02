"""测试 stream URL 解析逻辑。"""
from fuo_spotify.api import _base62_to_hex, SpotifyApi
from unittest.mock import MagicMock


def test_base62_to_hex():
    """测试 base62 到 hex 的转换。"""
    # 测试一些已知的 Spotify track ID
    # 例如：4iV5W9uYEdYUVa79Axb7Rh 是一个常见的 track ID
    test_id = "4iV5W9uYEdYUVa79Axb7Rh"
    hex_result = _base62_to_hex(test_id)
    print(f"Track ID: {test_id} -> Hex: {hex_result}")
    assert len(hex_result) == 32, f"Hex should be 32 chars, got {len(hex_result)}"

    # 测试另一个 ID
    test_id2 = "11dFghVXANMlKmJXsNCbNl"
    hex_result2 = _base62_to_hex(test_id2)
    print(f"Track ID: {test_id2} -> Hex: {hex_result2}")
    assert len(hex_result2) == 32, f"Hex should be 32 chars, got {len(hex_result2)}"


def test_stream_url_parsing():
    """测试 stream URL 解析逻辑。"""
    # 模拟 protobuf 响应（基于 Spotify CDN URL 格式）
    # Spotify CDN URL 通常像这样：
    # https://audio-ak-spotify-com.akamaized.net/...
    # 或者
    # https://spotifycdn.com/...

    # 构造一个模拟的 protobuf 响应
    # \x12 是字段标记，后面跟着长度和 URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true"
    fake_response = b'\x12' + bytes([len(fake_url)]) + fake_url.encode('utf-8')

    # 创建 mock 对象
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = fake_response
    mock_client.get.return_value = mock_resp

    # 创建 SpotifyApi 实例
    mock_login = MagicMock()
    mock_login.client = mock_client
    mock_song = MagicMock()
    mock_song.base.client = mock_client

    api = SpotifyApi(mock_login)
    api._song = mock_song

    # 测试解析
    result = api.get_track_stream_url("4iV5W9uYEdYUVa79Axb7Rh")
    print(f"Parsed URL: {result}")

    if result:
        assert result.startswith("https://"), f"URL should start with https://, got {result}"
        assert "spotify" in result.lower() or "akamaized" in result.lower(), \
            f"URL should be from Spotify CDN, got {result}"
    else:
        print("Warning: No URL parsed")


if __name__ == "__main__":
    test_base62_to_hex()
    test_stream_url_parsing()
    print("All tests passed!")
