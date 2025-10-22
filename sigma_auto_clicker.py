import logging as _logging
import sys
import time
import platform
import threading
import subprocess
import urllib.request
import requests
import webbrowser
import pyautogui
import keyboard
import socket
import psutil
import os
import random
import re
import time
# from pypresence import Presence
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Final
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit,
    QComboBox, QSystemTrayIcon, QMenu, QFormLayout, QMessageBox, QDialog
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal as pyqtSignal, QObject
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

_LOGGING: Final = _logging.getLogger(__name__)

# PyAutoGUI settings
try:
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False
except Exception as e:
    _LOGGING.error("Failed to set PyAutoGUI settings: %s", e)

class Logger:
    """Centralized logging for the application."""
    def __init__(self, log_widget: Optional[QTextEdit] = None):
        self.log_widget = log_widget

    def log(self, message: str) -> None:
        """Log a message to the Activity Log tab or print if no widget is set."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}]: {message}"
        if self.log_widget:
            self.log_widget.append(formatted_message)
            self.log_widget.verticalScrollBar().setValue(self.log_widget.verticalScrollBar().maximum())
        else:
            print(formatted_message)

@dataclass(slots=True, frozen=True)
class UpdateLogEntry:
    date: str
    version: str
    description: str

    def to_bullets(self, bullet: str = "•") -> str:
        """Return a bullet-point representation of the description."""
        desc = self.description.strip()
        points = [p.strip() for p in desc.split(". ") if p.strip()]
        if "and so much more" in desc.lower():
            points.append("Various additional improvements")
        if not points:
            points = ["No details provided."]
        return "\n".join(f"  {bullet} {p}" for p in points)

class _MetaConfig(type):
    """Metaclass that turns the namespace into read-only class attributes."""
    def __setattr__(cls, name: str, value: Any) -> None:
        raise AttributeError(f"{cls.__name__} is immutable")

class Config(metaclass=_MetaConfig):
    """Immutable application configuration constants."""

    # --- Application identity -------------------------------------------------
    APP_NAME: Final[str] = "Sigma Auto Clicker"
    AUTHORNAME: Final[str] = "MrAndiGamesDev"
    GITHUB_REPO: Final[str] = f"{AUTHORNAME}/Sigma-Auto-Clicker"
    ICON_URL: Final[str] = (
        f"https://raw.githubusercontent.com/{AUTHORNAME}/My-App-Icons/main/mousepointer.ico"
    )

    # --- Defaults -------------------------------------------------------------
    DEFAULT_VERSION: Final[str] = "1.0.0"
    DEFAULT_THEME: Final[str] = "Dark"
    DEFAULT_COLOR: Final[str] = "Blue"
    DEFAULT_ADMIN_MODE: Final[bool] = False
    DEFAULT_SETTINGS: Final[Dict[str, str]] = {
        "click_count": "1",
        "loop_count": "0",
        "click_delay": "1",
        "cycle_delay": "0.5",
    }

    # --- Internals ------------------------------------------------------------
    UPDATE_CHECK_INTERVAL: Final[int] = 24 * 60 * 60 * 1000  # ms
    LOCK_PORT: Final[int] = random.randint(1024, 49151)
    PORTS: Final[str] = "127.0.0.1"

    # --- Platform information -------------------------------------------------
    SYSTEM: Final[str] = platform.system()
    RELEASE: Final[str] = platform.release()
    VERSION: Final[str] = platform.version()
    MACHINE: Final[str] = platform.machine()

    # --- Paths ----------------------------------------------------------------
    HOME_DIR: Final[Path] = Path.home()
    APPDATA_DIR: Final[Path] = (
        HOME_DIR / "AppData" / "Roaming" / "SigmaAutoClicker"
        if SYSTEM == "Windows"
        else HOME_DIR / ".sigma_autoclicker"
    )

    # --- File names -----------------------------------------------------------
    HOTKEY: Final[str] = "Ctrl+F"
    HOTKEY_FILE: Final[Path] = APPDATA_DIR / "hotkey.txt"
    APP_ICON: Final[Path] = APPDATA_DIR / "mousepointer.ico"
    UPDATE_CHECK_FILE: Final[Path] = APPDATA_DIR / "last_update_check.txt"
    VERSION_FILE: Final[Path] = APPDATA_DIR / "current_version.txt"
    VERSION_CACHE_FILE: Final[Path] = APPDATA_DIR / "version_cache.txt"
    LOCK_FILE: Final[Path] = APPDATA_DIR / f"app.lock.{LOCK_PORT}"
    ADMIN_MODE_FILE: Final[Path] = APPDATA_DIR / "admin_mode.txt"

    # --- Update history --------------------------------------------------------
    UPDATE_LOGS: Final[List[UpdateLogEntry]] = [
        UpdateLogEntry(
            date="2025-10-22",
            version="1.1.2-beta.1",
            description=(
                "Integrated Discord Rich Presence (Currently broken) removed for now. "
            ),
        ),
        UpdateLogEntry(
            date="2025-10-22",
            version="1.1.2",
            description=(
                "Enhanced admin mode toggle with improved functionality. "
                "Reduced resource usage via performance optimizations. "
                "Resolved session persistence and caching bugs. "
                "Added data-sync API endpoints. "
                "Strengthened network error handling. "
            ),
        ),
        UpdateLogEntry(
            date="2025-10-19",
            version="1.1.0",
            description=(
                "Added admin mode toggle for enhanced functionality. "
                "Improved tab navigation and layout. "
                "Optimized performance for lower resource usage. "
                "Enhanced accessibility with ARIA labels. "
                "Added dark mode toggle with system theme detection. "
                "Fixed bugs related to session persistence and caching. "
                "Introduced API endpoints for data syncing. "
                "Improved error handling for network issues. "
                "Upgraded encryption protocols for data transmission."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-18",
            version="1.0.9",
            description=(
                "Tabs Improvements "
                "Removed Notification during minimized "
                "and so much more!"
            ),
        ),
        UpdateLogEntry(
            date="2025-10-17",
            version="1.0.8",
            description=(
                "Enhanced UI with refined styling and improved responsiveness. "
                "Fixed bugs related to theme switching and button states."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-16",
            version="1.0.7",
            description=(
                "Fixed miscellaneous application bugs for improved stability. "
                "Improved error handling in the update checker."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-16",
            version="1.0.6",
            description=(
                "Resolved issues in the update management system. "
                "Added support for caching version information."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-16",
            version="1.0.5",
            description=(
                "Introduced automatic update checking. "
                "Added version management features and improved UI code structure."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-15",
            version="1.0.4",
            description=(
                "Fixed Light Mode rendering issues. "
                "Improved UI consistency across themes."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-14",
            version="1.0.3",
            description=(
                "Added Update Logs tab for version history. "
                "Introduced customizable color themes."
            ),
        ),
        UpdateLogEntry(
            date="2025-10-13",
            version="1.0.0",
            description=f"Initial release of {APP_NAME}.",
        ),
    ]

    @staticmethod
    def format_update_logs(
        separator: str = "\n",
        logger: Optional[Logger] = None,
        bullet: str = "•",
    ) -> str:
        """Return a formatted string with the update history."""
        logger = logger or Logger(None)
        if not Config.UPDATE_LOGS:
            logger.log("⚠️ No update logs available.")
            return "No update logs available."

        try:
            entries = [
                f"Version {entry.version} ({entry.date}){separator.rstrip()}\n{entry.to_bullets(bullet)}"
                for entry in Config.UPDATE_LOGS
            ]
        except Exception as e:
            logger.log(f"⚠️ Error formatting update logs: {e}")
            return "No valid update logs available."

        footer = "=" * 39
        header = f"🖱️ {Config.APP_NAME} Update History 🖱️\n{footer}\n"
        return f"{header}{separator.join(entries)}\n{footer}\n"

    @staticmethod
    def load_hotkey() -> str:
        """Return the hotkey stored on disk or the default."""
        return FileManager.read_file(Config.HOTKEY_FILE, Config.HOTKEY) or Config.HOTKEY

    @staticmethod
    def save_hotkey(hotkey: str) -> None:
        """Persist the given hotkey to disk."""
        FileManager.write_file(Config.HOTKEY_FILE, hotkey.strip())

    @staticmethod
    def load_admin_mode() -> bool:
        """Return the admin-mode flag stored on disk or the default."""
        content = FileManager.read_file(Config.ADMIN_MODE_FILE)
        if content is None:
            return Config.DEFAULT_ADMIN_MODE
        return content.lower() == "true"

    @staticmethod
    def save_admin_mode(admin_mode: bool) -> None:
        """Persist the admin-mode flag to disk."""
        FileManager.write_file(Config.ADMIN_MODE_FILE, str(admin_mode).lower())

class FileManager:
    """Handles file operations and persistence."""

    @staticmethod
    def ensure_app_directory() -> None:
        """Ensure app directory exists and is hidden on Windows."""
        Config.APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        if Config.SYSTEM != "Windows":
            return

        paths_to_hide = (
            Config.APPDATA_DIR,
            Config.HOTKEY_FILE,
            Config.APP_ICON,
            Config.ADMIN_MODE_FILE,
        )
        for path in paths_to_hide:
            if not path.exists():
                continue
            try:
                subprocess.run(
                    ["attrib", "+H", str(path)],
                    capture_output=True,
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                _LOGGING.warning("Failed to hide %s: %s", path, exc)

    @staticmethod
    def download_icon() -> str:
        """Download and cache application icon."""
        FileManager.ensure_app_directory()
        if Config.APP_ICON.exists():
            return str(Config.APP_ICON)

        try:
            urllib.request.urlretrieve(Config.ICON_URL, Config.APP_ICON)
        except Exception as exc:
            _LOGGING.error("Failed to download icon: %s", exc)
            Config.APP_ICON.touch(exist_ok=True)
        return str(Config.APP_ICON)

    @staticmethod
    def read_file(filepath: Path, default: str | None = None) -> str | None:
        """Read content from file with validation."""
        if not filepath.exists():
            return default
        try:
            content = filepath.read_text(encoding="utf-8").strip()
            return content or default
        except Exception as exc:
            _LOGGING.error("Error reading %s: %s", filepath, exc)
            return default

    @staticmethod
    def write_file(filepath: Path, content: str) -> None:
        """Write content to file."""
        FileManager.ensure_app_directory()
        try:
            filepath.write_text(content.strip(), encoding="utf-8")
            _LOGGING.debug("Wrote to %s: %s", filepath, content)
        except Exception as exc:
            _LOGGING.error("Error writing to %s: %s", filepath, exc)

class HotkeyManager:
    """Manages hotkey registration and validation."""

    _VALID_MODIFIERS = {'ctrl', 'alt', 'shift', 'cmd', 'win', 'control', 'command'}

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.current_hotkey = Config.load_hotkey()

    def register_hotkey(self, hotkey: str, callback: callable) -> bool:
        """Register a hotkey with the keyboard library."""
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(hotkey, callback)
            self.current_hotkey = hotkey
            self.logger.log(f"Hotkey '{hotkey}' registered")
            return True
        except Exception as e:
            self.logger.log(f"Failed to register hotkey '{hotkey}': {e}")
            return False

    def validate_hotkey(self, hotkey: str) -> bool:
        """Validate hotkey format."""
        try:
            keys = [k.strip().lower() for k in hotkey.split('+')]
            if not keys:
                return False
            main_key = keys[-1]
            modifiers = keys[:-1]
            if not (
                main_key.isalnum()
                or main_key in keyboard.all_modifiers
                or len(main_key) == 1
            ):
                return False
            return all(mod in self._VALID_MODIFIERS for mod in modifiers)
        except Exception:
            return False

    def update_hotkey(self, new_hotkey: str, callback: callable) -> bool:
        """Update the current hotkey."""
        if not new_hotkey:
            self.logger.log("❌ No hotkey provided")
            return False
        if not self.validate_hotkey(new_hotkey):
            self.logger.log(
                f"❌ Invalid hotkey format: '{new_hotkey}'. "
                "Use format like 'Ctrl+F' or 'Alt+Shift+G'"
            )
            return False
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(new_hotkey, lambda: None)
            keyboard.unhook_all()
            Config.save_hotkey(new_hotkey)
            self.register_hotkey(new_hotkey, callback)
            self.logger.log(f"✅ Hotkey updated to '{new_hotkey}'")
            return True
        except Exception as e:
            self.logger.log(f"❌ Failed to set hotkey '{new_hotkey}': {e}")
            self.register_hotkey(self.current_hotkey, callback)
            return False

class ThemeManager:
    """Centralized, data-driven theming for the entire application."""

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    _BASE_STYLE_TEMPLATE: Final[str] = """
        QMainWindow {{ background-color: {main_bg}; color: {main_fg}; }}
        QGroupBox {{ font-weight: bold; border: 1px solid {border_color};
                    border-radius: 8px; margin-top: 10px; padding: 10px;
                    color: {group_fg}; background-color: {group_bg}; }}
        QLabel {{ color: {label_fg}; }}
        QLineEdit {{ background-color: {input_bg}; border: 1px solid {input_border};
                    border-radius: 5px; padding: 5px; color: {input_fg}; }}
        QTextEdit {{ background-color: {input_bg}; color: {input_fg};
                    border: 1px solid {input_border}; border-radius: 5px; padding: 5px; }}
        QComboBox {{ background-color: {input_bg}; color: {input_fg};
                    border: 1px solid {input_border}; border-radius: 5px; padding: 5px; }}
        QTabWidget::pane {{ border: 1px solid {border_color}; background: {tab_bg}; }}
        QTabBar::tab {{ background: {tab_bg}; color: {tab_fg}; padding: 8px; }}
        QTabBar::tab:selected {{ background: {tab_selected_bg}; color: {tab_selected_fg}; }}
    """

    _BUTTON_STYLE_TEMPLATE: Final[str] = """
        QPushButton {{ background-color: {base}; color: white; border: none;
                       border-radius: 5px; padding: 4px 8px; font-weight: bold;
                       font-size: 12px; min-height: 16px; }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
        QPushButton:disabled {{ background-color: #666; color: #999; }}
    """

    _HEX_COLOR_RE: Final[re.Pattern] = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')

    # ------------------------------------------------------------------
    # Palette definitions
    # ------------------------------------------------------------------
    BASE_STYLES: Final[Dict[str, Dict[str, str]]] = {
        "Dark": {
            "main_bg": "#1e1e2e", "main_fg": "#ffffff",
            "group_bg": "#2e2e3e", "group_fg": "#ffffff",
            "label_fg": "#ffffff",
            "input_bg": "#2e2e3e", "input_fg": "#ffffff", "input_border": "#444",
            "border_color": "#333",
            "tab_bg": "#2e2e3e", "tab_fg": "#aaa",
            "tab_selected_bg": "#6c00c4", "tab_selected_fg": "#ffffff"
        },
        "Light": {
            "main_bg": "#f0f0f0", "main_fg": "#000000",
            "group_bg": "#ffffff", "group_fg": "#000000",
            "label_fg": "#000000",
            "input_bg": "#ffffff", "input_fg": "#000000", "input_border": "#aaa",
            "border_color": "#ccc",
            "tab_bg": "#e0e0e0", "tab_fg": "#444",
            "tab_selected_bg": "#ae22ff", "tab_selected_fg": "#ffffff"
        }
    }

    COLOR_THEMES: Final[Dict[str, Dict[str, str]]] = {
        "Blue": {"base": "#0078d4", "hover": "#106ebe", "category": "Primary"},
        "Dark Gray": {"base": "#36454f", "hover": "#2f3d44", "category": "Neutral"},
        "Green": {"base": "#107c10", "hover": "#0a5f0a", "category": "Vibrant"},
        "Red": {"base": "#d13438", "hover": "#a52a2e", "category": "Vibrant"},
        "Orange": {"base": "#d24726", "hover": "#a63d1f", "category": "Vibrant"},
        "Purple": {"base": "#701cb8", "hover": "#5a1699", "category": "Vibrant"},
        "Teal": {"base": "#00838f", "hover": "#006d77", "category": "Vibrant"},
        "Indigo": {"base": "#3f51b5", "hover": "#303f9f", "category": "Primary"},
        "Amber": {"base": "#ff9800", "hover": "#f57c00", "category": "Vibrant"},
        "Cyan": {"base": "#00bcd4", "hover": "#00acc1", "category": "Vibrant"},
        "Lime": {"base": "#cddc39", "hover": "#c0ca33", "category": "Vibrant"},
        "DeepPurple": {"base": "#9c27b0", "hover": "#8e24aa", "category": "Vibrant"},
        "Brown": {"base": "#795548", "hover": "#5d4037", "category": "Neutral"},
        "Grey": {"base": "#9e9e9e", "hover": "#757575", "category": "Neutral"},
        "Gold": {"base": "#ffd700", "hover": "#ffb300", "category": "Vibrant"},
        "Turquoise": {"base": "#26c6da", "hover": "#00bcd4", "category": "Vibrant"},
        "Coral": {"base": "#ff7f50", "hover": "#ff6b35", "category": "Vibrant"},
        "Mint": {"base": "#98fb98", "hover": "#7cfc00", "category": "Vibrant"},
        "Lavender": {"base": "#e6e6fa", "hover": "#d8bfd8", "category": "Pastel"},
        "Emerald": {"base": "#2ecc71", "hover": "#27ae60", "category": "Vibrant"},
        "Slate": {"base": "#34495e", "hover": "#2c3e50", "category": "Neutral"},
        "Maroon": {"base": "#800000", "hover": "#660000", "category": "Neutral"},
        "Olive": {"base": "#808000", "hover": "#666633", "category": "Neutral"},
        "SkyBlue": {"base": "#87ceeb", "hover": "#00b7eb", "category": "Pastel"},
        "Violet": {"base": "#ee82ee", "hover": "#da70d6", "category": "Vibrant"},
        "Rose": {"base": "#ff66cc", "hover": "#ff33b5", "category": "Vibrant"},
        "Navy": {"base": "#000080", "hover": "#000066", "category": "Neutral"},
        "Peach": {"base": "#ffdab9", "hover": "#ffc107", "category": "Pastel"}
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @classmethod
    def apply_theme(cls,
                    widget: QWidget,
                    appearance: str,
                    color_theme: str,
                    logger: Optional[Logger] = None) -> None:
        """Apply base theme and button palette to a widget tree."""
        logger = logger or Logger(None)
        appearance = appearance if appearance in cls.BASE_STYLES else Config.DEFAULT_THEME
        try:
            style_config = cls.BASE_STYLES[appearance]
            widget.setStyleSheet(cls._BASE_STYLE_TEMPLATE.format(**style_config))
            button_style = cls._build_button_style(color_theme, appearance, logger)
            for button in widget.findChildren(QPushButton):
                button.setStyleSheet(button_style)
        except Exception as exc:
            logger.log(f"❌ Theme application failed: {exc}")
            widget.setStyleSheet(cls._BASE_STYLE_TEMPLATE.format(**cls.BASE_STYLES[Config.DEFAULT_THEME]))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @classmethod
    def _build_button_style(cls, theme: str, appearance: str, logger: Logger) -> str:
        """Compose button stylesheet from palette and appearance."""
        theme = theme if theme in cls.COLOR_THEMES else Config.DEFAULT_COLOR
        base, hover = cls._resolve_colors(theme, appearance, logger)
        pressed = cls._darken(base, 0.2, logger)
        return cls._BUTTON_STYLE_TEMPLATE.format(base=base, hover=hover, pressed=pressed)

    @classmethod
    def _resolve_colors(cls, theme: str, appearance: str, logger: Logger) -> tuple[str, str]:
        """Return validated (base, hover) hex pair, adjusted for Light mode."""
        config = cls.COLOR_THEMES[theme]
        base, hover = config["base"], config["hover"]
        if appearance == "Light":
            base = cls._darken(base, 0.1, logger)
            hover = cls._darken(hover, 0.15, logger)
        if not (cls._is_hex(base) and cls._is_hex(hover)):
            logger.log(f"⚠️ Invalid colors in theme '{theme}', using default")
            config = cls.COLOR_THEMES[Config.DEFAULT_COLOR]
            base, hover = config["base"], config["hover"]
            if appearance == "Light":
                base = cls._darken(base, 0.1, logger)
                hover = cls._darken(hover, 0.15, logger)
        return base, hover

    @staticmethod
    def _darken(hex_color: str, factor: float, logger: Logger) -> str:
        """Darken a hex color by factor (0–1)."""
        try:
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
            darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
            return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        except Exception as exc:
            logger.log(f"⚠️ Color darken failed: {exc}")
            return hex_color

    @staticmethod
    def _is_hex(color: str) -> bool:
        """Fast hex color validation."""
        return bool(ThemeManager._HEX_COLOR_RE.fullmatch(color))

class OSCompatibilityChecker:
    """Checks OS compatibility and requirements."""
    SUPPORTED_PLATFORMS = {
        "Windows": {
            "min_version": "10",
            "required_libs": ["pyautogui", "keyboard", "requests", "PySide6", "psutil"],
            "system_tray": True,
            "hotkeys": True,
            "pyautogui": True,
            "admin_warning": False
        }
    }

    @classmethod
    def check_compatibility(cls, logger: Logger, require_admin: bool = False) -> Dict[str, Any]:
        """Perform comprehensive OS compatibility check."""
        system = Config.SYSTEM
        release = Config.RELEASE
        result = {
            "system": system,
            "release": release,
            "version": Config.VERSION,
            "machine": Config.MACHINE,
            "compatible": False,
            "warnings": [],
            "errors": [],
            "features": {}
        }
        if system not in cls.SUPPORTED_PLATFORMS:
            result["errors"].append(f"Unsupported OS: {system}")
            return result
        platform_config = cls.SUPPORTED_PLATFORMS[system]
        result["features"] = platform_config
        if not cls._check_version(system, release, platform_config.get("min_version")):
            result["errors"].append(f"OS version too old. Requires {platform_config['min_version']}+")
        missing_libs = cls._check_libraries(platform_config["required_libs"])
        if missing_libs:
            result["errors"].extend([f"Missing library: {lib}" for lib in missing_libs])
        if require_admin and not cls._is_admin_or_elevated():
            result["errors"].append("Administrator privileges required for admin mode")
        if platform_config.get("admin_warning", False) and not cls._is_admin_or_elevated():
            result["warnings"].append("Administrator privileges may be required")
        if platform_config.get("pyautogui", False) and not cls._check_pyautogui_support():
            result["errors"].append("PyAutoGUI not supported on this system")
        if not cls._check_system_resources():
            result["warnings"].append("Low system resources detected")
        result["compatible"] = len(result["errors"]) == 0
        for error in result["errors"]:
            logger.log(f"❌ {error}")
        for warning in result["warnings"]:
            logger.log(f"⚠️ {warning}")
        return result

    @staticmethod
    def _check_version(system: str, release: str, min_version: Optional[str]) -> bool:
        """Check if OS version meets minimum requirements."""
        try:
            if system == "Windows" and hasattr(sys, 'getwindowsversion'):
                win_ver = sys.getwindowsversion()
                return (win_ver.major > 10) or (win_ver.major == 10 and win_ver.minor >= 0)
            return True
        except:
            return True

    @staticmethod
    def _check_libraries(required_libs: List[str]) -> List[str]:
        """Check if required Python libraries are installed."""
        missing = []
        for lib in required_libs:
            try:
                __import__(lib)
            except ImportError:
                missing.append(lib)
        return missing

    @staticmethod
    def _is_admin_or_elevated() -> bool:
        """Check if running with administrator privileges."""
        try:
            if Config.SYSTEM == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            return os.geteuid() == 0
        except:
            return False

    @staticmethod
    def request_admin_privileges() -> bool:
        """Attempt to restart the application with admin privileges."""
        try:
            if Config.SYSTEM == "Windows":
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                    return False
                return True
            else:
                if os.geteuid() != 0:
                    subprocess.run(["sudo", sys.executable] + sys.argv, check=False)
                    return False
                return True
        except Exception as e:
            Logger(None).log(f"Failed to request admin privileges: {e}")
            return False

    @staticmethod
    def _check_pyautogui_support() -> bool:
        """Check PyAutoGUI compatibility."""
        try:
            pyautogui.position()
            return True
        except Exception:
            return False

    @staticmethod
    def _check_system_resources() -> bool:
        """Check minimum system resources."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            return cpu_percent <= 90 and memory.available >= 512 * 1024 * 1024
        except:
            return True

    @classmethod
    def show_compatibility_dialog(cls, check_result: Dict[str, Any], logger: Logger) -> None:
        """Show compatibility dialog to user."""
        if check_result["compatible"]:
            if check_result["warnings"]:
                QMessageBox.warning(
                    None, "Compatibility Notice",
                    f"{check_result['system']} detected with warnings:\n\n" +
                    "\n".join(check_result["warnings"]) +
                    "\n\nApplication will run but some features may be limited."
                )
        else:
            error_msg = "System Compatibility Issues:\n\n" + "\n".join(f"• {error}" for error in check_result["errors"])
            error_msg += "\nPlease update your system or install missing dependencies."
            logger.log(error_msg)
            reply = QMessageBox.critical(None, "Incompatible System", error_msg, QMessageBox.Ok | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                sys.exit(1)

class SingletonLock(QObject):
    """Manages singleton lock for single-instance enforcement."""
    activation_requested = pyqtSignal()

    def __init__(self, lock_port: int = Config.LOCK_PORT, logger: Logger = None):
        super().__init__()
        self.lock_port = lock_port
        self.logger = logger or Logger(None)
        self.socket = None
        self.listener_thread = None
        self.lockfile_path = Config.LOCK_FILE
        self._running = True

    def acquire_lock(self) -> Optional[socket.socket]:
        """Acquire singleton lock with stale cleanup."""
        self._cleanup_stale_locks()
        existing_port = FileManager.read_file(self.lockfile_path)
        if existing_port and self._try_connect_to_existing(int(existing_port)):
            return None
        sock = self._create_lock()
        if sock:
            self.socket = sock
            FileManager.write_file(self.lockfile_path, str(self.lock_port))
            self._start_listener()
        return sock

    def release_lock(self) -> None:
        """Clean release of lock resources."""
        self._running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.lockfile_path.exists():
            try:
                self.lockfile_path.unlink()
            except:
                pass
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1)

    def activate_existing(self) -> bool:
        """Activate existing instance."""
        port = FileManager.read_file(self.lockfile_path)
        if not port:
            return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((Config.PORTS, int(port)))
            sock.send(b"ACTIVATE")
            sock.close()
            return True
        except Exception as e:
            self.logger.log(f"Failed to activate existing instance: {e}")
            return False

    def _cleanup_stale_locks(self) -> None:
        """Remove stale lock files."""
        port = FileManager.read_file(self.lockfile_path)
        if port and not self._is_port_active(int(port)):
            try:
                self.lockfile_path.unlink()
                self.logger.log("Cleaned up stale lock file")
            except:
                pass

    def _is_port_active(self, port: int) -> bool:
        """Check if port has active connection."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            result = sock.connect_ex((Config.PORTS, port))
            sock.close()
            return result == 0
        except:
            return False

    def _try_connect_to_existing(self, port: int) -> bool:
        """Try to connect to existing instance."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((Config.PORTS, port))
            sock.close()
            return True
        except:
            return False

    def _create_lock(self) -> Optional[socket.socket]:
        """Create new lock socket."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((Config.PORTS, self.lock_port))
            sock.listen(5)
            sock.settimeout(0.1)
            return sock
        except OSError as e:
            self.logger.log(f"Failed to bind to port {self.lock_port}: {e}")
            return None

    def _start_listener(self) -> None:
        """Start listener thread for activation requests."""
        def listen():
            while self._running and self.socket:
                try:
                    client_sock, _ = self.socket.accept()
                    try:
                        data = client_sock.recv(1024)
                        if data == b"ACTIVATE":
                            self.activation_requested.emit()
                    finally:
                        client_sock.close()
                except socket.timeout:
                    continue
                except:
                    break
        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()

class VersionManager:
    """Manages application versioning and updates."""

    _LOCAL_VERSION_FILE = Path('VERSION.txt')

    @staticmethod
    def detect_local_version() -> str:
        """Detect version from local files or embedded info."""
        version = FileManager.read_file(VersionManager._LOCAL_VERSION_FILE)
        if version:
            FileManager.write_file(Config.VERSION_FILE, version)
            return version
        return FileManager.read_file(Config.VERSION_FILE, Config.DEFAULT_VERSION)

    @staticmethod
    def get_cached_latest() -> Optional[str]:
        """Get cached latest version if still valid."""
        try:
            if not Config.VERSION_CACHE_FILE.exists():
                return None
            content = Config.VERSION_CACHE_FILE.read_text(encoding='utf-8').strip().split('\n')
            if len(content) < 2:
                return None
            version, timestamp_str = content
            if version == Config.DEFAULT_VERSION:
                return None
            if (time.time() - int(timestamp_str)) / 86400 > 7:
                return None
            return version
        except Exception as e:
            Logger(None).log(f"Error reading version cache: {e}")
            return None

    @staticmethod
    def cache_latest_version(version: str) -> None:
        """Cache latest version with timestamp."""
        FileManager.write_file(Config.VERSION_CACHE_FILE, f"{version}\n{int(time.time())}")

    @staticmethod
    def fetch_latest_release(timeout: float = 10.0) -> Dict[str, Any]:
        """Fetch latest release info from GitHub."""
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return {'version': Config.DEFAULT_VERSION, 'success': False, 'error': 'Invalid timeout value'}
        if not Config.GITHUB_REPO:
            return {'version': Config.DEFAULT_VERSION, 'success': False, 'error': 'Missing GitHub repository configuration'}
        try:
            headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': Config.APP_NAME}
            response = requests.get(
                f"https://api.github.com/repos/{Config.GITHUB_REPO}/releases/latest",
                headers=headers, timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return {'version': Config.DEFAULT_VERSION, 'success': False, 'error': 'Invalid API response format'}
            tag_name = data.get('tag_name', '').lstrip('v')
            if not tag_name:
                return {'version': Config.DEFAULT_VERSION, 'success': False, 'error': 'No valid version found'}
            return {
                'version': tag_name,
                'download_url': data.get('html_url', f"https://github.com/{Config.GITHUB_REPO}/releases/latest"),
                'release_notes': data.get('body', 'No release notes available'),
                'success': True
            }
        except (Timeout, ConnectionError, HTTPError, RequestException) as e:
            return {'version': Config.DEFAULT_VERSION, 'success': False, 'error': str(e)}
        except Exception as e:
            return {'version': Config.DEFAULT_VERSION, 'success': False, 'error': f'Unexpected error: {str(e)}'}

    @staticmethod
    def get_current_version() -> str:
        """Get the current application version."""
        version = VersionManager.detect_local_version()
        if version != Config.DEFAULT_VERSION:
            return version
        cached = VersionManager.get_cached_latest()
        if cached:
            FileManager.write_file(Config.VERSION_FILE, cached)
            return cached
        release_info = VersionManager.fetch_latest_release()
        if release_info.get('success'):
            version = release_info['version']
            VersionManager.cache_latest_version(version)
            FileManager.write_file(Config.VERSION_FILE, version)
            return version
        return Config.DEFAULT_VERSION

    @staticmethod
    def is_newer_version(new: str, current: str) -> bool:
        """Compare semantic versions."""
        def parse_version(v: str) -> tuple:
            parts = [int(p) if p.isdigit() else 0 for p in v.split('.')[:3]]
            return tuple(parts) + (0, 0, 0)[:3-len(parts)]
        try:
            return parse_version(new) > parse_version(current)
        except Exception:
            return new > current

class UpdateChecker(QThread):
    """Thread for checking application updates asynchronously."""
    update_available = pyqtSignal(dict)
    check_completed = pyqtSignal(bool, str)
    version_fetched = pyqtSignal(str)

    def __init__(self, current_version: str, logger: Logger, timeout: float = 10.0):
        super().__init__()
        self._current_version = current_version
        self._logger = logger
        self._timeout = timeout
        self._running = True

    def run(self) -> None:
        """Check for updates and emit signals."""
        if not self._running:
            return
        self._logger.log("🔃 Starting update check...")
        release_info = VersionManager.fetch_latest_release(self._timeout)
        latest_version = release_info.get('version', self._current_version)
        self.version_fetched.emit(latest_version)
        if release_info.get('success'):
            if VersionManager.is_newer_version(latest_version, self._current_version):
                self.update_available.emit(release_info)
                self.check_completed.emit(True, f"Update available: v{latest_version}")
            else:
                self.check_completed.emit(True, f"You're up to date! (v{self._current_version})")
            VersionManager.cache_latest_version(latest_version)
        else:
            self.check_completed.emit(False, "Failed to fetch update information")

    def stop(self) -> None:
        """Safely stop the update checker thread."""
        self._running = False
        self.wait()

class UIManager:
    """Manages the application's user interface."""
    def __init__(self, parent, logger: Logger):
        self.parent = parent
        self.logger = logger
        self.widgets = {}

    def create_header(self) -> QWidget:
        """Create the header with version and update button."""
        layout = QHBoxLayout()
        header_label = QLabel(f"🖱️ {Config.APP_NAME}")
        header_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.widgets['version_display'] = QLabel(f"(v{self.parent.current_version})")
        self.widgets['version_display'].setStyleSheet("font-size: 20px; font-weight: bold;")
        update_btn = QPushButton("🔄 Check Updates")
        update_btn.clicked.connect(self.parent.check_for_updates)
        layout.addWidget(header_label)
        layout.addWidget(self.widgets['version_display'])
        layout.addStretch()
        layout.addWidget(update_btn)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_click_settings(self) -> QGroupBox:
        """Create click settings group box."""
        group = QGroupBox("🖱️ Click Settings")
        form = QFormLayout()
        settings = [
            ('click_count', "Clicks per Cycle", Config.DEFAULT_SETTINGS["click_count"]),
            ('loop_count', "Max Cycles (0=∞)", Config.DEFAULT_SETTINGS["loop_count"]),
            ('click_delay', "Delay Between Clicks (s)", Config.DEFAULT_SETTINGS["click_delay"]),
            ('cycle_delay', "Delay Between Cycles (s)", Config.DEFAULT_SETTINGS["cycle_delay"]),
            ('hotkey_input', "Hotkey", Config.load_hotkey(), "e.g., Ctrl+F, Alt+Shift+G")
        ]
        for key, label, default, *extras in settings:
            widget = QLineEdit(default)
            if extras:
                widget.setPlaceholderText(extras[0])
            self.widgets[key] = widget
            form.addRow(f"{label}:", widget)
        self.widgets['hotkey_apply'] = QPushButton("Apply Hotkey")
        self.widgets['hotkey_apply'].clicked.connect(self.parent.update_hotkey)
        form.addRow("", self.widgets['hotkey_apply'])
        group.setLayout(form)
        return group

    def create_theme_settings(self) -> QGroupBox:
        """Create theme settings group box with admin mode toggle."""
        group = QGroupBox("🎨 Interface")
        form = QFormLayout()
        self.widgets['appearance_combo'] = QComboBox()
        self.widgets['appearance_combo'].addItems(["Dark", "Light"])
        self.widgets['appearance_combo'].currentTextChanged.connect(self.parent.update_theme)
        self.widgets['color_combo'] = QComboBox()
        self.widgets['color_combo'].addItems(list(ThemeManager.COLOR_THEMES.keys()))
        self.widgets['color_combo'].currentTextChanged.connect(self.parent.update_color_theme)
        self.widgets['admin_mode_toggle'] = QPushButton("Enable Admin Mode")
        self.widgets['admin_mode_toggle'].clicked.connect(self.parent.toggle_admin_mode)
        self.widgets['progress_label'] = QLabel("Cycles: 0")
        self.widgets['progress_label'].setAlignment(Qt.AlignRight)
        form.addRow("Appearance Mode:", self.widgets['appearance_combo'])
        form.addRow("Color Theme:", self.widgets['color_combo'])
        form.addRow("Admin Mode:", self.widgets['admin_mode_toggle'])
        form.addRow("Progress:", self.widgets['progress_label'])
        group.setLayout(form)
        return group

    def create_update_tab(self) -> QWidget:
        """Create Updates tab content."""
        widget = QWidget()
        layout = QVBoxLayout()
        version_group = QGroupBox("📋 Version Information")
        v_layout = QVBoxLayout()
        self.widgets['current_version_label'] = QLabel(f"Current: v{self.parent.current_version}")
        self.widgets['latest_version_label'] = QLabel("Latest: Checking...")
        self.widgets['last_check_label'] = QLabel("Last Check: Never")
        v_layout.addWidget(self.widgets['current_version_label'])
        v_layout.addWidget(self.widgets['latest_version_label'])
        v_layout.addWidget(self.widgets['last_check_label'])
        version_group.setLayout(v_layout)
        layout.addWidget(version_group)
        self.widgets['update_text'] = QTextEdit()
        self.widgets['update_text'].setReadOnly(True)
        self.widgets['update_text'].setPlainText(Config.format_update_logs())
        layout.addWidget(self.widgets['update_text'])
        widget.setLayout(layout)
        return widget

    def create_credits_tab(self) -> QWidget:
        """Create Credits tab content."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        header_label = QLabel("📄 Credits")
        header_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(header_label)
        credits_group = QGroupBox("👥 Contributors & Credits")
        credits_layout = QVBoxLayout()
        credits_content = (
            f"Developed by: {Config.AUTHORNAME}\n"
            f"GitHub: https://github.com/{Config.AUTHORNAME}\n\n"
            "Contributors:\n"
            f"- Lead Developer: {Config.AUTHORNAME}\n"
            "- UI/UX Design: MrAndiGamesDev\n"
            "- Special Thanks: Open Source Community\n\n"
            "Libraries Used:\n"
            "- PySide6: GUI Framework\n"
            "- PyAutoGUI: Automation Engine\n"
            "- Requests: HTTP Requests\n"
            "- Keyboard: Hotkey Support\n"
            "- Psutil: System Resources Monitoring\n\n"
            f"Version: {self.parent.current_version}"
        )
        self.widgets['credits_text'] = QTextEdit()
        self.widgets['credits_text'].setReadOnly(True)
        self.widgets['credits_text'].setPlainText(credits_content)
        self.widgets['credits_text'].setFixedHeight(380)
        credits_layout.addWidget(self.widgets['credits_text'])
        credits_group.setLayout(credits_layout)
        layout.addWidget(credits_group)
        github_btn = QPushButton("🌐 Visit GitHub")
        github_btn.setFixedWidth(150)
        github_btn.clicked.connect(lambda: webbrowser.open(f"https://github.com/{Config.GITHUB_REPO}"))
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(github_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def update_version_display(self, current: str, latest: str = None) -> None:
        """Update version display in UI."""
        self.widgets['version_display'].setText(f"v{current}")
        self.widgets['current_version_label'].setText(f"Current: v{current}")
        if latest:
            self.widgets['latest_version_label'].setText(f"Latest: v{latest}")
        self.widgets['last_check_label'].setText(f"Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.parent.tray.update_tooltip()

    def update_admin_mode_button(self, is_admin: bool) -> None:
        """Update the admin mode toggle button text."""
        self.widgets['admin_mode_toggle'].setText("Disable Admin Mode" if is_admin else "Enable Admin Mode")

class SystemTrayManager:
    """Manages system tray functionality."""
    def __init__(self, parent, logger: Logger):
        self.parent = parent
        self.logger = logger
        self.tray_icon = None
        self.setup_tray()

    def setup_tray(self) -> None:
        """Set up system tray icon and menu."""
        try:
            icon_path = FileManager.download_icon()
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path))
            self.update_tooltip()
            self.tray_icon.setContextMenu(self.create_tray_menu())
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
        except Exception as e:
            self.logger.log(f"Tray setup failed: {e}")

    def update_tooltip(self) -> None:
        """Update system tray tooltip."""
        if self.tray_icon:
            mode = "Admin" if self.parent.is_admin_mode else "Normal"
            self.tray_icon.setToolTip(f"{Config.APP_NAME} (v{self.parent.current_version}, {mode} Mode)")

    def create_tray_menu(self) -> QMenu:
        """Create system tray menu."""
        menu = QMenu()
        actions = [
            ("👁️ Show", self.parent.show_normal),
            (f"▶️ Start/Stop ({self.parent.hotkey_manager.current_hotkey})", self.parent.toggle_clicking),
            (f"{'🔓 Disable' if self.parent.is_admin_mode else '🔒 Enable'} Admin Mode", self.parent.toggle_admin_mode),
            ("🔄 Check Updates", self.parent.check_for_updates),
            (None, None),
            ("❌ Quit", self.parent.quit_app)
        ]
        for text, callback in actions:
            if text is None:
                menu.addSeparator()
                continue
            action = QAction(text, self.parent)
            if callback:
                action.triggered.connect(callback)
            menu.addAction(action)
        return menu

    def update_tray_menu(self) -> None:
        """Update tray menu with current hotkey and admin mode."""
        if self.tray_icon:
            self.tray_icon.setContextMenu(self.create_tray_menu())

    def on_tray_activated(self, reason) -> None:
        """Handle tray icon activation."""
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.parent.show_normal()

class ClickerEngine:
    """Manages the auto-clicking functionality."""
    def __init__(self, parent, logger: Logger):
        self.parent = parent
        self.logger = logger
        self.running = False
        self.thread = None
        self.require_admin = Config.SYSTEM == "Windows"  # Require admin on Windows for clicking

    def start(self) -> None:
        """Start the clicker engine."""
        if self.running:
            return
        if self.require_admin and not self.parent.is_admin_mode:
            self.logger.log("❌ Admin mode required for clicking on this system")
            QMessageBox.warning(None, "Admin Mode Required", "Please enable Admin Mode to use the clicker functionality.")
            return
        self.running = True
        self.parent.start_btn.setEnabled(False)
        self.parent.stop_btn.setEnabled(True)
        self.parent.ui.widgets['progress_label'].setText("Cycles: 0")
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()
        self.logger.log("▶️ Started clicking")

    def stop(self) -> None:
        """Stop the clicker engine."""
        self.running = False
        self.parent.start_btn.setEnabled(True)
        self.parent.stop_btn.setEnabled(False)
        self.logger.log("⏹️ Stopped clicking")

    def _click_loop(self) -> None:
        """Main click loop."""
        try:
            settings = self._get_settings()
            cycle_count = 0
            while self.running and (settings['max_loops'] == 0 or cycle_count < settings['max_loops']):
                for _ in range(settings['clicks']):
                    if not self.running:
                        break
                    pyautogui.click()
                    self.logger.log("🖱️ Clicked")
                    time.sleep(settings['click_delay'])
                cycle_count += 1
                self.parent.ui.widgets['progress_label'].setText(f"Cycles: {cycle_count}")
                self.logger.log(f"🔁 Cycle {cycle_count} complete")
                time.sleep(settings['cycle_delay'])
        except Exception as e:
            self.logger.log(f"❌ Clicker error: {e}")
        finally:
            self.stop()

    def _get_settings(self) -> Dict[str, Any]:
        """Get clicker settings from UI."""
        widgets = self.parent.ui.widgets
        def safe_int(widget, default):
            try:
                return int(widget.text() or default)
            except:
                return default
        def safe_float(widget, default):
            try:
                return float(widget.text() or default)
            except:
                return default
        return {
            'clicks': max(1, safe_int(widgets.get('click_count'), Config.DEFAULT_SETTINGS["click_count"])),
            'max_loops': safe_int(widgets.get('loop_count'), Config.DEFAULT_SETTINGS["loop_count"]),
            'click_delay': max(0.01, safe_float(widgets.get('click_delay'), Config.DEFAULT_SETTINGS["click_delay"])),
            'cycle_delay': max(0.01, safe_float(widgets.get('cycle_delay'), Config.DEFAULT_SETTINGS["cycle_delay"]))
        }

class AutoClickerApp(QMainWindow):
    """Main application window."""
    def __init__(self, lock: SingletonLock):
        super().__init__()
        self.lock = lock
        self.logger = Logger(None)
        self.current_version = VersionManager.get_current_version()
        self.hotkey_manager = HotkeyManager(self.logger)
        self.latest_version = self.current_version
        self.update_checker = None
        self.current_appearance = Config.DEFAULT_THEME
        self.current_color_theme = Config.DEFAULT_COLOR
        self.is_admin_mode = Config.load_admin_mode()
        self.ui = UIManager(self, self.logger)
        self.tray = SystemTrayManager(self, self.logger)
        self.clicker = ClickerEngine(self, self.logger)
        self.lock.activation_requested.connect(self.show_normal)
        self._init_ui()
        self._setup_timers()
        self.hotkey_manager.register_hotkey(self.hotkey_manager.current_hotkey, self.toggle_clicking)
        self.ui.widgets['update_text'].setPlainText(Config.format_update_logs())
        self._update_admin_mode_ui()
        self._check_admin_mode_compatibility()
        self.update_theme()

    def _init_ui(self) -> None:
        """Initialize the main UI."""
        self.setWindowTitle(f"{Config.APP_NAME} (v{self.current_version})")
        self.setFixedSize(640, 580)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        layout.addWidget(self.ui.create_header())
        self._setup_tabs(layout)
        self._setup_controls(layout)
        self.ui.update_version_display(self.current_version)
        try:
            icon_path = FileManager.download_icon()
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            self.logger.log(f"Failed to set window icon: {e}")

    def _setup_tabs(self, layout: QVBoxLayout) -> None:
        """Set up tabbed interface."""
        tabs = QTabWidget()
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.addWidget(self.ui.create_click_settings())
        settings_layout.addWidget(self.ui.create_theme_settings())
        settings_layout.addStretch()
        tabs.addTab(settings_tab, "⚙️ Settings")
        tabs.addTab(self.ui.create_update_tab(), "📜 Updates")
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.logger.log_widget = QTextEdit()
        self.logger.log_widget.setReadOnly(True)
        log_layout.addWidget(self.logger.log_widget)
        tabs.addTab(log_tab, "📋 Activity Log")
        tabs.addTab(self.ui.create_credits_tab(), "📄 Credits")
        layout.addWidget(tabs)

    def _setup_controls(self, layout: QVBoxLayout) -> None:
        """Set up control buttons."""
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton(f"▶️ Start ({self.hotkey_manager.current_hotkey})")
        self.stop_btn = QPushButton(f"⏹️ Stop ({self.hotkey_manager.current_hotkey})")
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.toggle_clicking)
        self.stop_btn.clicked.connect(self.clicker.stop)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

    def _setup_timers(self) -> None:
        """Set up update check timer."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_for_updates_silent)
        self.update_timer.start(Config.UPDATE_CHECK_INTERVAL)
        QTimer.singleShot(10000, self.check_for_updates)

    def _check_admin_mode_compatibility(self) -> None:
        """Check compatibility for admin mode."""
        if self.is_admin_mode:
            compat_result = OSCompatibilityChecker.check_compatibility(self.logger, require_admin=True)
            if not compat_result["compatible"]:
                self.logger.log("⚠️ Admin mode not supported, switching to non-admin mode")
                self.is_admin_mode = False
                Config.save_admin_mode(False)
                self._update_admin_mode_ui()
                OSCompatibilityChecker.show_compatibility_dialog(compat_result, self.logger)

    def toggle_admin_mode(self) -> None:
        """Toggle between admin and non-admin modes."""
        if self.is_admin_mode:
            self.is_admin_mode = False
            Config.save_admin_mode(False)
            self.logger.log("🔓 Switched to non-admin mode")
        else:
            if OSCompatibilityChecker.request_admin_privileges():
                self.is_admin_mode = True
                Config.save_admin_mode(True)
                self.logger.log("🔒 Switched to admin mode")
            else:
                self.quit_app()
                return
        self._update_admin_mode_ui()

    def _update_admin_mode_ui(self) -> None:
        """Update UI elements related to admin mode."""
        self.ui.update_admin_mode_button(self.is_admin_mode)
        self.tray.update_tray_menu()
        ThemeManager.apply_theme(self, self.current_appearance, self.current_color_theme)

    def toggle_clicking(self) -> None:
        """Toggle the clicker engine."""
        if self.clicker.running:
            self.clicker.stop()
        else:
            self.clicker.start()

    def update_hotkey(self) -> None:
        """Update the hotkey based on user input."""
        new_hotkey = self.ui.widgets.get('hotkey_input').text().strip()
        if self.hotkey_manager.update_hotkey(new_hotkey, self.toggle_clicking):
            self.start_btn.setText(f"▶️ Start ({self.hotkey_manager.current_hotkey})")
            self.stop_btn.setText(f"⏹️ Stop ({self.hotkey_manager.current_hotkey})")
            self.tray.update_tray_menu()

    def check_for_updates(self, silent: bool = False) -> None:
        """Check for application updates."""
        if self.update_checker and self.update_checker.isRunning():
            self.logger.log("ℹ️ Update check already in progress.")
            return
        if not silent:
            self.logger.log("🔄 Checking for updates...")
        self.update_checker = UpdateChecker(self.current_version, self.logger, timeout=5.0)
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.check_completed.connect(self._on_check_completed)
        self.update_checker.version_fetched.connect(self._on_version_fetched)
        self.update_checker.start()

    def check_for_updates_silent(self) -> None:
        """Silently check for updates."""
        self.check_for_updates(silent=True)

    def update_theme(self, appearance: str = None) -> None:
        """Update the application theme."""
        if appearance is None and 'appearance_combo' in self.ui.widgets:
            appearance = self.ui.widgets['appearance_combo'].currentText()
        self.current_appearance = appearance or Config.DEFAULT_THEME
        ThemeManager.apply_theme(self, self.current_appearance, self.current_color_theme)

    def update_color_theme(self, theme: str = None) -> None:
        """Update the color theme."""
        if theme is None and 'color_combo' in self.ui.widgets:
            theme = self.ui.widgets['color_combo'].currentText()
        self.current_color_theme = theme or Config.DEFAULT_COLOR
        ThemeManager.apply_theme(self, self.current_appearance, self.current_color_theme)

    def _on_version_fetched(self, latest_version: str) -> None:
        """Handle version fetched signal."""
        self.latest_version = latest_version
        self.ui.update_version_display(self.current_version, self.latest_version)
        FileManager.write_file(Config.UPDATE_CHECK_FILE, datetime.now().isoformat())

    def _on_update_available(self, info: dict) -> None:
        """Handle update available signal."""
        reply = QMessageBox.question(
            self, "Update Available",
            f"New version {info['version']} available!\n\n"
            f"Current: v{self.current_version}\nLatest: v{info['version']}\n\n"
            f"Visit GitHub for download?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            webbrowser.open(info['download_url'])
        self.logger.log(f"🆕 Update available: v{info['version']}")

    def _on_check_completed(self, success: bool, message: str) -> None:
        """Handle update check completion."""
        status = "✅" if success else "ℹ️"
        self.logger.log(f"{status} {message}")

    def show_normal(self) -> None:
        """Show and activate the main window."""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        event.ignore()
        self.hide()

    def quit_app(self) -> None:
        """Clean shutdown with lock release."""
        self.logger.log("👋 Shutting down...")
        self.update_timer.stop()
        if self.update_checker and self.update_checker.isRunning():
            self.update_checker.stop()
        self.lock.release_lock()
        if self.tray.tray_icon:
            self.tray.tray_icon.hide()
        keyboard.unhook_all()
        QApplication.quit()

class InstanceDialog(QDialog):
    """Dialog for handling multiple instance detection."""
    def __init__(self, lockfile_path: Path, logger: Logger, parent=None):
        super().__init__(parent)
        self.lockfile_path = lockfile_path
        self.logger = logger
        self.setWindowTitle(f"{Config.APP_NAME} - Instance Detected")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedSize(500, 200)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Assemble the dialog layout and widgets."""
        main_layout = QVBoxLayout()
        main_layout.addLayout(self._create_header())
        main_layout.addWidget(self._create_message())
        main_layout.addLayout(self._create_buttons())
        self.setLayout(main_layout)

    def _create_header(self) -> QHBoxLayout:
        """Create the header row with icon and title."""
        layout = QHBoxLayout()
        icon = QLabel("🖱️")
        icon.setStyleSheet("font-size: 24px; margin: 5px;")
        title = QLabel(f"{Config.APP_NAME} is already running!")
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #d32f2f; margin-left: 10px;"
        )
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addStretch()
        return layout

    def _create_message(self) -> QLabel:
        """Create the informational message label."""
        label = QLabel(
            "An instance of the application is already active.\n\nWhat would you like to do?"
        )
        label.setWordWrap(True)
        label.setStyleSheet(
            "font-size: 12px; color: #333; padding: 15px; "
            "background-color: #f5f5f5; border-radius: 5px; margin: 10px;"
        )
        return label

    def _create_buttons(self) -> QHBoxLayout:
        """Create the action buttons row."""
        layout = QHBoxLayout()
        self.force_btn = QPushButton("⚠️ Force New Instance")
        self.exit_btn = QPushButton("🚪 Exit")
        self.force_btn.setStyleSheet(self._button_style("#ff9800", "#e68900"))
        self.exit_btn.setStyleSheet(self._button_style("#f44336", "#da190b"))
        self.exit_btn.clicked.connect(self.reject)
        self.force_btn.clicked.connect(self._on_force_new)
        layout.addWidget(self.force_btn)
        layout.addWidget(self.exit_btn)
        layout.addStretch()
        return layout

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _button_style(base: str, hover: str) -> str:
        """Return a consistent QPushButton stylesheet."""
        return (
            f"QPushButton {{ background-color: {base}; color: white; border: none; "
            f"padding: 8px 16px; border-radius: 4px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
        )

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------
    def _on_force_new(self) -> None:
        """Prompt for confirmation and close with custom code (2) if approved."""
        choice = QMessageBox.warning(
            self,
            "Warning",
            "Running multiple instances may cause conflicts and instability!\n\n"
            "Would you like to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if choice == QMessageBox.Yes:
            self.done(2)

# try:
#     _PYPRESENCE_AVAILABLE = True
# except ImportError:
#     _PYPRESENCE_AVAILABLE = False
#     Presence = None

# class DiscordRPC:
#     """Cross-platform Discord Rich Presence wrapper using pypresence."""

#     load_dotenv()
#     CLIENT_ID: Final[str] = os.getenv("DISCORD_CLIENT_ID") or ""

#     def __init__(self) -> None:
#         self._rpc: Optional[Presence] = None

#     def connect(self) -> bool:
#         if not _PYPRESENCE_AVAILABLE:
#             _LOGGING.info("Discord RPC skipped: pypresence not installed")
#             return False
#         if not self.CLIENT_ID:
#             _LOGGING.warning("Discord RPC skipped: DISCORD_CLIENT_ID not set")
#             return False
#         try:
#             self._rpc = Presence(self.CLIENT_ID)
#             self._rpc.connect()
#             _LOGGING.info("Discord RPC connected")
#             return True
#         except Exception as e:
#             _LOGGING.warning("Discord RPC connect failed: %s", e)
#             return False

#     def update_presence(self) -> None:
#         if self._rpc is None:
#             return
#         version = FileManager.read_file(Config.VERSION_FILE, Config.DEFAULT_VERSION) or Config.DEFAULT_VERSION
#         try:
#             self._rpc.update(
#                 state="Clicking away!",
#                 details=f"{Config.APP_NAME} (v{version})",
#                 start=int(time.time()),
#                 large_image="app_icon",
#                 large_text=Config.APP_NAME
#             )
#         except Exception as e:
#             _LOGGING.warning("Discord RPC update failed: %s", e)

#     def close(self) -> None:
#         if self._rpc is not None:
#             try:
#                 self._rpc.close()
#             except Exception:
#                 pass
#             self._rpc = None

class ApplicationLauncher:
    """Handles application startup with singleton enforcement."""

    def __init__(self) -> None:
        self.logger = self._ensure_directories_and_log()

    def _ensure_directories_and_log(self) -> Logger:
        FileManager.ensure_app_directory()
        return Logger(None)

    def _check_os_compatibility(self) -> bool:
        compat = OSCompatibilityChecker.check_compatibility(self.logger)
        OSCompatibilityChecker.show_compatibility_dialog(compat, self.logger)
        return compat["compatible"]

    def _build_qapp(self) -> QApplication:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName(Config.APP_NAME)
        app.setOrganizationName(Config.AUTHORNAME)
        return app

    def _set_app_icon(self, app: QApplication) -> None:
        try:
            icon_path = FileManager.download_icon()
            app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            self.logger.log(f"Failed to set app icon: {e}")

    def _handle_singleton_lock(self, lock: "SingletonLock") -> bool:
        acquired = lock.acquire_lock()
        if acquired is not None:
            return True

        dialog = InstanceDialog(lock.lockfile_path, self.logger)
        result = dialog.exec()

        if result == QDialog.Accepted:
            if lock.activate_existing():
                self.logger.log("Activated existing instance")
                sys.exit(0)
            QMessageBox.critical(None, "❌ Error", "Could not activate existing instance.")
            sys.exit(1)

        if result == 2:
            lock.release_lock()
            if lock.lockfile_path.exists():
                lock.lockfile_path.unlink()
            if lock.acquire_lock() is None:
                QMessageBox.critical(None, "❌ Error", "Could not create new instance.")
                sys.exit(1)
            self.logger.log("Forced new instance created")
            return True

        sys.exit(0)

    # def _start_rpc(self) -> None:
    #     try:
    #         discord_rpc = DiscordRPC()
    #         if not discord_rpc.connect():
    #             sys.exit(1)
    #         discord_rpc.update_presence()
    #         self.logger.log("Discord Rich Presence started.")
    #     except Exception as e:
    #         self.logger.log(f"RPC error: {e}")
    #         sys.exit(1)

    def run(self) -> None:
        if not self._check_os_compatibility():
            sys.exit(1)

        app = self._build_qapp()
        self._set_app_icon(app)

        lock = SingletonLock(logger=self.logger)
        if not self._handle_singleton_lock(lock):
            sys.exit(1)

        try:
            # self._start_rpc()
            window = AutoClickerApp(lock)
            window.show()
            sys.exit(app.exec())
        except Exception as e:
            self.logger.log(f"Application error: {e}")
            sys.exit(1)
        finally:
            lock.release_lock()

if __name__ == "__main__":
    Launcher = ApplicationLauncher()
    Launcher.run()