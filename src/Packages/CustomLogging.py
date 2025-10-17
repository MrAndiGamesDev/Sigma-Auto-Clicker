from colorama import init, Fore, Style
from typing import Optional

class Logging:
    def __init__(self):
        init(autoreset=True)

    @staticmethod
    def Log(DebugType: Optional[str], message: str):
        try:
            DebugType = (DebugType or "info").lower()
            color_map = {
                "error": Fore.RED,
                "info": Fore.WHITE,
                "success": Fore.GREEN,
                "warning": Fore.YELLOW,
            }
            color = color_map.get(DebugType, Fore.WHITE)
            tag = DebugType.upper()
            print(f"{color}[{tag}]{Style.RESET_ALL} {message}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}{Style.RESET_ALL}")
