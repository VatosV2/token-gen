import re
import json
import curl_cffi

from json import dumps, loads, JSONDecodeError
from typing import Union, Dict, Tuple, Optional

import random_name
import requests
import websocket
from requests import RequestException


class DiscordSessionFactory:
    def __init__(self, proxy: str | None):
        self.proxy = proxy

    def create(self):
        session = curl_cffi.Session(impersonate="chrome146")

        if self.proxy:
            session.proxies = {
                "http": f"http://{self.proxy}",
                "https": f"http://{self.proxy}",
            }

        return session

class DiscordUtils:
    
    @staticmethod
    def get_fingerprint(dcfduid, sdcfduid, session):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "cookie": f"__dcfduid={dcfduid}; __sdcfduid={sdcfduid};",
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not/A)Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        session.headers = headers
        data = session.get('https://discord.com/api/v9/experiments')
        data = data.text
        fingerprint = json.loads(data)
        fingerprint = fingerprint['fingerprint']
        return fingerprint

    @staticmethod
    def fetch_cookies(session):
        data = session.get('https://discord.com')
        cookiess = session.cookies.get_dict()
        dcfduid = cookiess.get("__dcfduid")
        sdcfduid = cookiess.get("__sdcfduid")
        return dcfduid, sdcfduid

    @staticmethod
    def get_web() -> int:
        """Fetch the build number from the Discord web app page."""
        try:
            page = requests.get("https://discord.com/app").text
            assets = re.findall(r'src="/assets/([^"]+)"', page)

            for asset in reversed(assets):
                js = requests.get(f"https://discord.com/assets/{asset}").text
                if "buildNumber:" in js:
                    return int(js.split('buildNumber:"')[1].split('"')[0])

        except RequestException as e:
            print(f"Error fetching build from web: {e}")

        return -1

    @staticmethod
    def get_session_id(token: str) -> Tuple[Union[str, None], Optional[websocket.WebSocket], Optional[float]]:
        ws: websocket.WebSocket = websocket.WebSocket()
        try:
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")

            hello: dict = loads(ws.recv())
            heartbeat_interval: float = hello["d"]["heartbeat_interval"] / 1000

            payload: dict = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {"$os": "Windows"},
                },
            }

            ws.send(dumps(payload))

            while True:
                response: dict = loads(ws.recv())
                op: int = response.get("op", -1)
                event: Optional[str] = response.get("t")

                if event == "READY":
                    return response["d"]["session_id"], ws, heartbeat_interval
                if op == 9:
                    return "Invalid token", None, None
                if op == 429:
                    return "Rate limited", None, None

        except websocket.WebSocketException as e:
            return f"WebSocket error: {e}", None, None
        except JSONDecodeError as e:
            return f"JSON error: {e}", None, None

    @staticmethod
    def check_discord_token(session) -> Dict[str, str]:
        try:
            r = session.get("https://discord.com/api/v9/users/@me")
            if r.status_code != 200:
                return {"status": "invalid"}

            r2 = session.get("https://discord.com/api/v9/users/@me/settings")
            if r2.status_code == 200:
                return {"status": "Valid"}
            elif r2.status_code == 403:
                return {"status": "locked"}
        except Exception:
            return {"status": "invalid"}

        return {"status": "invalid"}

    @staticmethod
    def _get_username() -> Optional[str]:
        username = random_name.generate_name(separator="_")
        return username
