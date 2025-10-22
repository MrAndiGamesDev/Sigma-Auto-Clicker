import platform
from pathlib import Path
from typing import Optional, Dict, Any, List

class Config:
    """Application configuration constants."""
    @classmethod
    def get_settings(cls) -> Dict[str, str]:
        """Return the default settings dictionary."""
        return cls.DEFAULT_SETTINGS.copy()
        
    @classmethod
    def create_app_directories(cls) -> None:
        """Create necessary application directories if they don't exist."""
        cls.APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    APP_NAME = "Sigma Auto Clicker"
    AUTHORNAME = "MrAndiGamesDev"
    ICON_URL = f"https://raw.githubusercontent.com/{AUTHORNAME}/My-App-Icons/main/mousepointer.ico"
    GITHUB_REPO = f"{AUTHORNAME}/Sigma-Auto-Clicker"
    UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000
    DEFAULT_VERSION = "1.0.0"
    LOCK_PORT = 49513
    PORTS = "127.0.0.1"
    DEFAULT_THEME = "Dark"
    DEFAULT_COLOR = "Blue"
    DEFAULT_ADMIN_MODE = False
    DEFAULT_SETTINGS = {
        "click_count": "1",
        "loop_count": "0",
        "click_delay": "1",
        "cycle_delay": "0.5",
    }
    SYSTEM = platform.system()
    RELEASE = platform.release()
    VERSION = platform.version()
    MACHINE = platform.machine()
    HOME_DIR = Path.home()
    APPDATA_DIR = (
        HOME_DIR / "AppData" / "Roaming" / "SigmaAutoClicker"
        if SYSTEM == "Windows" else HOME_DIR / ".sigma_autoclicker"
    )
    HOTKEY = "Ctrl+F"
    HOTKEY_FILE = APPDATA_DIR / "hotkey.txt"
    APP_ICON = APPDATA_DIR / "mousepointer.ico"
    UPDATE_CHECK_FILE = APPDATA_DIR / "last_update_check.txt"
    VERSION_FILE = APPDATA_DIR / "current_version.txt"
    VERSION_CACHE_FILE = APPDATA_DIR / "version_cache.txt"
    LOCK_FILE = APPDATA_DIR / f"app.lock.{LOCK_PORT}"
    ADMIN_MODE_FILE = APPDATA_DIR / "admin_mode.txt"

    UPDATE_LOGS = [
        {
            "date": "2025-10-21",
            "version": "1.1.1",
            "description": (
                "Removed admin mode toggle for enhanced functionality. due to a lack of bugs! "
            ),
        },
        {
            "date": "2025-10-19",
            "version": "1.1.0",
            "description": (
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
        },
        {
            "date": "2025-10-18",
            "version": "1.0.9",
            "description": (
                "Tabs Improvements "
                "Removed Notification during minimized "
                "and so much more!"
            )
        },
        {
            "date": "2025-10-17",
            "version": "1.0.8",
            "description": (
                "Enhanced UI with refined styling and improved responsiveness. "
                "Fixed bugs related to theme switching and button states."
            )
        },
        {
            "date": "2025-10-16",
            "version": "1.0.7",
            "description": (
                "Fixed miscellaneous application bugs for improved stability. "
                "Improved error handling in the update checker."
            )
        },
        {
            "date": "2025-10-16",
            "version": "1.0.6",
            "description": (
                "Resolved issues in the update management system. "
                "Added support for caching version information."
            )
        },
        {
            "date": "2025-10-16",
            "version": "1.0.5",
            "description": (
                "Introduced automatic update checking. "
                "Added version management features and improved UI code structure."
            )
        },
        {
            "date": "2025-10-15",
            "version": "1.0.4",
            "description": (
                "Fixed Light Mode rendering issues. "
                "Improved UI consistency across themes."
            )
        },
        {
            "date": "2025-10-14",
            "version": "1.0.3",
            "description": (
                "Added Update Logs tab for version history. "
                "Introduced customizable color themes."
            )
        },
        {
            "date": "2025-10-13",
            "version": "1.0.0",
            "description": f"Initial release of {APP_NAME}."
        }
    ]

    @staticmethod
    def format_update_logs(separator: str = "\n", logger=None, bullet: str = "•") -> str:
        """Format update logs for display."""
        from logger import Logger
        logger = logger or Logger(None)
        if not Config.UPDATE_LOGS:
            logger.log("⚠️ No update logs available.")
            return "No update logs available."

        formatted_entries = []
        for index, log in enumerate(Config.UPDATE_LOGS):
            try:
                if not all(key in log for key in ["date", "version", "description"]):
                    logger.log(f"⚠️ Invalid update log entry at index {index}: Missing required keys")
                    continue
                description = log["description"].strip()
                bullet_points = [p.strip() for p in description.split(". ") if p.strip()]
                if "and so much more" in description.lower():
                    bullet_points.append("Various additional improvements")
                bullet_list = "\n".join(f"  {bullet} {point}" for point in bullet_points) or f"  {bullet} No details provided."
                entry = f"Version {log['version']} ({log['date']}){separator.rstrip()}\n{bullet_list}"
                formatted_entries.append(entry)
            except Exception as e:
                logger.log(f"⚠️ Error formatting update log entry at index {index}: {e}")
                continue

        if not formatted_entries:
            logger.log("⚠️ No valid update log entries found.")
            return "No valid update logs available."
        footer = "=" * 39
        header = f"🖱️ {Config.APP_NAME} Update History 🖱️\n{footer}\n"
        return f"{header}{separator.join(formatted_entries)}\n{footer}\n"