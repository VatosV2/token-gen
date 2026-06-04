
import json
import time
import base64
import uuid
import random

from platform import system

from typing import Optional

from Core.discord.utils import DiscordUtils

class HeaderBuilder:
    def __init__(self, session):
        self.session = session
        self._header_cache: dict = {}
        self._cookie_cache: dict = {}

        self.chrome_version = 146
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{self.chrome_version}.0.0.0 Safari/537.36"
        )

    def _super_properties(self, invite_code: Optional[str] = None) -> str:
        # Imagine using Xbox One Device Spoof for no reason
        payload = {
            "os": system(),
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "has_client_mods": False,
            "browser_user_agent": self.user_agent,
            "browser_version": f"{self.chrome_version}.0.0.0",
            "os_version": 10,
            "referrer": "" if not invite_code else f"https://discord.com/invite/{invite_code}",
            "referring_domain": "",
            "referrer_current": "https://discord.com/",
            "referring_domain_current": "discord.com",
            "release_channel": "stable",
            "client_build_number": DiscordUtils.get_web(),
            "client_event_source": None,
            "client_launch_id": str(uuid.uuid4()),
            "launch_signature": str(uuid.uuid4()),
            "client_heartbeat_session_id": str(uuid.uuid4()),
            "client_app_state": "focused",
        }


        raw = json.dumps(payload, separators=(",", ":")).encode()
        return base64.b64encode(raw).decode()


    def _fetch_cookies(self, token: str) -> str:
        now = time.time()

        cached = self._cookie_cache.get(token)
        if cached and now - cached["ts"] < 86400:
            return cached["cookie"]

        try:
            resp = self.session.get(
                f"https://discord.com/api/v9/users/@me",
                headers={"Authorization": token},
                timeout=15,
            )

            cookies = []
            if "set-cookie" in resp.headers:
                for part in resp.headers["set-cookie"].split(", "):
                    cookie = part.split(";", 1)[0]
                    if "=" in cookie:
                        cookies.append(cookie)

            cookie_str = "; ".join(cookies)
            self._cookie_cache[token] = {"cookie": cookie_str, "ts": now}
            return cookie_str

        except Exception:
            return ""

    def build(
        self,
        fp: str,
        invite_code: Optional[str] = None,
        *,
        context: Optional[str] = None,
    ) -> dict[str, str]:
        cache_key = context or "no_context"
        now = time.time()

        cached = self._header_cache.get(cache_key)
        if cached and now - cached["ts"] < 86400:
            headers = cached["headers"].copy()
        else:
            headers = {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "origin": "https://discord.com",
                "priority": "u=1, i",
                "referer": "https://discord.com/register" if not invite_code else f"https://discord.com/invite/{invite_code}",
                "sec-ch-ua": (
                    f'"Google Chrome";v="{self.chrome_version}", '
                    f'"Chromium";v="{self.chrome_version}", '
                    '"Not/A)Brand";v="99"'
                ),
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.user_agent,
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "America/Los_Angeles",
                "x-fingerprint": fp,
                "x-super-properties": self._super_properties(invite_code),
            }

            self._header_cache[cache_key] = {
                "headers": headers.copy(),
                "ts": now,
            }

        return headers