"""测试 extended-metadata API 是否返回可用的 CDN URL。"""
import json
import re
import sys
from fuo_spotify.login import LoginManager

TRACK_ID = sys.argv[1] if len(sys.argv) > 1 else "3j6IzoLrLYzx8HX36N1EKz"

print(f"Track ID: {TRACK_ID}")
print("=" * 60)

lm = LoginManager()
login = lm.restore_session()
if not login:
    print("ERROR: 无法恢复 Spotify 会话")
    sys.exit(1)

client = login.client

# 确保 client 有 access_token 和 client_token
base = login._base
print(f"\n[0] 检查认证状态...")
print(f"    access_token exists: {base.access_token is not None and str(base.access_token) != '_Undefined'}")
print(f"    client_token exists: {base.client_token is not None and str(base.client_token) != '_Undefined'}")

# 1. 调用 extended-metadata API（用 authenticate=True 让 spotapi 自动加认证头）
print("\n[1] 调用 extended-metadata API (authenticate=True) ...")
url = "https://spclient.wg.spotify.com/extended-metadata/v0/extended-metadata"
payload = {
    "entityRequest": [
        {
            "entityUri": f"spotify:track:{TRACK_ID}",
            "query": [
                {"extensionKind": 249, "etag": ""}
            ],
        }
    ]
}

resp = client.post(url, json=payload, authenticate=True)
print(f"    fail={resp.fail}")
if resp.fail:
    print(f"    error: {resp.error.string}")
    # 尝试打印更多信息
    if hasattr(resp, 'status_code'):
        print(f"    status_code: {resp.status_code}")
else:
    data = resp.response
    print(f"    type: {type(data).__name__}")
    if isinstance(data, (bytes, str)):
        raw = data if isinstance(data, bytes) else data.encode('utf-8', errors='replace')
        print(f"    length: {len(raw)}")
        urls = re.findall(rb'https?://[^\x00-\x1f"\s<>]+', raw)
        for i, u in enumerate(urls):
            print(f"    URL[{i}]: {u.decode('utf-8', errors='replace')}")
        print(f"\n    raw (first 3000):")
        print(raw[:3000])
    elif isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str)[:3000])
