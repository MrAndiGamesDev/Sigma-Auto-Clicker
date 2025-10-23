from typing import Optional
from colorama import init, Fore, Style

class Logging:
    def __init__(self) -> None:
        init(autoreset=True)

    @staticmethod
    def Log(DebugType: Optional[str], message: str) -> None:
        """Log a message with a specified debug type."""
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
        except Exception as error:
            DebugType = (DebugType or "error")
            tag = DebugType.upper()
            print(f"{Fore.RED}[{tag}]{Style.RESET_ALL} {error}{Style.RESET_ALL}")