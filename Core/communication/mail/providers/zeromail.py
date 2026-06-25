import random
import requests
from typing import Optional, List
from Core.communication.mail.base import MailApi

class ZeromailApi(MailApi):
    BASE_URL = "https://api.0mail.tech/api"

    def __init__(self, api_key: str, use_pro_domains: bool = False):
        super().__init__(api_key)
        self.api_key = api_key
        self.use_pro_domains = use_pro_domains
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
        self.domains = []
    
    def create_account(self, username: str, password: str = None) -> Optional[str]:
        # Populate domains list dynamically from API if not loaded yet
        if not self.domains:
            self.domains = self.get_domains()
            
        if not self.domains:
            raise RuntimeError("No available domains returned from ZeroMail API")

        domain = random.choice(self.domains)
        email = f"{username}@{domain}"
        
        try:
            resp = requests.post(
                f"{self.BASE_URL}/inboxes",
                headers=self.headers,
                json={
                    "local": username,
                    "domain": domain
                },
                timeout=15
            )
            if not resp.ok:
                raise RuntimeError(f"ZeroMail returned {resp.status_code}: {resp.text}")
        except Exception as e:
            raise RuntimeError(
                f"ZeroMail inbox creation failed for {email} -> {e}"
            ) from e

        return email

    def fetch_inbox(self, email: str, password: str = None) -> List[dict]:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/inboxes",
                headers=self.headers,
                timeout=15
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Network error listing ZeroMail inboxes: {e}")

        if not resp.ok:
            raise RuntimeError(f"ZeroMail API returned {resp.status_code}: {resp.text}")

        inboxes_data = resp.json().get("inboxes", [])
        inbox_id = None
        for ibox in inboxes_data:
            if ibox.get("address").lower() == email.lower():
                inbox_id = ibox.get("id")
                break

        if not inbox_id:
            return []

        try:
            resp = requests.get(
                f"{self.BASE_URL}/inboxes/{inbox_id}/messages",
                headers=self.headers,
                timeout=15
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Network error fetching ZeroMail messages: {e}")

        if not resp.ok:
            raise RuntimeError(f"ZeroMail API returned {resp.status_code}: {resp.text}")

        data = resp.json()
        messages = data.get("messages", [])

        normalized = []
        for msg in messages:
            normalized.append({
                "id": msg.get("id"),
                "from": f"{msg.get('from_name')} <{msg.get('from_addr')}>",
                "to": email,
                "subject": msg.get("subject"),
                "body": msg.get("body", ""),
                "html": msg.get("html", "") or msg.get("body", "")  
            })
        return normalized

    def get_domains(self, type: str = "discord") -> list:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/domains",
                params={"website": type},
                headers=self.headers,
                timeout=10,
            )
            if not resp.ok:
                raise RuntimeError(
                    f"ZeroMail API returned {resp.status_code}: {resp.text}"
                )
            raw_domains = resp.json().get("domains", [])
        except requests.RequestException as e:
            raise RuntimeError(f"Network error fetching ZeroMail domains: {e}")

        has_pro_plan = False
        if self.use_pro_domains:
            try:
                profile_resp = requests.get(
                    f"{self.BASE_URL}/profile",
                    headers=self.headers,
                    timeout=10
                )
                if profile_resp.ok:
                    plan_id = profile_resp.json().get("plan", {}).get("id", "free")
                    if plan_id in ["pro", "elite"]:
                        has_pro_plan = True
            except Exception:
                pass  

        if self.use_pro_domains and has_pro_plan:
            filtered = [d["domain"] for d in raw_domains if isinstance(d, dict) and d.get("premium") is True]
            if not filtered:
                filtered = [d["domain"] for d in raw_domains if isinstance(d, dict) and not d.get("premium")]
        else:
            filtered = [d["domain"] for d in raw_domains if isinstance(d, dict) and not d.get("premium")]

        return filtered

    def delete_mailbox(self, email: str) -> bool:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/inboxes",
                headers=self.headers,
                timeout=10
            )
            if not resp.ok:
                return False
            
            inboxes_data = resp.json().get("inboxes", [])
            inbox_id = None
            for ibox in inboxes_data:
                if ibox.get("address").lower() == email.lower():
                    inbox_id = ibox.get("id")
                    break
            
            if not inbox_id:
                return False

            delete_resp = requests.delete(
                f"{self.BASE_URL}/inboxes/{inbox_id}",
                headers=self.headers,
                timeout=10
            )
            return delete_resp.ok
        except Exception:
            return False