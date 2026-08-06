import random
import requests

from typing import Optional, List
from Core.communication.mail.base import MailApi

class TempMailLolApi(MailApi):
    BASE_URL = "https://api.tempmail.lol/v2"

    def __init__(self, api_key: str = None):
        super().__init__(api_key or "")
        self.name = "tempmaillol"

    def create_account(self, username: str = None, password: str = None) -> Optional[str]:
        params = {}

        if username:
            params["prefix"] = username

        resp = requests.get(
            f"{self.BASE_URL}/inbox/create",
            params=params,
            timeout=15,
        )

        if not resp.ok:
            raise RuntimeError(
                f"TempMail.lol API returned {resp.status_code}: {resp.text}"
            )

        data = resp.json()

        self.token = data["token"]

        return data["address"]

    def fetch_inbox(self, email: str, password: str = None) -> List[dict]:
        token = password or getattr(self, "token", None)

        if not token:
            raise RuntimeError(
                "TempMail.lol requires the inbox token returned during creation"
            )

        resp = requests.get(
            f"{self.BASE_URL}/inbox",
            params={"token": token},
            timeout=15,
        )

        if not resp.ok:
            raise RuntimeError(
                f"TempMail.lol API returned {resp.status_code}: {resp.text}"
            )

        data = resp.json()

        emails = data.get("emails", [])

        normalized = []
        for msg in emails:
            normalized.append({
                "id": msg.get("id"),
                "from": msg.get("from"),
                "to": msg.get("to"),
                "subject": msg.get("subject"),
                "body": msg.get("body") or "",
                "html": msg.get("html") or "",
            })

        return normalized
