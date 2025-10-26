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
import contextlib
import logging as _logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Final
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QGraphicsDropShadowEffect,
    QComboBox, QSystemTrayIcon, QMenu, QFormLayout, QMessageBox, QDialog, QProgressBar, QCheckBox
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal as pyqtSignal, QObject

_LOGGING: Final = _logging.getLogger(__name__)

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

    def to_bullets(self, bullet: str = "•", separator: str = "\n") -> str:
        """Return a bullet-point representation of the description."""
        desc = self.description.strip()
        points = [p.strip() for p in desc.split(". ") if p.strip()]
        is_last_word = "and so much more"
        if is_last_word in desc.lower():
            points.append("Various additional improvements")
        if not points:
            points = ["No details provided."]
        return separator.join(f"  {bullet} {p}" for p in points)

class _MetaConfig(type):
    """Metaclass that turns the namespace into read-only class attributes."""
    def __setattr__(cls, name: str, value: Any) -> None:
        raise AttributeError(f"{cls.__name__} is immutable")

class Config(metaclass=_MetaConfig):
    """Immutable application configuration constants."""

    # ------------------------------------------------------------------
    # Application identity
    # ------------------------------------------------------------------
    APP_NAME: Final[str] = "Sigma Auto Clicker"
    AUTHORNAME: Final[str] = "MrAndiGamesDev"
    GITHUB_REPO: Final[str] = f"{AUTHORNAME}/Sigma-Auto-Clicker"
    ICON_URL: Final[str] = (
        f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/dev/src/icons/mousepointer.ico"
    )

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    DEFAULT_VERSION: Final[str] = "1.0.0"
    DEFAULT_THEME: Final[str] = "Light"
    DEFAULT_COLOR: Final[str] = "Purple"
    DEFAULT_SETTINGS: Final[Dict[str, str]] = {
        "click_count": "1",
        "loop_count": "0",
        "click_delay": "1",
        "cycle_delay": "0.5",
    }
    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    UPDATE_CHECK_INTERVAL: Final[int] = 24 * 60 * 60 * 1000  # ms
    LOCK_PORT: Final[int] = random.randint(1024, 49151)
    PORTS: Final[str] = "127.0.0.1"

    # ------------------------------------------------------------------
    # Platform information
    # ------------------------------------------------------------------
    SYSTEM: Final[str] = platform.system()
    RELEASE: Final[str] = platform.release()
    VERSION: Final[str] = platform.version()
    MACHINE: Final[str] = platform.machine()

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    HOME_DIR: Final[Path] = Path.home()
    APPDATA_DIR: Final[Path] = (
        HOME_DIR / "AppData" / "Roaming" / "SigmaAutoClicker"
        if SYSTEM == "Windows"
        else HOME_DIR / "sigma_auto_clicker"
    )

    # ------------------------------------------------------------------
    # File names
    # ------------------------------------------------------------------
    HOTKEY: Final[str] = "Ctrl+F"
    HOTKEY_FILE: Final[Path] = APPDATA_DIR / "hotkey.txt"
    APP_ICON: Final[Path] = APPDATA_DIR / "mousepointer.ico"
    UPDATE_CHECK_FILE: Final[Path] = APPDATA_DIR / "last_update_check.txt"
    VERSION_FILE: Final[Path] = APPDATA_DIR / "current_version.txt"
    VERSION_CACHE_FILE: Final[Path] = APPDATA_DIR / "version_cache.txt"
    LOCK_FILE: Final[Path] = APPDATA_DIR / f"app.lock.{LOCK_PORT}"

    # ------------------------------------------------------------------
    # Update history
    # ------------------------------------------------------------------
    UPDATE_LOGS: Final[List[UpdateLogEntry]] = [
        UpdateLogEntry(
            date="2025-10-26",
            version="1.1.3",
            description=(
                "Removed Discord Rich Presence to trim dependencies and speed up startup. "
                "Fixed Activity-Log UI bug that duplicated timestamps and broke scrolling. "
                "Hardened network-request error handling to surface failures instead of swallowing them. "
                "Rewrote update-checker internals for clearer feedback and higher reliability. "
                "Squeezed idle CPU usage with micro-optimizations. "
                "Added Always On Top Option To Enable/Disable. "
                "Refactored internal threading model to reduce race conditions and improve responsiveness. "
                "Introduced granular logging levels for easier debugging and user feedback. "
                "Improved tray-icon context menu with additional quick-toggle actions. "
                "Enhanced accessibility with better keyboard navigation hints and screen-reader labels. "
                "Streamlined settings persistence to reduce disk writes and extend SSD life. "
                "Added optional start-with-system toggle via registry or launch-agent. "
                "Bundled updated SSL certificates to prevent update-check failures on older systems. "
                "Performed code-wide linting and type-hint coverage for maintainability. "
                "Added a splashscreen when opening an app (Not Animated on an executable file atm). "
                "Added a killswitch (emergency stop). "
                "Removed Admin Mode due to the lack of bugs. "
                "Added Always On Top Switch Toggle. "
            ),
        ),
        UpdateLogEntry(
            date="2025-10-22",
            version="1.1.2-beta.1",
            description="Integrated Discord Rich Presence (Currently broken) removed for now.",
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
            description="Tabs Improvements. Removed Notification during minimized. Various additional improvements.",
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

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    @staticmethod
    def format_update_logs(separator: str = "\n\n", logger: Optional[Logger] = None, bullet: str = "•") -> str:
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

        footer = "=" * 50
        header = f"🖱️ {Config.APP_NAME} Update History 🖱️\n{footer}\n"
        return f"{header}{separator.join(entries)}\n{footer}\n"

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    @staticmethod
    def load_hotkey() -> str:
        """Return the hotkey stored on disk or the default."""
        return (FileManager.read_file(Config.HOTKEY_FILE, Config.HOTKEY) or Config.HOTKEY)

    @staticmethod
    def save_hotkey(hotkey: str) -> None:
        """Persist the given hotkey to disk."""
        return FileManager.write_file(Config.HOTKEY_FILE, hotkey.strip())

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
    def read_file(filepath: Path, default: Optional[str] = None) -> Optional[str]:
        """Read content from file with validation."""
        if not filepath.is_file():
            return default
        try:
            return filepath.read_text(encoding="utf-8").strip() or default
        except Exception as exc:
            _LOGGING.error("Error reading %s: %s", filepath, exc)
            return default

    @staticmethod
    def write_file(filepath: Path, content: str) -> None:
        """Write content to file, repairing permissions if necessary."""
        FileManager.ensure_app_directory()
        try:
            filepath.write_text(content.strip(), encoding="utf-8")
            _LOGGING.debug("Wrote to %s: %s", filepath, content)
        except PermissionError as exc:
            _LOGGING.warning("Permission denied writing %s: %s", filepath, exc)
            FileManager._repair_permissions(filepath)
            # Retry write after permission repair
            filepath.write_text(content.strip(), encoding="utf-8")
            _LOGGING.debug("Repaired permissions and wrote to %s", filepath)
        except Exception as exc:
            _LOGGING.error("Error writing to %s: %s", filepath, exc)

    @staticmethod
    def _repair_permissions(filepath: Path) -> None:
        """Repair permissions for the file and its parent directory."""
        try:
            os.chmod(filepath.parent, 0o700)
            if filepath.exists():
                os.chmod(filepath, 0o600)
            else:
                filepath.touch(mode=0o600, exist_ok=True)
        except Exception as repair_exc:
            _LOGGING.error("Failed to repair permissions for %s: %s", filepath, repair_exc)
            raise

class HotkeyManager:
    """Manages hotkey registration and validation."""

    _VALID_MODIFIERS = {'ctrl', 'alt', 'shift', 'cmd', 'win', 'control', 'command'}

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.current_hotkey = Config.load_hotkey()

    def register_hotkey(self, hotkey: str, callback: callable) -> bool:
        """Register a hotkey with the keyboard library."""
        try:
            self.unhook_hotkey()
            keyboard.add_hotkey(hotkey, callback)
            self.current_hotkey = hotkey
            self.logger.log(f"Hotkey '{hotkey}' registered")
            return True
        except Exception as e:
            self.logger.log(f"Failed to register hotkey '{hotkey}': {e}")
            return False

    def validate_hotkey(self, hotkey: str) -> bool:
        """Validate hotkey format."""
        if not hotkey or '+' not in hotkey:
            return False
        try:
            parts = [k.strip().lower() for k in hotkey.split('+')]
            if len(parts) < 2:
                return False
            *modifiers, main = parts
            valid_main = (
                main.isalnum() or
                main in keyboard.all_modifiers or
                (len(main) == 1 and main.isprintable())
            )
            if not valid_main:
                return False
            return all(m in self._VALID_MODIFIERS for m in modifiers)
        except Exception:
            return False

    def unhook_hotkey(self) -> bool:
        """Unhook all registered hotkeys from the keyboard library."""
        try:
            keyboard.unhook_all()
            self.logger.log("✅ All hotkeys unhooked successfully")
            return True
        except Exception as e:
            self.logger.log(f"❌ Failed to unhook hotkeys: {e}")
            return False

    def update_hotkey(self, new_hotkey: str, callback: Final[callable]) -> bool:
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
            self.unhook_hotkey()
            Config.save_hotkey(new_hotkey)
            success = self.register_hotkey(new_hotkey, callback)
            if success:
                self.logger.log(f"✅ Hotkey updated to '{new_hotkey}'")
            else:
                self.register_hotkey(self.current_hotkey, callback)
            return success
        except Exception as e:
            self.logger.log(f"❌ Failed to set hotkey '{new_hotkey}': {e}")
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
    def apply_theme(
        cls,
        widget: QWidget,
        appearance: str,
        color_theme: str,
        logger: Optional[Logger] = None
    ) -> None:
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

    # ------------------------------------------------------------------
    # System integration
    # ------------------------------------------------------------------
    @classmethod
    def detect_system_theme(cls) -> str:
        """Detect the current system-wide light/dark preference (Windows 10+)."""
        if Config.SYSTEM != "Windows":
            return Config.DEFAULT_THEME
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                detect_system = "Light" if value else "Dark"
                return detect_system
        except Exception:
            return Config.DEFAULT_THEME

class OSCompatibilityChecker:
    """Checks OS compatibility and requirements."""
    SUPPORTED_PLATFORMS: Final[Dict[str, Dict[str, Any]]] = {
        "Windows": {
            "min_version": "11",
            "required_libs": ("pyautogui", "keyboard", "requests", "PySide6", "psutil"),
            "system_tray": True,
            "hotkeys": True,
            "pyautogui": True,
            "admin_warning": False,
        }
    }

    @classmethod
    def check_compatibility(cls, logger: Logger) -> Dict[str, Any]:
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
    def _check_version(system: str, release: Optional[str] = None, min_version: Optional[str] = None) -> List[bool]:
        """Check if OS version meets minimum requirements."""
        try:
            Is_Windows = system == "Windows" and hasattr(sys, 'getwindowsversion')
            if Is_Windows:
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
            cpu_available = cpu_percent <= 90
            memory_available = memory.available >= 512 * 1024 * 1024
            return (cpu_available and memory_available)
        except:
            return True

    @classmethod
    def show_compatibility_dialog(cls, check_result: Dict[str, Any], logger: Logger) -> None:
        """Show compatibility dialog to user."""
        if not check_result.get("compatible", False):
            errors = check_result.get("errors", [])
            error_msg = (
                "System Compatibility Issues:\n\n"
                + "\n".join(f"• {error}" for error in errors)
                + "\nPlease update your system or install missing dependencies."
            )
            logger.log(error_msg)
            reply = QMessageBox.critical(
                None, "Incompatible System", error_msg, QMessageBox.Ok | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                sys.exit(1)
            return

        warnings = check_result.get("warnings", [])
        if warnings:
            QMessageBox.warning(
                None,
                "Compatibility Notice",
                f"{check_result['system']} detected with warnings:\n\n"
                + "\n".join(warnings)
                + "\n\nApplication will run but some features may be limited.",
            )

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

    def _start_listener(self) -> Optional[socket.socket]:
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

@dataclass(slots=True, frozen=True)
class ReleaseInfo:
    version: str
    download_url: str
    release_notes: str
    prerelease: bool
    success: bool
    error: Optional[str] = None

    @staticmethod
    def failure(error: str) -> "ReleaseInfo":
        return ReleaseInfo(
            version=Config.DEFAULT_VERSION,
            download_url="",
            release_notes="",
            prerelease=False,
            success=False,
            error=error,
        )

class VersionManager:
    """Manages application versioning and updates, including pre-release support."""

    _LOCAL_VERSION_FILE: Final = Path("VERSION.txt")
    _CACHE_TTL_DAYS: Final = 7

    @staticmethod
    def _read_version(path: Path, default: str | None = None) -> str | None:
        """Internal helper to read a version file."""
        try:
            content = path.read_text(encoding="utf-8").strip()
            return content if content else default
        except FileNotFoundError:
            return default
        except Exception as e:
            _LOGGING.warning("Failed to read %s: %s", path, e)
            return default

    @staticmethod
    def _write_version(path: Path, version: str) -> None:
        """Internal helper to write a version file."""
        FileManager.write_file(path, version)

    @staticmethod
    def detect_local_version() -> str:
        """Detect version from local files or embedded info."""
        version = VersionManager._read_version(VersionManager._LOCAL_VERSION_FILE)
        if version:
            VersionManager._write_version(Config.VERSION_FILE, version)
            return version
        return VersionManager._read_version(Config.VERSION_FILE, Config.DEFAULT_VERSION) or Config.DEFAULT_VERSION

    @staticmethod
    def get_cached_latest() -> Optional[str]:
        """Get cached latest version if still valid."""
        try:
            if not Config.VERSION_CACHE_FILE.exists():
                return None
            content = Config.VERSION_CACHE_FILE.read_text(encoding="utf-8").strip().splitlines()
            if len(content) < 2:
                return None
            version, timestamp_str = content
            if version == Config.DEFAULT_VERSION:
                return None
            if (time.time() - int(timestamp_str)) / 86400 > VersionManager._CACHE_TTL_DAYS:
                return None
            return version
        except Exception as e:
            _LOGGING.warning("Failed to read version cache: %s", e)
            return None

    @staticmethod
    def cache_latest_version(version: str) -> None:
        """Cache latest version with timestamp."""
        FileManager.write_file(Config.VERSION_CACHE_FILE, f"{version}\n{int(time.time())}")

    @staticmethod
    def fetch_latest_release(timeout: float = 10.0, include_prerelease: bool = False) -> ReleaseInfo:
        """
        Fetch latest release info from GitHub.
        If include_prerelease is True, will consider pre-releases as candidates.
        """
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return ReleaseInfo.failure("Invalid timeout value")
        if not Config.GITHUB_REPO:
            return ReleaseInfo.failure("Missing GitHub repository configuration")

        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": Config.APP_NAME,
            }
            url = f"https://api.github.com/repos/{Config.GITHUB_REPO}/releases"
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            releases = response.json()
            if not isinstance(releases, list) or not releases:
                return ReleaseInfo.failure("No releases found")

            candidates = [
                r
                for r in releases
                if (include_prerelease or not r.get("prerelease", True))
                and r.get("tag_name")
            ]
            if not candidates:
                return ReleaseInfo.failure("No suitable releases found")

            latest = candidates[0]
            tag_name = latest.get("tag_name", "").lstrip("v")
            if not tag_name:
                return ReleaseInfo.failure("No valid version found")

            return ReleaseInfo(
                version=tag_name,
                download_url=latest.get(
                    "html_url",
                    f"https://github.com/{Config.GITHUB_REPO}/releases/latest",
                ),
                release_notes=latest.get("body", "No release notes available"),
                prerelease=latest.get("prerelease", False),
                success=True,
            )
        except (Timeout, ConnectionError, HTTPError, RequestException) as e:
            return ReleaseInfo.failure(str(e))
        except Exception as e:
            return ReleaseInfo.failure(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_current_version() -> str:
        """Get the current application version."""
        version = VersionManager.detect_local_version()
        if version != Config.DEFAULT_VERSION:
            return version
        cached = VersionManager.get_cached_latest()
        if cached:
            VersionManager._write_version(Config.VERSION_FILE, cached)
            return cached
        release_info = VersionManager.fetch_latest_release()
        if release_info.success:
            version = release_info.version
            VersionManager.cache_latest_version(version)
            VersionManager._write_version(Config.VERSION_FILE, version)
            return version
        return Config.DEFAULT_VERSION

    @staticmethod
    def is_newer_version(new: str, current: str) -> bool:
        """Compare semantic versions, including pre-release identifiers."""
        def parse_version(v: str) -> tuple[tuple[int, ...], str]:
            parts = v.split("-", 1)
            numeric_part = parts[0]
            prerelease_part = parts[1] if len(parts) > 1 else ""
            nums = [int(p) if p.isdigit() else 0 for p in numeric_part.split(".")[:3]]
            nums += [0] * (3 - len(nums))
            return (tuple(nums), prerelease_part)

        try:
            new_parsed = parse_version(new)
            current_parsed = parse_version(current)
            return new_parsed > current_parsed
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
        latest_version = getattr(release_info, 'version', self._current_version)
        self.version_fetched.emit(latest_version)
        if release_info and getattr(release_info, 'success', False):
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
    """Centralized UI builder – keeps widget references in one dict."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, parent, logger: Logger) -> None:
        self.parent = parent
        self.logger = logger
        self.widgets: Dict[str, QWidget] = {}

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def update_version_display(self, current: str, latest: str | None = None) -> None:
        """Refresh version labels and tray tooltip."""
        self.widgets["version_display"].setText(f"v{current}")
        self.widgets["current_version_label"].setText(f"Current: v{current}")
        if latest:
            self.widgets["latest_version_label"].setText(f"Latest: v{latest}")
        self.widgets["last_check_label"].setText(
            f"Last Check: {datetime.now():%Y-%m-%d %H:%M:%S}"
        )

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    def _make_line_edit(self, key: str, default: str, placeholder: str = "") -> QLineEdit:
        le = QLineEdit(default)
        if placeholder:
            le.setPlaceholderText(placeholder)
        self.widgets[key] = le
        return le

    def _make_combo(self, key: str, items: List[str], handler) -> QComboBox:
        cb = QComboBox()
        cb.addItems(items)
        cb.currentTextChanged.connect(handler)
        self.widgets[key] = cb
        return cb

    def _make_button(self, text: str, handler) -> QPushButton:
        btn = QPushButton(text)
        btn.clicked.connect(handler)
        return btn

    # ------------------------------------------------------------------
    # Major UI sections
    # ------------------------------------------------------------------
    def create_header(self) -> QWidget:
        """Top bar with title, version and update button."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(f"🖱️ {Config.APP_NAME}")
        title.setStyleSheet("font-size:22px;font-weight:bold;")

        version = QLabel(f"(v{self.parent.current_version})")
        version.setStyleSheet("font-size:20px;font-weight:bold;")
        self.widgets["version_display"] = version

        update_btn = self._make_button("🔄 Check Updates", self.parent.check_for_updates)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addStretch()
        layout.addWidget(update_btn)

        w = QWidget()
        w.setLayout(layout)
        return w

    def create_click_settings(self) -> QGroupBox:
        """Click-parameter inputs."""
        group = QGroupBox("🖱️ Click Settings")
        form = QFormLayout()

        defs = Config.DEFAULT_SETTINGS
        form.addRow("Clicks per Cycle:", self._make_line_edit("click_count", defs["click_count"]))
        form.addRow("Max Cycles (0=∞):", self._make_line_edit("loop_count", defs["loop_count"]))
        form.addRow("Delay Between Clicks (s):", self._make_line_edit("click_delay", defs["click_delay"]))
        form.addRow("Delay Between Cycles (s):", self._make_line_edit("cycle_delay", defs["cycle_delay"]))

        hotkey = self._make_line_edit("hotkey_input", Config.load_hotkey(), "e.g., Ctrl+F, Alt+Shift+G")
        form.addRow("Hotkey:", hotkey)

        apply_btn = self._make_button("Apply Hotkey", self.parent.update_hotkey)
        self.widgets["hotkey_apply"] = apply_btn
        form.addRow("", apply_btn)

        group.setLayout(form)
        return group

    def create_theme_settings(self) -> QGroupBox:
        """Theme & admin-mode controls."""
        group = QGroupBox("🎨 Interface")
        form = QFormLayout()

        # Always-on-top toggle (switch button)
        aot_switch = QCheckBox("Always on Top")
        aot_switch.setChecked(False)
        aot_switch.stateChanged.connect(lambda state: self.parent.toggle_always_on_top())
        self.widgets["always_on_top_toggle"] = aot_switch
        form.addRow(aot_switch)

        # Appearance
        form.addRow(
            "Appearance Mode:",
            self._make_combo("appearance_combo", ["Dark", "Light"], self.parent.update_theme),
        )

        # Color theme
        form.addRow(
            "Color Theme:",
            self._make_combo(
                "color_combo", list(ThemeManager.COLOR_THEMES.keys()), self.parent.update_color_theme
            ),
        )

        # Progress counter
        progress = QLabel("Cycles: 0")
        progress.setAlignment(Qt.AlignRight)
        self.widgets["progress_label"] = progress
        form.addRow("Progress:", progress)

        group.setLayout(form)
        return group

    def create_update_tab(self) -> QWidget:
        """Updates / changelog tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        info_group = QGroupBox("📋 Version Information")
        vbox = QVBoxLayout()
        current_lbl = QLabel(f"Current: v{self.parent.current_version}")
        latest_lbl = QLabel("Latest: Checking...")
        last_lbl = QLabel("Last Check: Never")

        for key, w in zip(
            ("current_version_label", "latest_version_label", "last_check_label"),
            (current_lbl, latest_lbl, last_lbl),
        ):
            self.widgets[key] = w
            vbox.addWidget(w)

        info_group.setLayout(vbox)
        layout.addWidget(info_group)

        changelog = QTextEdit()
        changelog.setReadOnly(True)
        changelog.setPlainText(Config.format_update_logs())
        self.widgets["update_text"] = changelog
        layout.addWidget(changelog)

        widget.setLayout(layout)
        return widget

    def create_credits_tab(self) -> QWidget:
        """Credits / about tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QLabel("📄 Credits")
        header.setStyleSheet("font-size:22px;font-weight:bold;")
        layout.addWidget(header)

        group = QGroupBox("👥 Contributors & Credits")
        vbox = QVBoxLayout()

        text = QTextEdit()
        text.setReadOnly(True)
        text.setFixedHeight(380)
        text.setPlainText(
            f"Developed by: {Config.AUTHORNAME}\n"
            f"GitHub: https://github.com/{Config.AUTHORNAME}\n\n"
            "Contributors:\n"
            f"- Lead Developer: {Config.AUTHORNAME}\n"
            f"- UI/UX Design: {Config.AUTHORNAME}\n"
            "- Special Thanks: Open Source Community\n\n"
            "Libraries Used:\n"
            "- PySide6: GUI Framework\n"
            "- PyAutoGUI: Automation Engine\n"
            "- Requests: HTTP Requests\n"
            "- Keyboard: Hotkey Support\n"
            "- Psutil: System Resources Monitoring\n\n"
        )
        self.widgets["credits_text"] = text
        vbox.addWidget(text)
        group.setLayout(vbox)
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        gh_btn = self._make_button("🌐 Visit GitHub", lambda: webbrowser.open(f"https://github.com/{Config.GITHUB_REPO}"))
        gh_btn.setFixedWidth(150)
        btn_layout.addWidget(gh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

class ClickerEngine:
    """Manages the auto-clicking functionality."""
    def __init__(self, parent, logger: Logger):
        self.parent = parent
        self.logger = logger
        self.running = False
        self.thread = None

    def start(self) -> None:
        """Start the clicker engine."""
        if self.running:
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

class SystemTrayManager:
    """Manages system tray functionality."""

    def __init__(self, parent, logger: Logger) -> None:
        self.parent = parent
        self.logger = logger
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._ensure_tray()

    def refresh_menu(self) -> None:
        """Rebuild the context menu to pick up state changes."""
        if self.tray_icon:
            self.tray_icon.setContextMenu(self._build_menu())

    def update_tray_menu(self) -> None:
        """Alias for refresh_menu to match external calls."""
        self.refresh_menu()

    def _ensure_tray(self) -> None:
        """Create and show the tray icon; fail gracefully."""
        try:
            icon_path = FileManager.download_icon()
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path))
            self.tray_icon.setContextMenu(self._build_menu())
            self.tray_icon.activated.connect(self._on_activated)
            self.tray_icon.show()
        except Exception as exc:
            self.logger.log(f"Tray setup failed: {exc}")

    def _build_menu(self) -> QMenu:
        """Construct the context menu dynamically."""
        menu = QMenu()

        def add(text: str, callback: Final[callable]) -> QAction:
            action = QAction(text, self.parent)
            action.triggered.connect(callback)
            menu.addAction(action)
            return action

        add("👁️ Show", self.parent.show_normal)
        add(f"▶️ Start/Stop ({self.parent.hotkey_manager.current_hotkey})", self.parent.toggle_clicking)
        add("🔄 Check Updates", self.parent.check_for_updates)
        menu.addSeparator()
        add("🚫 Kill Application (Emergency If Crashes)", self.parent.kill_application)  # Added kill switch option
        add("❌ Quit", self.parent.quit_app)
        return menu

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle left-click / double-click on the tray icon."""
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.parent.show_normal()

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
        self.ui = UIManager(self, self.logger)
        self.tray = SystemTrayManager(self, self.logger)
        self.clicker = ClickerEngine(self, self.logger)
        self.lock.activation_requested.connect(self.show_normal)
        self._init_ui()
        self._setup_timers()
        self.hotkey_manager.register_hotkey(self.hotkey_manager.current_hotkey, self.toggle_clicking)
        self.ui.widgets['update_text'].setPlainText(Config.format_update_logs())
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

    def toggle_clicking(self) -> None:
        """Toggle the clicker engine."""
        if self.clicker.running:
            self.clicker.stop()
        else:
            self.clicker.start()

    def toggle_always_on_top(self) -> None:
        """Toggle the window always-on-top flag and update UI text."""
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.logger.log("🔓 Disabled always-on-top")
        else:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.logger.log("🔒 Enabled always-on-top")
        self.show()

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

    def _on_update_available(self, info: dict, separator: str = "\n", otherseparator: str = "\n\n") -> None:
        """Handle update available signal."""
        reply = QMessageBox.question(
            self, "Update Available",
            f"New version {info['version']} available!{otherseparator}"
            f"Current: v{self.current_version}{separator}Latest: v{info['version']}{otherseparator}"
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

    def kill_application(self) -> None:
        """Immediately terminate the application with full cleanup."""
        self.logger.log("🚫 Kill switch activated: Terminating application...")
        # Stop the clicker engine
        if self.clicker.running:
            self.clicker.stop()
        # Stop the update checker
        if self.update_checker and self.update_checker.isRunning():
            self.update_checker.stop()
        # Stop the update timer
        self.update_timer.stop()
        # Release the singleton lock
        self.lock.release_lock()
        # Unhook all keyboard hotkeys
        try:
            keyboard.unhook_all()
        except Exception as e:
            self.logger.log(f"Failed to unhook hotkeys: {e}")
        # Hide and clean up the system tray
        if self.tray.tray_icon:
            try:
                self.tray.tray_icon.hide()
                self.tray.tray_icon.deleteLater()
            except Exception as e:
                self.logger.log(f"Failed to clean up system tray: {e}")
        try:
            # Quit the application
            QApplication.quit()
            # Ensure the process terminates
            sys.exit(0)
        except Exception as e:
            self.logger.log(f"Failed to quit application: {e}")

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
    """Premium-styled dialog for handling multiple instance detection."""

    _DIALOG_CSS = """
        QWidget#dialogFrame{
            background-color:#1e1e2e;
            border-radius:16px;
            border:1px solid #333;
        }
    """

    _TITLE_CSS = """
        font-size:18px;
        font-weight:600;
        color:#ffffff;
        letter-spacing:0.5px;
    """

    _CLOSE_BTN_CSS = """
        QPushButton{
            background-color:#2e2e3e;
            color:#aaa;
            border:none;
            border-radius:14px;
            font-weight:bold;
            font-size:14px;
        }
        QPushButton:hover{background-color:#ff4757; color:#fff;}
    """

    _MSG_CSS = """
        font-size:14px;
        color:#c9c9d9;
        line-height:22px;
        padding:16px;
        background-color:rgba(255,255,255,5);
        border-radius:8px;
    """

    _BTN_CSS_TPL = """
        QPushButton{{
            background-color:{accent};
            color:#ffffff;
            border:none;
            border-radius:8px;
            font-weight:600;
            font-size:14px;
            padding:0 20px;
        }}
        QPushButton:hover{{background-color:{hover};}}
    """

    def __init__(self, lockfile_path: Path, logger: Logger, parent=None):
        super().__init__(parent)
        self.lockfile_path = lockfile_path
        self.logger = logger
        self.setWindowTitle(f"{Config.APP_NAME} – Instance Detected")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(480, 240)
        self._build_ui()
        self._apply_shadow()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Assemble the premium dialog layout and widgets."""
        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)

        frame = QWidget()
        frame.setObjectName("dialogFrame")
        frame.setStyleSheet(self._DIALOG_CSS)

        lay = QVBoxLayout(frame)
        lay.setSpacing(12)
        lay.setContentsMargins(24, 24, 24, 24)

        lay.addLayout(self._create_header())
        lay.addWidget(self._create_message())
        lay.addLayout(self._create_buttons())

        main.addWidget(frame)
        self.setLayout(main)

    def _create_header(self) -> QHBoxLayout:
        """Create the sleek header with icon and title."""
        lay = QHBoxLayout()

        icon = QLabel("🖱️")
        icon.setStyleSheet("font-size:28px; padding:0px;")

        title = QLabel("Already Running")
        title.setStyleSheet(self._TITLE_CSS)

        close = QPushButton("✕")
        close.setFixedSize(28, 28)
        close.setStyleSheet(self._CLOSE_BTN_CSS)
        close.clicked.connect(self.reject)

        lay.addWidget(icon)
        lay.addWidget(title, 1)
        lay.addWidget(close)
        return lay

    def _create_message(self) -> QLabel:
        """Create the refined message label."""
        lbl = QLabel(
            "An instance of Sigma Auto Clicker is currently active.<br><br>"
            "How would you like to proceed?"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet(self._MSG_CSS)
        return lbl

    def _create_buttons(self) -> QHBoxLayout:
        """Create premium action buttons."""
        lay = QHBoxLayout()
        lay.setSpacing(12)

        self.force_btn = QPushButton("Force New Instance")
        self.exit_btn = QPushButton("Exit")

        for btn, accent, hover in (
            (self.force_btn, "#ff9800", "#e68900"),
            (self.exit_btn, "#f44336", "#da190b"),
        ):
            btn.setFixedHeight(42)
            btn.setStyleSheet(self._BTN_CSS_TPL.format(accent=accent, hover=hover))

        self.exit_btn.clicked.connect(self.reject)
        self.force_btn.clicked.connect(self._on_force_new)

        lay.addWidget(self.force_btn)
        lay.addWidget(self.exit_btn)
        return lay

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _apply_shadow(self) -> None:
        """Add drop shadow for depth."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor("#00000080")
        self.setGraphicsEffect(shadow)

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------
    def _on_force_new(self) -> None:
        """Prompt for confirmation and close with code 2 if approved."""
        choice = QMessageBox.warning(
            self,
            "Confirmation",
            "Running multiple instances may cause conflicts and instability.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if choice == QMessageBox.Yes:
            self.done(2)
            
class SplashScreen(QWidget):
    """Frameless splash window with progress bar and version label."""

    _STYLE = """
        background-color: #2b2b2b;
    """
    _TITLE_STYLE = """
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    """
    _SUBTITLE_STYLE = """
        color: #aaaaaa;
        font-size: 12px;
    """
    _VERSION_STYLE = """
        color: #666666;
        font-size: 21px;
    """
    _PROGRESS_STYLE = """
        QProgressBar {
            background-color: #3c3c3c;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #00aaff;
            border-radius: 5px;
        }
    """

    def __init__(self, timeout: int = 3000, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._dots = 0
        self._base_text = "Loading"
        self._subtitle_timer: Optional[QTimer] = None
        self._build_ui()
        QTimer.singleShot(timeout, self.close)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle(Config.APP_NAME)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(400, 250)
        self.setStyleSheet(self._STYLE)
        self._center_on_screen()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self._create_title(), alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self._create_subtitle(), alignment=Qt.AlignCenter)
        layout.addSpacing(30)
        layout.addWidget(self._create_progress(), alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self._create_version(), alignment=Qt.AlignCenter)

    # ------------------------------------------------------------------
    # Widget factories
    # ------------------------------------------------------------------
    def _create_title(self) -> QLabel:
        lbl = QLabel(Config.APP_NAME)
        lbl.setStyleSheet(self._TITLE_STYLE)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def _create_subtitle(self) -> QLabel:
        lbl = QLabel(self._base_text)
        lbl.setStyleSheet(self._SUBTITLE_STYLE)
        lbl.setAlignment(Qt.AlignCenter)

        def animate() -> None:
            self._dots = (self._dots + 1) % 4
            lbl.setText(self._base_text + "." * self._dots + " " * (3 - self._dots))

        self._subtitle_timer = QTimer(lbl)
        self._subtitle_timer.timeout.connect(animate)
        self._subtitle_timer.start(350)

        return lbl

    def _create_progress(self) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, 0)  # indeterminate
        bar.setFixedWidth(300)
        bar.setStyleSheet(self._PROGRESS_STYLE)
        return bar

    def _create_version(self) -> QLabel:
        version = FileManager.read_file(Config.VERSION_FILE, Config.DEFAULT_VERSION)
        lbl = QLabel(f"v{version}")
        lbl.setStyleSheet(self._VERSION_STYLE)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _center_on_screen(self) -> None:
        screen_geo = QApplication.primaryScreen().geometry()
        self.move(screen_geo.center() - self.rect().center())

class ApplicationLauncher:
    """Orchestrates application startup with singleton enforcement."""

    def __init__(self) -> None:
        self.logger = self._setup_logger()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _setup_logger() -> Logger:
        FileManager.ensure_app_directory()
        return Logger(None)

    # ------------------------------------------------------------------
    # Compatibility & environment
    # ------------------------------------------------------------------
    @staticmethod
    def _check_os_compatibility(logger: Logger) -> bool:
        compat = OSCompatibilityChecker.check_compatibility(logger)
        OSCompatibilityChecker.show_compatibility_dialog(compat, logger)
        return compat["compatible"]

    @staticmethod
    def _build_qapplication() -> QApplication:
        # Destroy any existing QApplication instance cleanly
        if (existing := QApplication.instance()) is not None:
            existing.quit()
            existing.deleteLater()
            QApplication.processEvents()
            time.sleep(0.1)  # brief grace period

        # Disable high-DPI scaling to avoid Windows permission warnings
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName(Config.APP_NAME)
        app.setOrganizationName(Config.AUTHORNAME)
        return app

    @staticmethod
    def _set_app_icon(app: QApplication, logger: Logger) -> None:
        try:
            app.setWindowIcon(QIcon(FileManager.download_icon()))
        except Exception as exc:
            logger.log(f"Failed to set app icon: {exc}")

    # ------------------------------------------------------------------
    # Singleton & lifecycle
    # ------------------------------------------------------------------
    @staticmethod
    def _handle_singleton_lock(logger: Logger) -> SingletonLock:
        lock = SingletonLock(logger=logger)
        acquired = lock.acquire_lock()
        if acquired is not None:
            return lock

        # Lock not acquired → show dialog
        dialog = InstanceDialog(lock.lockfile_path, logger)
        result = dialog.exec()

        if result == QDialog.Accepted:
            if lock.activate_existing():
                logger.log("Activated existing instance")
                sys.exit(0)
            QMessageBox.critical(None, "❌ Error", "Could not activate existing instance.")
            sys.exit(1)

        if result == 2:  # Force new instance
            lock.release_lock()
            with contextlib.suppress(Exception):
                lock.lockfile_path.unlink()

            acquired = lock.acquire_lock()
            if acquired is None:
                QMessageBox.critical(None, "❌ Error", "Could not create new instance.")
                sys.exit(1)
            logger.log("Forced new instance created")
            return lock
        sys.exit(0)

    @staticmethod
    def _run_main_app(app: QApplication, lock: SingletonLock, logger: Logger) -> None:
        splash = SplashScreen()
        splash.show()
        app.processEvents()  # ensure splash paints immediately

        try:
            main_window = AutoClickerApp(lock)
        except Exception as exc:
            logger.log(f"Application error during initialization: {exc}")
            splash.close()
            lock.release_lock()
            sys.exit(1)

        # Close splash after 3 seconds and show main window
        QTimer.singleShot(3000, lambda: (splash.close(), main_window.show()))

        try:
            sys.exit(app.exec())
        except Exception as exc:
            logger.log(f"Application runtime error: {exc}")
            sys.exit(1)
        finally:
            lock.release_lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        if not self._check_os_compatibility(self.logger):
            sys.exit(1)

        app = self._build_qapplication()
        self._set_app_icon(app, self.logger)

        lock = self._handle_singleton_lock(self.logger)
        self._run_main_app(app, lock, self.logger)

class AppLauncher:
    """Thin wrapper to start the application."""

    def __init__(self) -> None:
        self._app = ApplicationLauncher()
        self._log = _LOGGING

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        self._log.info("Application started")
        try:
            self._app.run()
        except Exception as exc:
            self._log.error(f"Application error: {exc}")
            sys.exit(1)
