import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SEEKTABLE_URL = "https://seektables.spotifycdn.com/v1/seektable/{file_id}"
STORAGE_RESOLVE_URL = (
    "https://spclient.wg.spotify.com"
    "/storage-resolve/v2/files/audio/interactive/10/{file_id}"
    "?version=10000000&product=9&platform=39&alt=json"
)
WIDEVINE_LICENSE_URL = "https://gew4-spclient.spotify.com/widevine-license/v1/audio/license"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Accept": "*/*",
    "Referer": "https://open.spotify.com/",
    "Origin": "https://open.spotify.com",
}


def get_seektable(file_id: str) -> dict:
    url = SEEKTABLE_URL.format(file_id=file_id)
    resp = requests.get(url, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_cdn_url(file_id: str, auth_token: str, client_token: str) -> str:
    url = STORAGE_RESOLVE_URL.format(file_id=file_id)
    headers = {**_HEADERS, "client-token": client_token}
    if auth_token:
        headers["authorization"] = f"Bearer {auth_token}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    urls = data.get("cdnurl", [])
    if not urls:
        raise RuntimeError(f"No CDN URL for file_id={file_id}")
    return urls[0]


def get_widevine_key(pssh_str: str, wvd_path: str, client_token: str) -> str:
    from pywidevine.cdm import Cdm
    from pywidevine.pssh import PSSH
    from pywidevine.device import Device

    device = Device.load(wvd_path)
    cdm = Cdm(
        device_type=device.type,
        system_id=device.system_id,
        security_level=device.security_level,
        client_id=device.client_id,
        rsa_key=device.private_key,
    )
    pssh = PSSH(pssh_str)
    sid = cdm.open()
    try:
        challenge = cdm.get_license_challenge(sid, pssh)
        headers = {
            **_HEADERS,
            "Content-Type": "application/octet-stream",
            "client-token": client_token,
        }
        resp = requests.post(
            WIDEVINE_LICENSE_URL, data=challenge, headers=headers, timeout=15,
        )
        resp.raise_for_status()
        cdm.parse_license(sid, resp.content)
        for key in cdm.get_keys(sid):
            if key.type == "CONTENT":
                return key.key.hex()
        raise RuntimeError("No CONTENT key found in license response")
    finally:
        cdm.close(sid)
