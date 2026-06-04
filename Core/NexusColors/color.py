"Colors.py File for handeling converting colors and saving color variables."

import re
import random
from typing import Tuple


class Color:

    @staticmethod
    def validate_hex(hex_code: str):
        if not (hex_code.startswith("#") and len(hex_code) in (4, 7)):
            raise ValueError(
                "Hex color code must start with '#' and be 4 or 7 characters long."
            )
        if len(hex_code) == 7 and not re.match(
            r"^#[0-9A-Fa-f]{6}$", hex_code
        ):
            raise ValueError(
                "Invalid hex color code format. It should be in the form '#RRGGBB'."
            )
        if len(hex_code) == 4 and not re.match(
            r"^#[0-9A-Fa-f]{3}$", hex_code
        ):
            raise ValueError(
                "Invalid shorthand hex color code format. It should be in the form '#RGB'."
            )

    @staticmethod
    def expand_shorthand_hex(hex_code: str) -> str:
        if len(hex_code) == 4:
            return "#" + "".join(c * 2 for c in hex_code[1:])
        return hex_code

    @staticmethod
    def hex_to_ansi(hex_code: str, is_background: bool = False) -> str:
        Color.validate_hex(hex_code)
        hex_code = Color.expand_shorthand_hex(hex_code).lstrip("#")
        r, g, b = tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))
        base_code = 48 if is_background else 38
        return f"\033[{base_code};2;{r};{g};{b}m"

    @staticmethod
    def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
        Color.validate_hex(hex_code)
        hex_code = Color.expand_shorthand_hex(hex_code).lstrip("#")
        return tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_ansi(
        r: int, g: int, b: int, is_background: bool = False
    ) -> str:
        if not all(0 <= value <= 255 for value in (r, g, b)):
            raise ValueError("RGB values must be between 0 and 255.")
        base_code = 48 if is_background else 38
        return f"\033[{base_code};2;{r};{g};{b}m"


class NexusColor:
    COLOR_HEX_LIST = ["#0fafff", "#630fff", "#26a178", "#9b6310"]
    RESET: str = "\033[0m"
    NEXUS: str = Color.hex_to_ansi("#cc00aa")
    RED: str = Color.hex_to_ansi("#ff001e")
    GREEN: str = Color.hex_to_ansi("#44ff00")
    LIGHTBLACK: str = Color.hex_to_ansi("#5c5e5b")
    LIGHTBLUE: str = Color.hex_to_ansi("#03f8fc")
    YELLOW: str = Color.hex_to_ansi("#fcf803")
    MAIN_COLOR: str = Color.hex_to_ansi(random.choice(COLOR_HEX_LIST))