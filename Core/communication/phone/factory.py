from Core.communication.phone.providers.onlinesim import OnlineSimApi

class PhoneApiFactory:
    def __init__(self, config: dict):
        self.config = config
        self.api_key = self.config["verification"]["phone_api_key"]
        self.country = self.config["verification"]["country_code"]
    
    def create(self):
        if not self.api_key:
            if self.config["verification"]["phone_verification"]:
                raise ValueError("No API Key")
        
        if self.config["verification"]["phone_provider"] == "onlinesim":
            return OnlineSimApi(self.api_key, self.country)
    