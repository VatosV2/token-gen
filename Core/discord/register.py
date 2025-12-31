from Core.discord.utils import DiscordUtils
from Core.NexusColors.color import NexusColor
from Core.accounts.storage import TokenStorage

class DiscordRegisterService:
    def __init__(self, session, logger, stats):
        self.session = session
        self.logger = logger
        self.stats = stats

    def start(self, ctx):
        y, m, d = ctx.birthday

        payload = {
            "fingerprint": ctx.fingerprint,
            "email": ctx.email,
            "username": ctx.username,
            "password": ctx.password,
            "date_of_birth": f"{y}-{m:02d}-{d:02d}",
            "consent": True,
        }

        self.logger.log("Creating Account..")
        response = self.session.post(
            "https://discord.com/api/v9/auth/register",
            json=payload,
        )

        data = response.json()

        ctx.captcha_rqdata = data.get("captcha_rqdata")
        ctx.captcha_rqtoken = data.get("captcha_rqtoken")
        ctx.captcha_session_id = data.get("captcha_session_id")

    def finish(self, ctx):
        self.session.headers.update({
            "x-captcha-key": ctx.captcha_key,
            "x-captcha-rqtoken": ctx.captcha_rqtoken,
            "x-captcha-session-id": ctx.captcha_session_id
        })
        
        y, m, d = ctx.birthday

        payload = {
            "fingerprint": ctx.fingerprint,
            "email": ctx.email,
            "username": ctx.username,
            "password": ctx.password,
            "date_of_birth": f"{y}-{m:02d}-{d:02d}",
            "consent": True,
        }

        response = self.session.post(
            "https://discord.com/api/v9/auth/register",
            json=payload,
        )
        if not response.ok:
            raise RuntimeError(f"Register failed: {response.text}")
        
        data = response.json()
        token = data.get("token", None)
        
        if token:
            ctx.token = token
            self.session.headers.update({"authorization": token})
            token_status = DiscordUtils.check_discord_token(session=self.session).get("status", "Invalid")
            if token_status == "Valid":
                self.stats.mark_valid()
                self.logger.log_token(f"Succsefully Created Account -> {NexusColor.GREEN} ", token)
                return
            
            if token_status == "invalid":
                self.stats.mark_invalid()
                
            if token_status == "locked":
                self.stats.mark_locked()
            
                
            TokenStorage().save(ctx=ctx, file=f"{token_status}.txt")
            raise RuntimeError(f"{token_status} Token")
        