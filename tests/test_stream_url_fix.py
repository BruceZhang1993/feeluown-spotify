"""测试 stream URL 解析修复。"""
import re


def test_current_logic_with_bytes():
    """测试当前逻辑对 bytes 响应的处理。"""
    # 模拟真实的 Spotify CDN URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true&other=test"

    # 构造 protobuf 响应（bytes）
    fake_response = b'\x12' + bytes([len(fake_url)]) + fake_url.encode('utf-8')

    # 当前的逻辑：str(bytes)
    raw = str(fake_response)

    # 当前的正则表达式
    for part in raw.split('\x12'):
        m = re.search(r'(https://[^\x00-\x1f"\s]+)', part)
        if m:
            stream_url = m.group(1)
            print(f"Current logic result: {stream_url}")
            print(f"URL ends with: {repr(stream_url[-5:])}")
            print(f"Has trailing quote: {stream_url.endswith(chr(39))}")
            return stream_url

    return None


def test_fixed_logic_with_bytes():
    """测试修复后的逻辑对 bytes 响应的处理。"""
    # 模拟真实的 Spotify CDN URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true&other=test"

    # 构造 protobuf 响应（bytes）
    fake_response = b'\x12' + bytes([len(fake_url)]) + fake_url.encode('utf-8')

    # 修复：直接使用 bytes 正则表达式
    m = re.search(rb'(https://[^\x00-\x1f"\s]+)', fake_response)
    if m:
        url_bytes = m.group(1)
        stream_url = url_bytes.decode('utf-8')
        print(f"Fixed logic result: {stream_url}")
        print(f"URL ends with: {repr(stream_url[-5:])}")
        print(f"Has trailing quote: {stream_url.endswith(chr(39))}")
        return stream_url

    return None


def test_fixed_logic_with_string():
    """测试修复后的逻辑对字符串响应的处理。"""
    # 模拟真实的 Spotify CDN URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true&other=test"

    # 如果 resp.response 已经是字符串
    raw = fake_url

    # 修复：使用字符串正则表达式
    m = re.search(r'(https://[^\x00-\x1f"\s]+)', raw)
    if m:
        stream_url = m.group(1)
        print(f"String logic result: {stream_url}")
        print(f"URL ends with: {repr(stream_url[-5:])}")
        print(f"Has trailing quote: {stream_url.endswith(chr(39))}")
        return stream_url

    return None


if __name__ == "__main__":
    print("=== 测试当前逻辑（有问题） ===")
    test_current_logic_with_bytes()

    print()
    print("=== 测试修复后的逻辑（bytes） ===")
    test_fixed_logic_with_bytes()

    print()
    print("=== 测试修复后的逻辑（string） ===")
    test_fixed_logic_with_string()
