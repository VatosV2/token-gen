from Core.communication.mail.providers.cybertemp import CybertempApi
from Core.communication.mail.providers.zeromail import ZeromailApi


class MailApiFactory:
    def __init__(self, config: dict):
        self.api_key = config["verification"]["mail_api_key"]
        self.provider = config["verification"]["mail_provider"]
        self.pro_domains = config["verification"]["pro_domains"]

    def create(self):
        if not self.api_key:
            raise ValueError("No API Key")
        
        if not self.provider:
            raise ValueError("No Mail Provider")

        if self.provider == "cybertemp":
            return CybertempApi(self.api_key)
        
        if self.provider == "zeromail":
            return ZeromailApi(self.api_key, self.pro_domains)
        
        raise ValueError(f"Unknown mail provider: {self.provider}")