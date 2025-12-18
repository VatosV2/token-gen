import sys
import time
from typing import Optional, Dict

from camoufox.sync_api import Camoufox

from ..NexusColors.color import NexusColor
from ..Utils.utils import Utils, JsInjection, Config
from ..Utils.proxy_manager import ProxyManager
from .captcha_solver import CaptchaSolver
from ..Helper.mail import NexusMailApi, MailVerify
from ..Helper.huminazer import DiscordHuminazer
from ..Utils.logger import Logger


class DiscordRegister:
    def __init__(self) -> None:
        self.proxy_manager: ProxyManager = ProxyManager()
        self.password: str = Utils.random_password()
        self.day, self.month, self.year = Utils.random_birthday()
        self.config: Dict = Config.config
        self.status: str = ""
        self.js_injector: JsInjection = JsInjection()


    @staticmethod
    def _censor_token(token: str, visible_start: int = 6, visible_end: int = 6) -> str:
        if len(token) <= visible_start + visible_end:
            return "***"
        return f"{token[:visible_start]}***{token[-visible_end:]}"
    
    def register(self, worker_id: int, on_browser_closed=None) -> str:


        proxy: Optional[Dict[str, str]] = self.proxy_manager.get_proxy(worker_id=worker_id)
        if not proxy:
            proxy = self.proxy_manager.wait_for_proxies(worker_id)

        start_time_startup: float = time.time()
        Logger.STATUS = f"{NexusColor.YELLOW}Starting Browser"
        Logger.queue_log(worker_id=worker_id)
        
        with Camoufox(
            proxy=proxy,
            headless=False,
            locale="en-US",
            geoip=True
            ) as browser:

            page = browser.new_page()

            
            page.goto("https://discord.com/register", timeout=30_000, wait_until="networkidle")
            self.js_injector.setup_js(page)

            elapsed_time_startup: float = time.time() - start_time_startup
            Logger.STATUS = f"{NexusColor.YELLOW}Loading Page"
            Logger.queue_log(worker_id=worker_id)

            domain: str = Utils.get_domain()
            username: str = Utils.random_string()
            email: str = NexusMailApi().create_account(
                email=f"{username}@{domain}",
                password=self.password
            )
            
            start_time: float = time.time()
            Logger.STATUS = f"{NexusColor.YELLOW}Filling Inputs"
            Logger.queue_log(worker_id=worker_id)

            
            page.wait_for_selector('input[name="email"]', timeout=10_000)
            self.js_injector.set_input(page, 'input[name="email"]', email)
            self.js_injector.set_input(page, 'input[name="username"]', username)
            self.js_injector.set_input(page, 'input[name="password"]', self.password)

            self.js_injector.set_dropdown(page, "Month", self.month)
            self.js_injector.set_dropdown(page, "Day", self.day)
            self.js_injector.set_dropdown(page, "Year", self.year)

            self.js_injector.click_all_checkboxes(page)

            page.wait_for_selector('button[type="submit"]', timeout=3_000)
            self.js_injector.click_element(page, 'button[type="submit"]')

            hcap_start: float = time.time()
            solver: CaptchaSolver = CaptchaSolver(page, worker_id)
            Logger.STATUS = f"{NexusColor.YELLOW}Waiting For Captcha"
            Logger.queue_log(worker_id=worker_id)

            frame = solver.find_hcaptcha_frame(page=page, timeout=self.config.get("captcha_timeout"))
            if not frame:
                Logger.STATUS = f"{NexusColor.RED}Hcaptcha not found."
                Logger.queue_log(worker_id=worker_id)
                return "ignore"

            hcap_time: float = time.time() - hcap_start
            hcap_time_solve: float = solver.solve_accessibility_hcaptcha(frame=frame)

            token: Optional[str] = self.js_injector.wait_for_discord_token(page=page)
            if not token:
                try:
                    frame2 = solver.find_hcaptcha_frame(page=page, timeout=10)
                    if frame2:
                        hcap_time = time.time() - hcap_start
                        hcap_time_solve = solver.solve_accessibility_hcaptcha(frame2)
                    else:
                        return "ignore"
                except Exception as e:
                    print(e)
                    return "Failed to fetch Token"

            token = self.js_injector.wait_for_discord_token(page=page)
            if not token:
                return "ignore"

            humanized: bool = False
            humanize_time: float = 0.0


            try:
                token_status: Dict[str, str] = Utils.check_discord_token(token=token, proxy=proxy)
            except Exception as e:
                token_status = {"status": "Invalid"}

            elapsed_time: float = time.time() - start_time

            if token_status["status"] == "Valid":
                Logger.STATUS = f"{NexusColor.YELLOW}Verifying Token.."
                Logger.queue_log(worker_id=worker_id)


                start_time_verify: float = time.time()
                upn = NexusMailApi().get_inbox(email=email, password=self.password)
                verify = MailVerify(proxy_dict=proxy)
                ev_token: Optional[str]
                ev: bool
                ev_token, ev = None, False
                elapsed_time_verify: float = time.time() - start_time_verify if ev else 0.0

                if ev:
                    Logger.STATUS = f"{NexusColor.GREEN}Token Verified!"
                    Logger.queue_log(worker_id=worker_id)

                    token = ev_token

                if self.config["humanizer"]["enabled"] and ev:
                    Logger.STATUS = f"{NexusColor.YELLOW}Humanizing Token..."
                    Logger.queue_log(worker_id=worker_id)

                    humanizer = DiscordHuminazer(worker_id=worker_id)
                    humanize_start: float = time.time()
                    humanized = humanizer.humanize_account(token, proxy)
                    humanize_time = time.time() - humanize_start
                    if humanized:
                        Logger.STATUS = f"{NexusColor.GREEN}Token Humanized!"
                        Logger.queue_log(worker_id=worker_id)


                with open("io/output/tokens.txt", "a", encoding="utf-8") as f:
                    f.write(f"{email}:{self.password}:{token}\n")

                humanize_status: str = f"{NexusColor.GREEN}Humanized" if humanized else f"{NexusColor.RED}Not Humanized"
                ev_status: str = f"{NexusColor.GREEN}Email Verified" if ev else f"{NexusColor.RED}Unclaimed"

                Logger.STATUS = f"{NexusColor.GREEN}Token Generated!"
                Logger.queue_log(worker_id=worker_id)

                sys.stdout.write("\n")

                self.print_stats(
                    worker_id, token, elapsed_time, elapsed_time_startup,
                    hcap_time, hcap_time_solve, humanize_time,
                    elapsed_time_verify, humanize_status, ev_status
                )
            else:
                with open(f"io/output/{token_status['status']}.txt", "a", encoding="utf-8") as f:
                    f.write(f"{email}:{self.password}:{token}\n")

                Logger.STATUS = f"{NexusColor.GREEN}Token Generated!"
                Logger.queue_log(worker_id=worker_id)

                logs_cfg: Dict = self.config.get("logs", {})

                display_token = token
                if logs_cfg.get("censor_token", False):
                    display_token = self._censor_token(token)

                stats: list[tuple[str, str, bool]] = [
                    ("Token", display_token, True),
                    ("Status", f"{token_status['status']}", True)
                ]

                Logger.queue_stats(worker_id, stats)
                time.sleep(30)
        return token_status["status"]

    def print_stats(
        self,
        worker_id: int,  
        token: str,
        elapsed_time: float,
        startup_time: float,
        hcap_wait: float,
        hcap_solve: float,
        humanize_time: float,
        email_verify_time: float,
        humanize_status: str,
        ev_status: str
    ) -> None:
        logs_cfg: Dict = self.config.get("logs", {})

        display_token = token
        if logs_cfg.get("censor_token", False):
            display_token = self._censor_token(token)

        stats: list[tuple[str, str, bool]] = [
            ("Token", display_token, True),
            ("Generation Time", f"{elapsed_time:.2f}s", logs_cfg.get("generation_time", True)),
            ("Browser Startup Time", f"{startup_time:.2f}s", logs_cfg.get("startup_time", False)),
            ("hCaptcha Waiting Time", f"{hcap_wait:.2f}s", logs_cfg.get("hcaptcha_waiting", False)),
            ("hCaptcha Solving Time", f"{hcap_solve:.2f}s", logs_cfg.get("hcaptcha_solving", True)),
            ("Humanize Time", f"{humanize_time:.2f}s", logs_cfg.get("humanize_time", True)),
            ("Email Verify Time", f"{email_verify_time:.2f}s", logs_cfg.get("verify_time", True)),
            ("Total Time", f"{email_verify_time + humanize_time + elapsed_time + startup_time:.2f}s", logs_cfg.get("total_time", True)),
            ("Status", f"{humanize_status}, {ev_status}", True)
        ]

        Logger.queue_stats(worker_id, stats)

