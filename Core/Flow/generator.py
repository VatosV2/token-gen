from Core.NexusColors.color import NexusColor
from Core.communication.mail.providers.cybertemp import CybertempApi
from Core.communication.mail.providers.zeromail import ZeromailApi

class TokenGenerator:
    def __init__(
        self,
        context_factory,
        register,
        captcha,
        email_verifier,
        phone_verifier,
        storage,
        humaniser,
        logger,
        config,
        mail_api,
        stats
    ):
        self.context_factory = context_factory
        self.register = register
        self.captcha = captcha
        self.phone_verifier = phone_verifier
        self.email_verifier = email_verifier
        self.storage = storage
        self.humaniser = humaniser
        self.logger = logger
        self.config = config
        self.mail_api = mail_api
        self.stats = stats

    def run(self):
        ctx = None
        try: 
            ctx = self.context_factory.create()

            self.register.start(ctx)
            self.captcha.solve(ctx)
            self.register.finish(ctx)

            self.storage.save(ctx, "tokens")
            
            ctx.upn = self.mail_api.wait_for_verification(email=ctx.email, password=ctx.password)
            self.email_verifier.verify_token(ctx)
            
            if isinstance(self.mail_api, (CybertempApi, ZeromailApi)):
                self.mail_api.delete_mailbox(email=ctx.email)
                
            self.storage.save(ctx, "email_verified")
            
            if self.config["verification"]["phone_verification"]:
                phone_verified = self.phone_verifier.verify_phone(ctx)
                if phone_verified:
                    self.storage.save(ctx, "phone_verified")
                else:
                    self.logger.log(f"Failed to verify phone for {NexusColor.RED}{ctx.phone_number}{NexusColor.RESET}")

            if self.config["humanizer"]["enabled"]:
                success = self.humaniser.run()
                if success:
                    self.storage.save(ctx, "humanized")
                    self.stats.humanized += 1
                
        except Exception as e:
            self.logger.log(
                f"Account generation failed -> {NexusColor.RED}{e}"
            )

        finally:
            if isinstance(self.mail_api, (CybertempApi, ZeromailApi)) and ctx and hasattr(ctx, "email"):
                try:
                    self.mail_api.delete_mailbox(email=ctx.email)
                except Exception:
                    pass
        