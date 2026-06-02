"""测试 stream URL 解析逻辑 - 验证修复。"""
import pytest
from fuo_spotify.api import SpotifyApi
from unittest.mock import MagicMock


@pytest.fixture
def api():
    """创建 SpotifyApi 测试实例。"""
    mock_login = MagicMock()
    mock_login.client = MagicMock()
    mock_song = MagicMock()
    mock_song.base.client = MagicMock()

    api = SpotifyApi(mock_login)
    api._song = mock_song
    return api


def test_get_track_stream_url_with_bytes_response(api):
    """测试当 resp.response 是 bytes 时，URL 解析是否正确。"""
    # 模拟真实的 Spotify CDN URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true"

    # 构造 protobuf 响应（bytes）
    fake_response = b'\x12' + bytes([len(fake_url)]) + fake_url.encode('utf-8')

    # 设置 mock
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = fake_response
    api._song.base.client.get.return_value = mock_resp

    # 调用被测试的方法
    result = api.get_track_stream_url("4iV5W9uYEdYUVa79Axb7Rh")

    # 验证结果
    assert result is not None, "应该返回 URL"
    assert result == fake_url, f"URL 应该匹配，得到: {result}"
    assert not result.endswith("'"), f"URL 不应该以单引号结尾，得到: {result}"
    assert result.startswith("https://"), f"URL 应该以 https:// 开头，得到: {result}"


def test_get_track_stream_url_with_string_response(api):
    """测试当 resp.response 是字符串时，URL 解析是否正确。"""
    # 模拟真实的 Spotify CDN URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true"

    # 设置 mock（直接返回字符串）
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = fake_url
    api._song.base.client.get.return_value = mock_resp

    # 调用被测试的方法
    result = api.get_track_stream_url("4iV5W9uYEdYUVa79Axb7Rh")

    # 验证结果
    assert result is not None, "应该返回 URL"
    assert result == fake_url, f"URL 应该匹配，得到: {result}"
    assert not result.endswith("'"), f"URL 不应该以单引号结尾，得到: {result}"
    assert result.startswith("https://"), f"URL 应该以 https:// 开头，得到: {result}"


def test_get_track_stream_url_no_url_found(api):
    """测试当响应中没有 URL 时，返回 None。"""
    # 构造一个没有 URL 的响应
    fake_response = b'\x12\x02\x08\x01'  # 随机 protobuf 数据，没有 URL

    # 设置 mock
    mock_resp = MagicMock()
    mock_resp.fail = False
    mock_resp.response = fake_response
    api._song.base.client.get.return_value = mock_resp

    # 调用被测试的方法
    result = api.get_track_stream_url("4iV5W9uYEdYUVa79Axb7Rh")

    # 验证结果
    assert result is None, "没有 URL 时应该返回 None"


def test_get_track_stream_url_api_failure(api):
    """测试当 API 调用失败时，返回 None。"""
    # 设置 mock
    mock_resp = MagicMock()
    mock_resp.fail = True
    mock_resp.error.string = "Not found"
    api._song.base.client.get.return_value = mock_resp

    # 调用被测试的方法
    result = api.get_track_stream_url("4iV5W9uYEdYUVa79Axb7Rh")

    # 验证结果
    assert result is None, "API 失败时应该返回 None"


def test_get_track_stream_url_exception(api):
    """测试当发生异常时，返回 None。"""
    # 设置 mock 抛出异常
    api._song.base.client.get.side_effect = Exception("Network error")

    # 调用被测试的方法
    result = api.get_track_stream_url("4iV5W9uYEdYUVa79Axb7Rh")

    # 验证结果
    assert result is None, "异常时应该返回 None"
