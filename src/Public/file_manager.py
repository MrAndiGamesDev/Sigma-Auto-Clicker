import os
import urllib.request
from pathlib import Path
from typing import Optional, Union
from src.Public.config import Config

class FileManager:
    """Manages file operations for the application."""
    
    @staticmethod
    def ensure_app_directory() -> None:
        """Ensure application directory exists."""
        os.makedirs(Config.APPDATA_DIR, exist_ok=True)
    
    @staticmethod
    def read_file(file_path: Path, default: str = "") -> str:
        """Read content from a file, return default if file doesn't exist."""
        if not file_path.exists():
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return default
    
    @staticmethod
    def write_file(file_path: Path, content: str) -> bool:
        """Write content to a file."""
        try:
            FileManager.ensure_app_directory()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    def download_icon() -> str:
        """Download application icon if not exists."""
        if Config.APP_ICON.exists():
            return str(Config.APP_ICON)
        
        try:
            FileManager.ensure_app_directory()
            urllib.request.urlretrieve(Config.ICON_URL, Config.APP_ICON)
            return str(Config.APP_ICON)
        except Exception:
            # Return a default system icon path if download fails
            return ""