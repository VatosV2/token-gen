from Core.NexusColors.color import NexusColor
from Core.communication.mail.providers.cybertemp import CybertempApi

class TokenGenerator:
    def __init__(
        self,
        context_factory,
        register,
        captcha,
        email_verifier,
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
        
        self.email_verifier = email_verifier
        self.storage = storage
        self.humaniser = humaniser
        self.logger = logger
        self.config = config
        self.mail_api = mail_api
        self.stats = stats

    def run(self):
        try: 
            ctx = self.context_factory.create()

            self.register.start(ctx)
            self.captcha.solve(ctx)
            self.register.finish(ctx)

            self.storage.save(ctx, "tokens.txt")
            
            ctx.upn = self.mail_api.wait_for_verification(email=ctx.email, password=ctx.password)
            self.email_verifier.verify_token(ctx)
            
            if isinstance(self.mail_api, CybertempApi):
                self.mail_api.delete_mailbox(email=ctx.email)
                
            self.storage.save(ctx, "email_verified.txt")

            if self.config["humanizer"]["enabled"]:
                succses = self.humaniser.run()
                if succses:
                    self.storage.save(ctx, "humanized.txt")
                
        except Exception as e:
            if isinstance(self.mail_api, CybertempApi) and ctx.email:
                self.mail_api.delete_mailbox(email=ctx.email)
            self.logger.log(f"Account generation failed -> {NexusColor.RED}{e} ")
        