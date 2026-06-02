"""调试 stream URL 解析问题。"""
import re


def debug_parsing():
    """调试 URL 解析逻辑。"""
    # 模拟真实的 Spotify CDN URL
    fake_url = "https://audio-ak-spotify-com.akamaized.net/audio/abc123?params=true&other=test"

    # 构造 protobuf 响应
    fake_response = b'\x12' + bytes([len(fake_url)]) + fake_url.encode('utf-8')

    # 模拟 str() 转换（这是问题所在！）
    raw = str(fake_response)
    print(f"raw string: {repr(raw)}")
    print()

    # 当前的解析逻辑
    for part in raw.split('\x12'):
        m = re.search(r'(https://[^\x00-\x1f"\s]+)', part)
        if m:
            stream_url = m.group(1)
            print(f"Current logic result: {stream_url}")
            print(f"URL ends with: {repr(stream_url[-5:])}")

    # 问题：str(bytes) 会变成 b'...' 格式
    print()
    print("=== 问题分析 ===")
    print(f"type(fake_response): {type(fake_response)}")
    print(f"type(str(fake_response)): {type(str(fake_response))}")
    print()

    # 正确的做法应该是直接使用 bytes
    print("=== 正确的解析方式 ===")
    # 方式1：直接在 bytes 中搜索
    m = re.search(rb'(https://[^\x00-\x1f"\s]+)', fake_response)
    if m:
        url_bytes = m.group(1)
        url_str = url_bytes.decode('utf-8')
        print(f"Bytes regex result: {url_str}")

    # 方式2：如果 resp.response 已经是字符串
    # 假设 spotapi 返回的是字符串而不是 bytes
    raw_str = fake_url  # 直接使用 URL
    m = re.search(r'(https://[^\x00-\x1f"\s]+)', raw_str)
    if m:
        print(f"String regex result: {m.group(1)}")


if __name__ == "__main__":
    debug_parsing()
