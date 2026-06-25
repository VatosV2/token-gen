import time
import re

from abc import ABC, abstractmethod
from typing import Dict, Optional

class MailApi(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers: Dict[str, str] = {
            "X-API-KEY": api_key
        }

    @abstractmethod
    def create_account(self, username: str, password: str) -> Optional[str]:
        pass

    @abstractmethod
    def fetch_inbox(self, email: str, password: str) -> list:
        pass

    def wait_for_verification(
        self,
        email: str,
        password: str,
        poll_interval: int = 1,
        timeout: int = 30
    ) -> Optional[str]:
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                inbox = self.fetch_inbox(email, password)
                if inbox:
                    body = inbox[0].get("body", "")
                    match = re.search(r"upn=([^\s&]+)", body)
                    if match:
                        return match.group(1)
            except Exception as e:
                  raise RuntimeError(e)

            time.sleep(poll_interval)
        return None