import re

from Core.accounts.context import AccountContext
from Core.utils.utils import Utils
from Core.discord.utils import DiscordUtils
from Core.discord.headers import HeaderBuilder
from Core.NexusColors.color import NexusColor

class AccountContextFactory:
    def __init__(self, session, proxy, logger, mail_api, config):
        self.session = session
        self.proxy = proxy
        self.logger = logger
        self.mail_api = mail_api
        self.config = config

    def create(self) -> AccountContext:
        dcfduid, sdcfduid = DiscordUtils.fetch_cookies(self.session)
        fingerprint = (
            Utils.get_fingerprint()
            if self.config["generator"]["custom_fingerprints"] and Utils.has_fingerprints()
            else DiscordUtils.get_fingerprint(dcfduid, sdcfduid, self.session)
        )
        
        mail_string = Utils.random_string()
        username = DiscordUtils._get_username() if self.config["humanizer"]["enabled"] and self.config["humanizer"]["username"] else mail_string
        password = Utils.random_password()
        
        email = self.mail_api.create_account(mail_string, password)
        invite = (
            re.search(
                r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([A-Za-z0-9-]+)",
                self.config["generator"].get("invite", ""),
            ).group(1)
            if re.search(
                r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([A-Za-z0-9-]+)",
                self.config["generator"].get("invite", ""),
            )
            else self.config["generator"].get("invite", None)
        )        
        birthday = Utils.random_birthday()
        y, m, d = birthday

        self.logger.log(
            f"Got Account Context -> "
            f"{NexusColor.MAIN_COLOR}{email}:{password}{NexusColor.LIGHTBLACK} | "
            f"{NexusColor.MAIN_COLOR}{y}-{m:02d}-{d:02d}{NexusColor.LIGHTBLACK} | "
            f"{NexusColor.MAIN_COLOR}{fingerprint[:12]}{NexusColor.LIGHTBLACK}"
            f"{f' | {NexusColor.MAIN_COLOR}{invite}' if invite else ''}"
            f"{NexusColor.RESET}"
        )
        
        
        headers = HeaderBuilder(self.session).build(fp=fingerprint, invite_code=invite)
        self.session.headers.update(headers)

        return AccountContext(
            fingerprint=fingerprint,
            username=username,
            password=password,
            email=email,
            birthday=birthday,
            proxy=self.proxy
        )
