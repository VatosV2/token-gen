import io
import random

from base64 import b64encode
from pathlib import Path
from typing import Optional, List
from PIL import Image

from Core.discord.utils import DiscordUtils
from Core.NexusColors.color import NexusColor

class Humaniser:
    def __init__(self,config: dict, session, logger):
        self.config = config.get("humanizer", {})

        self.session = session
        self.logger = logger
        
        self.profile_dir = Path("io/input/profiles")
        self.avatar_dir = self.profile_dir / "avatars"

        self.bios = self._load("bio.txt") if self.config.get("bio") else None
        self.names = self._load("names.txt") if self.config.get("display_name") else None
        self.pronouns = self._load("pronouns.txt") if self.config.get("pronouns") else None

    def _load(self, filename: str) -> Optional[List[str]]:
        path = self.profile_dir / filename
        if not path.exists():
            return None
        return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def _random(self, data: Optional[List[str]]) -> Optional[str]:
        return random.choice(data) if data else None

    def _random_avatar(self) -> Optional[Path]:
        if not self.config.get("avatar"):
            return None
        files = list(self.avatar_dir.glob("*.png")) + list(self.avatar_dir.glob("*.jpg"))
        return random.choice(files) if files else None

    def _avatar_to_b64(self, path: Path, max_mb: int = 8) -> Optional[str]:
        max_bytes = max_mb * 1024 * 1024

        with Image.open(path) as img:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()

            while len(data) > max_bytes:
                w, h = img.size
                if w < 64 or h < 64:
                    return None
                img = img.resize((w // 2, h // 2), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                data = buf.getvalue()

        return b64encode(data).decode()

    def _discord_error(self, r) -> str:
        try:
            data = r.json()
            if isinstance(data, dict):
                msg = data.get("message", "Unknown error")
                code = data.get("code")
                errors = data.get("errors")

                if errors:
                    return f"{r.status_code} | {msg} | {errors}"
                if code:
                    return f"{r.status_code} | {msg} (code {code})"

                return f"{r.status_code} | {msg}"
        except Exception:
            pass

        return f"{r.status_code} | {r.text[:200]}"


    def run(self) -> bool | str:
        
        DiscordUtils.get_session_id(self.session.headers["authorization"])
        
        try:
            self.session.headers.update({"referer": "https://discord.com/channels/@me"})
            
            if self.config.get("bio"):
                bio = self._random(self.bios)
                if bio:
                    r = self.session.patch(
                        "https://discord.com/api/v9/users/@me",
                        json={"bio": bio}
                    )
                    if not r.ok:
                        if r.status_code == 401:
                            raise RuntimeError("Token Invalid")
                        self.logger.log(f"Failed to update Bio -> {self._discord_error(r)}")
                        return 
                    self.logger.log(f"Updated Bio -> {NexusColor.GREEN}{bio}")

            if self.config.get("pronouns"):
                pronouns = self._random(self.pronouns)
                if pronouns:
                    r = self.session.patch(
                        "https://discord.com/api/v9/users/@me",
                        json={"pronouns": pronouns}
                    )
                    if not r.ok:
                        if r.status_code == 401:
                             raise RuntimeError("Token Invalid")
                        self.logger.log(f"Failed to update Pronouns -> {self._discord_error(r)}")
                        return 
                    self.logger.log(f"Updated Pronouns -> {NexusColor.GREEN}{pronouns}")

            if self.config.get("display_name"):
                name = self._random(self.names)
                if name:
                    r = self.session.patch(
                        "https://discord.com/api/v9/users/@me",
                        json={"global_name": name}
                    )
                    if not r.ok:
                        if r.status_code == 401:
                            raise RuntimeError("Token Invalid")
                        self.logger.log(f"Failed to update Display Name -> {self._discord_error(r)}")
                        return
                    self.logger.log(f"Updated Name -> {NexusColor.GREEN}{name}")

            if self.config.get("avatar"):
                avatar = self._random_avatar()
                if avatar:
                    b64 = self._avatar_to_b64(avatar)
                    if b64:
                        r = self.session.patch(
                            "https://discord.com/api/v9/users/@me",
                            json={"avatar": f"data:image/png;base64,{b64}"}
                        )
                        if not r.ok:
                            if r.status_code == 401:
                                raise RuntimeError("Token Invalid")
                            self.logger.log(f"Failed to update Avatar -> {self._discord_error(r)}")
                            return 
                        self.logger.log(f"Updated Avatar -> {NexusColor.GREEN}{str(avatar)}")

            return True

        except Exception as e:
            return f"exception | {e}"
