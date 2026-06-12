#!/usr/bin/env python3
"""测试 Widevine 解密流程。

需要:
1. 已保存的 Spotify 会话（~/.feeluown/spotify_credentials.json）
2. Widevine .wvd 设备文件（在 ~/.feeluown/spotify_config.json 中配置 wvd_path）
3. ffmpeg（系统依赖）

运行: python tests/test_widevine.py
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")
logger = logging.getLogger("test_widevine")

TEST_TRACK_ID = "4iV5W9uYEdYUVa79Axb7Rh"


def main():
    import json
    import spotapi
    from spotapi.utils.logger import Logger as SpotapiLogger
    from spotapi.client import generate_totp
    import requests as _requests

    # ── 检查 wvd 配置 ──
    config_path = Path.home() / ".feeluown" / "spotify_config.json"
    if not config_path.exists():
        logger.error("未找到配置文件: %s", config_path)
        logger.info("请创建配置文件，内容: {\"wvd_path\": \"/path/to/device.wvd\"}")
        return False

    with open(config_path) as f:
        config = json.load(f)
    wvd_path = config.get("wvd_path", "")
    if not wvd_path or not Path(wvd_path).exists():
        logger.error("wvd 文件不存在: %s", wvd_path)
        return False
    logger.info("✅ wvd 文件: %s", wvd_path)

    # ── 恢复会话 ──
    class _NoopSolver:
        def __init__(self, *a, **kw): pass
        def get_balance(self): return None

    creds_path = Path.home() / ".feeluown" / "spotify_credentials.json"
    with open(creds_path) as f:
        data = json.load(f)
    cfg = spotapi.Config(solver=_NoopSolver, logger=SpotapiLogger)
    login = spotapi.Login.from_cookies(data, cfg)
    song = spotapi.Song(client=login.client)
    base = song.base
    logger.info("✅ 会话恢复成功")

    # ── 获取 token ──
    if type(base.access_token).__name__ == "_UndefinedType":
        try:
            base.client.get("https://spclient.wg.spotify.com/", authenticate=True)
        except Exception:
            pass
    cookies = dict(base.client.cookies)
    totp, version = generate_totp()
    resp = _requests.get(
        "https://open.spotify.com/api/token",
        params={"reason": "init", "productType": "web-player",
                "totp": totp, "totpVer": version, "totpServer": totp},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*",
                 "Referer": "https://open.spotify.com/"},
        cookies=cookies, timeout=10,
    )
    auth_token = resp.json()["accessToken"]
    client_token = base.client_token
    logger.info("✅ Token 获取成功")

    # ── 获取加密 file_id ──
    from fuo_spotify.api import SpotifyApi, _ENCRYPTED_PREFIX
    api = SpotifyApi(login)
    file_id = api.get_encrypted_file_id(TEST_TRACK_ID)
    if not file_id:
        logger.error("❌ 未找到加密 file_id")
        return False
    file_id_hex = file_id.hex()
    logger.info("✅ 加密 file_id: %s", file_id_hex)

    # ── 获取 seektable ──
    from fuo_spotify.widevine import get_seektable, get_cdn_url, get_widevine_key, download_encrypted
    logger.info("=== 获取 seektable ===")
    seektable = get_seektable(file_id_hex)
    pssh_str = seektable["pssh"]["widevine"]
    logger.info("✅ PSSH: %s", pssh_str[:60])

    # ── 获取 CDN URL ──
    logger.info("=== 获取 CDN URL ===")
    cdn_url = get_cdn_url(file_id_hex, auth_token, client_token)
    logger.info("✅ CDN URL: %s", cdn_url[:80])

    # ── 下载加密音频 ──
    import tempfile, os
    logger.info("=== 下载加密音频 ===")
    tmp_dir = tempfile.mkdtemp(prefix="fuo_widevine_test_")
    encrypted_path = os.path.join(tmp_dir, "encrypted.mp4")
    download_encrypted(cdn_url, encrypted_path)
    logger.info("✅ 下载完成: %d bytes", os.path.getsize(encrypted_path))

    # ── 获取 Widevine key ──
    logger.info("=== 获取 Widevine key ===")
    key_hex = get_widevine_key(pssh_str, wvd_path, client_token)
    logger.info("✅ Content key: %s", key_hex)

    # ── ffmpeg 解密 ──
    import subprocess
    logger.info("=== ffmpeg 解密 ===")
    decrypted_path = os.path.join(tmp_dir, "decrypted.m4a")
    result = subprocess.run(
        ["ffmpeg", "-y", "-decryption_key", key_hex,
         "-i", encrypted_path, "-c:a", "copy", decrypted_path],
        capture_output=True, timeout=60,
    )
    if result.returncode != 0:
        logger.error("❌ ffmpeg 失败: %s", result.stderr.decode()[:200])
        return False
    logger.info("✅ 解密完成: %s (%d bytes)", decrypted_path, os.path.getsize(decrypted_path))

    # ── 播放 ──
    logger.info("=== 播放 ===")
    logger.info("文件: %s", decrypted_path)
    logger.info("可用 mpv 播放: mpv --no-video %s", decrypted_path)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
