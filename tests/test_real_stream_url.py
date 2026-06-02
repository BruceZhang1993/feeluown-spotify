#!/usr/bin/env python3
"""测试实际的 Spotify stream URL 获取。"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fuo_spotify.login import LoginManager
from fuo_spotify.api import SpotifyApi


def test_real_stream_url():
    """测试实际的 stream URL 获取。"""
    print("=== 测试实际的 Spotify stream URL 获取 ===\n")

    # 创建登录管理器
    login_manager = LoginManager()

    # 尝试恢复会话
    print("1. 尝试恢复会话...")
    if not login_manager.restore_session():
        print("❌ 无法恢复会话，请先登录")
        print("   提示：在 feeluown 中使用 spotify login 命令登录")
        return

    print("✅ 会话已恢复\n")

    # 创建 API 实例
    print("2. 创建 API 实例...")
    api = SpotifyApi(login_manager.login)
    print("✅ API 实例已创建\n")

    # 测试 track ID（使用一个常见的 track ID）
    test_tracks = [
        ("4iV5W9uYEdYUVa79Axb7Rh", "Ed Sheeran - Shape of You"),
        ("11dFghVXANMlKmJXsNCbNl", "Rihanna - Umbrella"),
    ]

    print("3. 测试获取 stream URL...\n")

    for track_id, track_name in test_tracks:
        print(f"   测试: {track_name}")
        print(f"   Track ID: {track_id}")

        try:
            stream_url = api.get_track_stream_url(track_id)

            if stream_url:
                print(f"   ✅ 获取成功!")
                print(f"   URL: {stream_url}")
                print(f"   URL 长度: {len(stream_url)}")
                print(f"   末尾字符: {repr(stream_url[-10:])}")
                print(f"   以单引号结尾: {stream_url.endswith(chr(39))}")
                print(f"   以 https:// 开头: {stream_url.startswith('https://')}")
            else:
                print(f"   ❌ 获取失败：返回 None")

        except Exception as e:
            print(f"   ❌ 获取失败：{e}")

        print()

    print("=== 测试完成 ===")


if __name__ == "__main__":
    test_real_stream_url()
