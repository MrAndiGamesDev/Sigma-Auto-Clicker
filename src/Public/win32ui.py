import sys
import winreg
import platform
import ctypes
from ctypes import wintypes
from typing import List, Dict, Any, Optional, Final

# ------------------------------------------------------------------
# Logging helpers
# ------------------------------------------------------------------
class _FallbackLogger:
    @staticmethod
    def log(level: str, message: str) -> str:
        return f"[{level.upper()}] {message}"

class _DebugLogger:
    def __init__(self, base_logger):
        self._base_logger = base_logger
        self._debug_enabled = False

    def enable_debug(self, can_debug: bool) -> None:
        self._debug_enabled = bool(can_debug)

    def log(self, level: str, message: str) -> str:
        if self._debug_enabled or level.lower() != "debug":
            return self._base_logger(level, message)
        return ""

def _get_logger():
    try:
        from src.Packages.CustomLogging import Logging
        return _DebugLogger(Logging.log)
    except Exception:
        return _DebugLogger(_FallbackLogger.log)

# ------------------------------------------------------------------
# Win32UI
# ------------------------------------------------------------------
class Win32UI:
    """
    Encapsulates Windows-specific UI enhancements:
    DPI awareness and Windows 11 Mica/Acrylic backdrop.
    """

    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2: Final[int] = -4
    DWMWA_USE_IMMERSIVE_DARK_MODE: Final[int] = 20
    DWMWA_SYSTEMBACKDROP_TYPE: Final[int] = 38
    WIN11_MIN_BUILD: Final[int] = 22000
    SYSTEMBACKDROP_MICATYPE: Final[int] = 2  # DWMSBT_MAINWINDOW
    _LOGGER: Final = _get_logger()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @classmethod
    def _is_win32(cls) -> bool:
        """Return True if the current platform is Windows."""
        return sys.platform == "win32"

    @classmethod
    def is_light_theme(cls) -> bool:
        """Detect Windows 11 light/dark mode via registry."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 1
        except Exception:
            return True  # default to light

    @classmethod
    def apply(cls, hwnd: Optional[int] = None) -> None:
        """
        Apply Windows-specific UI enhancements:
        1. Per-monitor DPI awareness (V2).
        2. Windows 11 Mica backdrop for the main window.

        Args:
            hwnd: Optional window handle (int) to target. If None, enhancements
                  that require a handle are skipped.
        """
        if not cls._is_win32():
            return

        cls._set_dpi_awareness()
        if hwnd is not None:
            cls._set_mica_backdrop(hwnd)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @classmethod
    def _set_dpi_awareness(cls) -> None:
        """Set DPI awareness to avoid blurry UI on high-DPI displays."""
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(
                cls.DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
        except (AttributeError, OSError):
            # Fallback for older Windows versions
            ctypes.windll.user32.SetProcessDPIAware()

    @classmethod
    def _unhook_windows_hookex(cls):
        if cls._is_win32():
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(0)
            except Exception:
                pass

    @classmethod
    def _set_mica_backdrop(cls, hwnd: int) -> None:
        """Apply Mica backdrop on Windows 11."""
        try:
            build = int(platform.version().split(".")[2])
            if build < cls.WIN11_MIN_BUILD:
                return
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(2)),
                ctypes.sizeof(ctypes.c_int),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(ctypes.c_int(cls.SYSTEMBACKDROP_MICATYPE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except (AttributeError, OSError, ValueError, IndexError):
            # Silently ignore on unsupported systems
            cls._LOGGER.log("debug", "Mica backdrop not applied (unsupported system)")