"""调试脚本 v4：测试其他可用的 GraphQL 操作。

用法: .venv/bin/python tests/debug_api.py
"""
import json
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(name)s %(levelname)s: %(message)s')

from fuo_spotify.login import LoginManager
from fuo_spotify.api import SpotifyApi


def dump(label, data, limit=3000):
    print(f"\n{'='*60}")
    print(f"[{label}]")
    print(f"{'='*60}")
    if isinstance(data, (dict, list)):
        s = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        s = repr(data)
    print(s[:limit])
    if len(s) > limit:
        print(f"... (truncated, total {len(s)} chars)")


def gql(client, part_hash, op_name, variables=None):
    """调用 GraphQL 操作。"""
    url = "https://api-partner.spotify.com/pathfinder/v1/query"
    params = {
        "operationName": op_name,
        "variables": json.dumps(variables or {}),
        "extensions": json.dumps({
            "persistedQuery": {
                "version": 1,
                "sha256Hash": part_hash(op_name),
            }
        }),
    }
    resp = client.post(url, params=params, authenticate=True)
    if resp.fail:
        return {"error": resp.error.string}
    return resp.response


def main():
    lm = LoginManager()
    login = lm.restore_session()
    if not login:
        print("ERROR: 没有已保存的登录会话")
        sys.exit(1)

    api = SpotifyApi(login)
    client = api._song.base.client
    ph = api._song.base.part_hash

    # 1. homePinnedSections - 不需要 EndUserIntegration
    print("\n\n>>> 1: homePinnedSections")
    try:
        result = gql(client, ph, "homePinnedSections")
        if "error" in result:
            print(f"  FAIL: {result['error']}")
        else:
            dump("homePinnedSections", result)
    except Exception as e:
        print(f"  FAIL: {e}")

    # 2. browseSection - 带 URI
    print("\n\n>>> 2: browseSection")
    try:
        result = gql(client, ph, "browseSection", {
            "uri": "spotify:section:home",
        })
        if "error" in result:
            print(f"  FAIL: {result['error']}")
        else:
            dump("browseSection", result)
    except Exception as e:
        print(f"  FAIL: {e}")

    # 3. userTopContent - 带 AffinityInput
    print("\n\n>>> 3: userTopContent")
    try:
        result = gql(client, ph, "userTopContent", {
            "topArtistsInput": {"limit": 10, "offset": 0},
            "topTracksInput": {"limit": 10, "offset": 0},
            "includeTopTracks": True,
            "includeTopArtists": True,
        })
        if "error" in result:
            print(f"  FAIL: {result['error']}")
        else:
            dump("userTopContent", result)
    except Exception as e:
        print(f"  FAIL: {e}")

    # 4. seoRecommendedTrackPlaylistDesktop
    print("\n\n>>> 4: seoRecommendedTrackPlaylistDesktop")
    try:
        result = gql(client, ph, "seoRecommendedTrackPlaylistDesktop")
        if "error" in result:
            print(f"  FAIL: {result['error']}")
        else:
            dump("seoRecommendedTrackPlaylistDesktop", result)
    except Exception as e:
        print(f"  FAIL: {e}")

    # 5. fetchPlaylistMetadata - 测试获取歌单元数据
    print("\n\n>>> 5: fetchPlaylistMetadata (Daily Mix 1)")
    try:
        # 先获取 Daily Mix 歌单 ID
        result = gql(client, ph, "fetchPlaylistMetadata", {
            "uri": "spotify:playlist:37i9dQZF1E3AFmNvSCnUvC",
        })
        if "error" in result:
            print(f"  FAIL: {result['error']}")
        else:
            dump("fetchPlaylistMetadata", result)
    except Exception as e:
        print(f"  FAIL: {e}")

    # 6. 测试 PrivatePlaylist.recommended_songs
    print("\n\n>>> 6: PrivatePlaylist.recommended_songs")
    try:
        import spotapi
        pp = spotapi.PrivatePlaylist("37i9dQZF1E3AFmNvSCnUvC", client=api._client)
        result = pp.recommended_songs(num_songs=5)
        dump("recommended_songs", result)
    except Exception as e:
        print(f"  FAIL: {e}")

    # 7. 测试 PrivatePlaylist.get_library
    print("\n\n>>> 7: PrivatePlaylist.get_library")
    try:
        import spotapi
        pp = spotapi.PrivatePlaylist("37i9dQZF1E3AFmNvSCnUvC", client=api._client)
        result = pp.get_library(limit=5)
        dump("get_library", result)
    except Exception as e:
        print(f"  FAIL: {e}")


if __name__ == "__main__":
    main()
