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
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QFileDialog,
    QComboBox, QSystemTrayIcon, QMenu, QFormLayout, QMessageBox
)
from PySide6.QtGui import QIcon, QAction, QColor
from PySide6.QtCore import Qt, QTimer, QThread, Signal as pyqtSignal, QObject

# PyAutoGUI settings
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

class Config:
    """Application configuration constants"""
    APP_NAME = "Sigma Auto Clicker"
    HOTKEY = "Ctrl+F"
    AUTHORNAME = "MrAndiGamesDev"
    ICON_URL = f"https://raw.githubusercontent.com/{AUTHORNAME}/My-App-Icons/main/mousepointer.ico"
    GITHUB_REPO = f"{AUTHORNAME}/Sigma-Auto-Clicker"
    UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000
    DEFAULT_VERSION = "1.0.0"

    PORTS = "127.0.0.1"

    SYSTEM = platform.system()
    HOME_DIR = Path.home()

    APPDATA_DIR = (
        HOME_DIR / "AppData" / "Roaming" / "SigmaAutoClicker" 
        if SYSTEM == "Windows" else HOME_DIR / ".sigma_autoclicker"
    )
    
    # File paths
    APP_ICON = APPDATA_DIR / "mousepointer.ico"
    UPDATE_CHECK_FILE = APPDATA_DIR / "last_update_check.txt"
    VERSION_FILE = APPDATA_DIR / "current_version.txt"
    VERSION_CACHE_FILE = APPDATA_DIR / "version_cache.txt"
    
    UPDATE_LOGS = [
        "2025-10-18: UI Improvements and Bug Fixes and much more!",
        "2025-10-16: Fixed app bugs! and much more (part 3)",
        "2025-10-16: Fixed An Update Management Bug and much more! (part 2)",
        "2025-10-16: Added automatic update checking Version management UI/Code improvements UI Improvements And Much More!",
        "2025-10-15: Fixed Light Mode support and UI improvements",
        "2025-10-14: Added Update Logs tab and color themes",
        "2025-10-13: Initial release"
    ]

class OSCompatibilityChecker:
    """Comprehensive OS compatibility and requirements checker"""
    
    SUPPORTED_PLATFORMS = {
        "Windows": {
            "min_version": "10.0",
            "required_libs": ["pyautogui", "keyboard", "requests", "PySide6", "psutil"],
            "system_tray": True,
            "hotkeys": True,
            "pyautogui": True,
            "admin_warning": False
        },
        "Darwin": {  # macOS
            "min_version": "10.15",
            "required_libs": ["pyautogui", "keyboard", "requests", "PySide6", "psutil"],
            "system_tray": True,
            "hotkeys": True,
            "pyautogui": True,
            "admin_warning": True,  # macOS requires accessibility permissions
            "accessibility_needed": True
        },
        "Linux": {
            "min_version": "5.4",
            "required_libs": ["pyautogui", "keyboard", "requests", "PySide6", "psutil"],
            "system_tray": True,  # Depends on desktop environment
            "hotkeys": True,
            "pyautogui": True,
            "admin_warning": False,
            "x11_warning": True  # May need X11 forwarding or Wayland compatibility
        }
    }
    
    @classmethod
    def check_compatibility(cls) -> Dict[str, Any]:
        """Perform comprehensive OS compatibility check"""
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        
        result = {
            "system": system,
            "release": release,
            "version": version,
            "machine": machine,
            "compatible": False,
            "warnings": [],
            "errors": [],
            "features": {}
        }
        
        # Check if platform is supported
        if system not in cls.SUPPORTED_PLATFORMS:
            result["errors"].append(f"Unsupported OS: {system}")
            return result
        
        platform_config = cls.SUPPORTED_PLATFORMS[system]
        result["features"] = platform_config
        
        # Version check
        if not cls._check_version(system, release, platform_config.get("min_version")):
            result["errors"].append(f"OS version too old. Requires {platform_config['min_version']}+")
        
        # Library checks
        missing_libs = cls._check_libraries(platform_config["required_libs"])
        if missing_libs:
            result["errors"].extend([f"Missing library: {lib}" for lib in missing_libs])
        
        # Admin/permissions check
        if platform_config.get("admin_warning", False):
            if not cls._is_admin_or_elevated():
                result["warnings"].append("Administrator privileges may be required for full functionality")
        
        # macOS accessibility
        if system == "Darwin" and platform_config.get("accessibility_needed", False):
            if not cls._check_macos_accessibility():
                result["warnings"].append("System Preferences > Security & Privacy > Accessibility permissions required")
        
        # Linux X11/Wayland check
        if system == "Linux":
            if not cls._check_linux_display():
                result["warnings"].append("X11 display server required for GUI automation")
        
        # PyAutoGUI specific checks
        if platform_config.get("pyautogui", False):
            if not cls._check_pyautogui_support():
                result["errors"].append("PyAutoGUI not supported on this system configuration")
        
        # System resources check
        if not cls._check_system_resources():
            result["warnings"].append("Low system resources detected - performance may be affected")
        
        result["compatible"] = len(result["errors"]) == 0
        return result
    
    @staticmethod
    def _check_version(system: str, release: str, min_version: str) -> bool:
        """Check if OS version meets minimum requirements"""
        try:
            if system == "Windows":
                # Windows version check using win32api or platform
                import sys
                if hasattr(sys, 'getwindowsversion'):
                    win_ver = sys.getwindowsversion()
                    major = win_ver.major
                    minor = win_ver.minor
                    return (major > 10) or (major == 10 and minor >= 0)
                return True  # Fallback
            elif system == "Darwin":
                # macOS version check
                import plistlib
                try:
                    with open('/System/Library/CoreServices/SystemVersion.plist', 'rb') as f:
                        info = plistlib.load(f)
                        major = int(info['ProductVersion'].split('.')[0])
                        minor = int(info['ProductVersion'].split('.')[1])
                        return (major > 10) or (major == 10 and minor >= 15)
                except:
                    return True  # Fallback
            else:  # Linux
                # Kernel version check
                kernel_parts = release.split('.')
                if len(kernel_parts) >= 2:
                    major = int(kernel_parts[0])
                    minor = int(kernel_parts[1])
                    return (major > 5) or (major == 5 and minor >= 4)
                return True
        except:
            return True  # Fallback to allow running
    
    @staticmethod
    def _check_libraries(required_libs: list) -> list:
        """Check if required Python libraries are installed"""
        missing = []
        for lib in required_libs:
            try:
                if lib == "psutil":
                    import psutil
                elif lib == "PySide6":
                    import PySide6
                else:
                    __import__(lib)
            except ImportError:
                missing.append(lib)
        return missing
    
    @staticmethod
    def _is_admin_or_elevated() -> bool:
        """Check if running with administrator privileges"""
        try:
            if platform.system() == "Windows":
                try:
                    import ctypes
                    return ctypes.windll.shell32.IsUserAnAdmin()
                except:
                    pass
            elif platform.system() == "Darwin":
                # macOS check
                return os.geteuid() == 0
            else:  # Linux
                return os.geteuid() == 0
        except:
            return False
    
    @staticmethod
    def _check_macos_accessibility() -> bool:
        """Check macOS accessibility permissions"""
        try:
            # This is a simplified check - actual verification requires AppleScript or checking permissions database
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to get name of every process'],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def _check_linux_display() -> bool:
        """Check if Linux has display server available"""
        try:
            display = os.environ.get('DISPLAY')
            wayland = os.environ.get('WAYLAND_DISPLAY')
            return bool(display or wayland)
        except:
            return False
    
    @staticmethod
    def _check_pyautogui_support() -> bool:
        """Check PyAutoGUI compatibility"""
        try:
            # Test basic PyAutoGUI functionality
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0
            # Just check if it can be imported and basic position works
            pos = pyautogui.position()
            return True
        except Exception:
            return False
    
    @staticmethod
    def _check_system_resources() -> bool:
        """Check minimum system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Basic resource checks
            if cpu_percent > 90:
                return False
            if memory.available < 512 * 1024 * 1024:  # Less than 512MB free
                return False
            
            return True
        except:
            return True  # Assume OK if can't check
    
    @classmethod
    def show_compatibility_dialog(cls, check_result: Dict[str, Any]):
        """Show compatibility dialog to user"""
        if check_result["compatible"]:
            if check_result["warnings"]:
                QMessageBox.warning(
                    None, "Compatibility Notice",
                    f"{check_result['system']} detected with warnings:\n\n" +
                    "\n".join(check_result["warnings"]) +
                    "\n\nApplication will run but some features may be limited."
                )
        else:
            error_msg = "System Compatibility Issues:\n\n"
            for error in check_result["errors"]:
                error_msg += f"• {error}\n"
            error_msg += "\nPlease update your system or install missing dependencies."
            
            reply = QMessageBox.critical(
                None, "Incompatible System", error_msg,
                QMessageBox.Ok | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                sys.exit(1)

class SingletonLock(QObject):
    """Manages singleton application lock using TCP socket on localhost"""
    activation_requested = pyqtSignal()
    
    def __init__(self, lock_port: int = 49513):
        super().__init__()
        self.lock_port = lock_port
        self.socket = None
        self.listener_thread = None
        self.lockfile_path = Config.APPDATA_DIR / f"app.lock.{lock_port}"
        self._running = True
    
    @contextmanager
    def acquire(self):
        """Context manager to acquire and release lock"""
        sock = self._try_acquire()
        if sock is None:
            yield None  # Another instance running
            return
        try:
            self.socket = sock
            self._write_port_file()
            self._start_listener()
            yield sock  # Lock acquired successfully
        finally:
            self._release()
    
    def _try_acquire(self) -> Optional[socket.socket]:
        """Attempt to acquire lock or detect existing instance"""
        # First check if lockfile exists with a port
        port = self._read_port_file()
        if port:
            if self._try_connect_to_existing(port):
                return None  # Existing instance found
        # Try to bind to port directly (will fail if another instance is using it)
        return self._create_lock()
    
    def _try_connect_to_existing(self, port: int) -> bool:
        """Try to connect to existing instance on given port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect((Config.PORTS, port))
            sock.close()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False
    
    def _create_lock(self) -> Optional[socket.socket]:
        """Create new lock socket on localhost"""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((Config.PORTS, self.lock_port))
            sock.listen(5)
            return sock
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {self.lock_port} already in use, another instance may be running")
            else:
                print(f"Failed to create lock socket: {e}")
            if sock:
                sock.close()
            return None
    
    def _write_port_file(self):
        """Write the port number to lockfile"""
        try:
            FileManager.ensure_app_directory()
            self.lockfile_path.write_text(str(self.lock_port))
            # Hide on Windows
            if Config.SYSTEM == "Windows":
                try:
                    subprocess.run(
                        ["attrib", "+H", str(self.lockfile_path)], 
                        capture_output=True,
                        check=True
                    )
                except subprocess.CalledProcessError:
                    pass
        except Exception as e:
            print(f"Failed to write port file: {e}")
    
    def _read_port_file(self) -> Optional[int]:
        """Read port number from lockfile"""
        try:
            if self.lockfile_path.exists():
                port_str = self.lockfile_path.read_text().strip()
                port = int(port_str)
                return port
        except (ValueError, OSError):
            # Cleanup invalid lockfile
            try:
                self.lockfile_path.unlink()
            except:
                pass
        return None
    
    def _start_listener(self):
        """Start background thread to listen for activation requests"""
        def listen():
            try:
                while self.socket and self._running:
                    try:
                        client_sock, _ = self.socket.accept()
                        try:
                            data = client_sock.recv(1024)
                            if data == b"ACTIVATE":
                                self.activation_requested.emit() # Emit signal to main thread
                        finally:
                            client_sock.close()
                    except socket.timeout:
                        continue
                    except Exception:
                        break  # Socket likely closed
            except Exception as e:
                print(f"Listener error: {e}")
        
        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()
    
    def _release(self):
        """Release lock resources"""
        self._running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        try:
            self.lockfile_path.unlink(missing_ok=True)
        except:
            pass

class FileManager:
    """Handles file operations and persistence"""
    @staticmethod
    def ensure_app_directory():
        Config.APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        if Config.SYSTEM == "Windows":
            try:
                subprocess.run(
                    ["attrib", "+H", str(Config.APPDATA_DIR)], 
                    capture_output=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                pass
    
    @staticmethod
    def download_icon() -> str:
        FileManager.ensure_app_directory()
        if not Config.APP_ICON.exists():
            try:
                urllib.request.urlretrieve(Config.ICON_URL, Config.APP_ICON)
                if Config.SYSTEM == "Windows":
                    subprocess.run(
                        ["attrib","+H",str(Config.APP_ICON)], 
                        capture_output=True,
                        check=True
                    )
            except Exception as e:
                print(f"Failed to download icon: {e}")
                Config.APP_ICON.touch()
        return str(Config.APP_ICON)
    
    @staticmethod
    def read_version_file(filepath: Path) -> Optional[str]:
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    return version if version and version != Config.DEFAULT_VERSION else None
        except Exception as e:
            print(f"Error reading version file {filepath}: {e}")
        return None
    
    @staticmethod
    def write_version_file(filepath: Path, version: str):
        try:
            FileManager.ensure_app_directory()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(version)
        except Exception as e:
            print(f"Error writing version file {filepath}: {e}")
    
    @staticmethod
    def update_last_check():
        try:
            Config.UPDATE_CHECK_FILE.write_text(datetime.now().isoformat())
        except Exception:
            pass

class VersionManager:
    """Manages application versioning and updates"""
    @staticmethod
    def load_local_version() -> Optional[str]:
        local_file = Path('VERSION.txt')
        version = FileManager.read_version_file(local_file)
        if version:
            FileManager.write_version_file(Config.VERSION_FILE, version)
            return version
        return FileManager.read_version_file(Config.VERSION_FILE)
    
    @staticmethod
    def get_cached_latest() -> Optional[str]:
        try:
            if Config.VERSION_CACHE_FILE.exists():
                content = Config.VERSION_CACHE_FILE.read_text(encoding='utf-8').strip().split('\n')
                if len(content) >= 2:
                    version, timestamp_str = content[0].strip(), content[1]
                    timestamp = int(timestamp_str)
                    if (version != "unknown" and 
                        (time.time() - timestamp) / 86400 <= 7):
                        return version
        except Exception:
            pass
        return None
    
    @staticmethod
    def cache_latest_version(version: str):
        try:
            timestamp = int(time.time())
            Config.VERSION_CACHE_FILE.write_text(f"{version}\n{timestamp}", encoding='utf-8')
        except Exception:
            pass
    
    @staticmethod
    def fetch_latest_release() -> Dict[str, Any]:
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': Config.APP_NAME
            }
            url = f"https://api.github.com/repos/{Config.GITHUB_REPO}/releases/latest"
            print(f"Fetching latest release from: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"GitHub API response received: {data.get('tag_name', 'No tag')}")
                if 'tag_name' in data and data['tag_name']:
                    version = data['tag_name'].lstrip('v')
                    return {
                        'version': version,
                        'download_url': data.get('html_url', f"https://github.com/{Config.GITHUB_REPO}/releases/latest"),
                        'release_notes': data.get('body', 'No release notes available'),
                        'success': True,
                        'assets': data.get('assets', [])
                    }
            elif response.status_code == 404:
                print(f"Repository not found: {Config.GITHUB_REPO}")
            else:
                print(f"GitHub API error: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching releases: {e}")
        except Exception as e:
            print(f"Unexpected error fetching releases: {e}")
        
        return {
            'version': Config.DEFAULT_VERSION,
            'download_url': f"https://github.com/{Config.GITHUB_REPO}",
            'release_notes': 'Unable to fetch latest release.',
            'success': False,
            'error': 'Failed to fetch from GitHub API'
        }
    
    @staticmethod
    def get_current_version() -> str:
        version = VersionManager.load_local_version()
        if version:
            print(f"Using local version: {version}")
            return version
        
        cached = VersionManager.get_cached_latest()
        if cached and cached != Config.DEFAULT_VERSION:
            print(f"Using cached version: {cached}")
            FileManager.write_version_file(Config.VERSION_FILE, cached)
            return cached
        
        print("No local version found, fetching from GitHub...")
        release_info = VersionManager.fetch_latest_release()
        if release_info.get('success') and release_info['version'] != Config.DEFAULT_VERSION:
            version = release_info['version']
            VersionManager.cache_latest_version(version)
            FileManager.write_version_file(Config.VERSION_FILE, version)
            print(f"Fetched and cached version: {version}")
            return version
        
        print("Using default version")
        return Config.DEFAULT_VERSION
    
    @staticmethod
    def is_newer_version(new: str, current: str) -> bool:
        try:
            def to_tuple(v: str) -> tuple:
                parts = [int(p) if p.isdigit() else 0 for p in v.split('.')[:3]]
                return tuple(parts) + (0, 0, 0)[:3-len(parts)]
            return to_tuple(new) > to_tuple(current)
        except:
            return new > current

class UpdateChecker(QThread):
    update_available = pyqtSignal(dict)
    check_completed = pyqtSignal(bool, str)
    version_fetched = pyqtSignal(str)
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            print("Starting update check...")
            release_info = VersionManager.fetch_latest_release()
            latest_version = release_info.get('version', self.current_version)
            self.version_fetched.emit(latest_version)
            if release_info.get('success', False):
                if VersionManager.is_newer_version(latest_version, self.current_version):
                    self.update_available.emit(release_info)
                    self.check_completed.emit(True, f"Update available: v{latest_version}")
                else:
                    self.check_completed.emit(True, f"You're up to date! (v{self.current_version})")
            else:
                self.check_completed.emit(True, "Update check unavailable")
                VersionManager.cache_latest_version(latest_version)
        except Exception as e:
            print(f"Update check error: {e}")
            self.check_completed.emit(False, f"Update check failed: {str(e)}")

class Styles:
    BASE_STYLES = {
        "Dark": """
            QMainWindow { background-color: #1e1e2e; color: #ffffff; }
            QGroupBox { font-weight: bold; border: 1px solid #333; border-radius: 8px; 
                       margin-top: 10px; padding: 10px; color: #fff; background-color: #2e2e3e; }
            QLabel { color: #ffffff; }
            QLineEdit { background-color: #2e2e3e; border: 1px solid #444; 
                       border-radius: 5px; padding: 5px; color: #fff; }
            QTextEdit { background-color: #2e2e3e; color: #fff; border: 1px solid #444; 
                       border-radius: 5px; padding: 5px; }
            QComboBox { background-color: #2e2e3e; color: white; border: 1px solid #444; 
                       border-radius: 5px; padding: 5px; }
            QTabWidget::pane { border: 1px solid #333; background: #2e2e3e; }
            QTabBar::tab { background: #2e2e3e; color: #aaa; padding: 8px; }
            QTabBar::tab:selected { background: #0a84ff; color: white; }
        """,
        "Light": """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; 
                       margin-top: 10px; padding: 10px; color: #000; background-color: #ffffff; }
            QLabel { color: #000; }
            QLineEdit { background-color: #fff; border: 1px solid #aaa; 
                       border-radius: 5px; padding: 5px; color: #000; }
            QTextEdit { background-color: #fff; color: #000; border: 1px solid #aaa; 
                       border-radius: 5px; padding: 5px; }
            QComboBox { background-color: #fff; color: #000; border: 1px solid #aaa; 
                       border-radius: 5px; padding: 5px; }
            QTabWidget::pane { border: 1px solid #ccc; background: #fff; }
            QTabBar::tab { background: #e0e0e0; color: #444; padding: 8px; }
            QTabBar::tab:selected { background: #0078d7; color: white; }
        """
    }
    
    COLOR_THEMES = {
        "Blue": {"base": "#0078d4", "hover": "#106ebe"},
        "Green": {"base": "#107c10", "hover": "#0a5f0a"},
        "Red": {"base": "#d13438", "hover": "#a52a2e"},
        "Orange": {"base": "#d24726", "hover": "#a63d1f"},
        "Purple": {"base": "#701cb8", "hover": "#5a1699"},
        "Teal": {"base": "#00838f", "hover": "#006d77"},
        "Pink": {"base": "#e91e63", "hover": "#c2185b"},
        "Indigo": {"base": "#3f51b5", "hover": "#303f9f"},
        "Amber": {"base": "#ff9800", "hover": "#f57c00"},
        "Cyan": {"base": "#00bcd4", "hover": "#00acc1"},
        "Lime": {"base": "#cddc39", "hover": "#c0ca33"},
        "DeepPurple": {"base": "#9c27b0", "hover": "#8e24aa"},
        "Brown": {"base": "#795548", "hover": "#5d4037"},
        "Grey": {"base": "#9e9e9e", "hover": "#757575"},
        "Magenta": {"base": "#e91e63", "hover": "#ad1457"},
        "Gold": {"base": "#ffd700", "hover": "#ffb300"},
        "Turquoise": {"base": "#26c6da", "hover": "#00bcd4"},
        "Coral": {"base": "#ff7f50", "hover": "#ff6b35"},
        "Mint": {"base": "#98fb98", "hover": "#7cfc00"},
        "Lavender": {"base": "#e6e6fa", "hover": "#d8bfd8"}
    }
    
    @classmethod
    def get_base_style(cls, mode: str) -> str:
        return cls.BASE_STYLES.get(mode, cls.BASE_STYLES["Dark"])
    
    @classmethod
    def get_button_style(cls, theme: str, appearance: str = "Dark") -> str:
        theme_config = cls.COLOR_THEMES.get(theme, cls.COLOR_THEMES["Blue"])
        base_color = theme_config["base"]
        hover_color = theme_config["hover"]
        
        if appearance == "Light":
            base_color = cls._darken_color(base_color, 0.1)
            hover_color = cls._darken_color(hover_color, 0.15)
        
        style = f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {cls._darken_color(base_color, 0.2)};
            }}
            QPushButton:disabled {{
                background-color: #666;
                color: #999;
            }}
        """
        return style
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float) -> str:
        try:
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
            return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        except:
            return hex_color
    
    @classmethod
    def apply_theme_to_all_buttons(cls, parent_widget, theme: str, appearance: str):
        buttons = parent_widget.findChildren(QPushButton)
        button_style = cls.get_button_style(theme, appearance)
        for button in buttons:
            button.setStyleSheet(button_style)

class UIManager:
    def __init__(self, parent):
        self.parent = parent
        self.widgets = {}
    
    def create_header(self) -> QWidget:
        layout = QHBoxLayout()
        header_label = QLabel(f"⚙️ {Config.APP_NAME}")
        header_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        try:
            icon_path = FileManager.download_icon()
            self.parent.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Failed to set window icon: {e}")

        self.widgets['version_display'] = QLabel(f"v{self.parent.current_version}")
        self.widgets['version_display'].setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4;")
        
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
        group = QGroupBox("🖱️ Click Settings")
        form = QFormLayout()
        
        self.widgets['click_count'] = QLineEdit("1")
        self.widgets['loop_count'] = QLineEdit("0")
        self.widgets['click_delay'] = QLineEdit("1")
        self.widgets['cycle_delay'] = QLineEdit("0.5")
        
        form.addRow("Clicks per Cycle:", self.widgets['click_count'])
        form.addRow("Max Cycles (0=∞):", self.widgets['loop_count'])
        form.addRow("Delay Between Clicks (s):", self.widgets['click_delay'])
        form.addRow("Delay Between Cycles (s):", self.widgets['cycle_delay'])
        
        group.setLayout(form)
        return group
    
    def create_theme_settings(self) -> QGroupBox:
        group = QGroupBox("🎨 Interface")
        form = QFormLayout()
        
        self.widgets['appearance_combo'] = QComboBox()
        self.widgets['appearance_combo'].addItems(["Dark", "Light"])
        self.widgets['appearance_combo'].currentTextChanged.connect(self.parent.update_theme)
        
        self.widgets['color_combo'] = QComboBox()
        self.widgets['color_combo'].addItems(list(Styles.COLOR_THEMES.keys()))
        self.widgets['color_combo'].currentTextChanged.connect(self.parent.update_color_theme)
        
        self.widgets['progress_label'] = QLabel("Cycles: 0")
        self.widgets['progress_label'].setAlignment(Qt.AlignRight)
        
        form.addRow("Appearance Mode:", self.widgets['appearance_combo'])
        form.addRow("Color Theme:", self.widgets['color_combo'])
        form.addRow("Progress:", self.widgets['progress_label'])
        
        group.setLayout(form)
        return group
    
    def create_update_tab(self) -> QWidget:
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
        layout.addWidget(self.widgets['update_text'])
        
        widget.setLayout(layout)
        return widget
    
    def update_version_display(self, current: str, latest: str = None):
        if 'version_display' in self.widgets:
            self.widgets['version_display'].setText(f"v{current}")

        if 'current_version_label' in self.widgets:
            self.widgets['current_version_label'].setText(f"Current: v{current}")

        if latest and 'latest_version_label' in self.widgets:
            self.widgets['latest_version_label'].setText(f"Latest: v{latest}")

        if hasattr(self.parent, 'tray') and self.parent.tray and self.parent.tray.tray_icon:
            self.parent.tray.tray_icon.setToolTip(f"{Config.APP_NAME} v{current}")
    
    def set_update_logs(self):
        if 'update_text' in self.widgets:
            logs = "\n\n".join(Config.UPDATE_LOGS)
            self.widgets['update_text'].setPlainText(logs)

class SystemTrayManager:
    def __init__(self, parent):
        self.parent = parent
        self.tray_icon = None
        self.setup_tray()
    
    def setup_tray(self):
        try:
            icon_path = FileManager.download_icon()
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path))
            self.update_tooltip()
            menu = self.create_tray_menu()
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
        except Exception as e:
            print(f"Tray setup failed: {e}")
    
    def update_tooltip(self):
        if self.tray_icon:
            self.tray_icon.setToolTip(f"{Config.APP_NAME} v{self.parent.current_version}")
    
    def create_tray_menu(self) -> QMenu:
        menu = QMenu()
        actions = [
            ("👁️ Show", self.parent.show_normal),
            ("▶️ Start/Stop", self.parent.toggle_clicking),
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
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick or reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.parent.show_normal()
    
    def show_minimize_notification(self):
        if self.tray_icon:
            self.tray_icon.showMessage(
                Config.APP_NAME, f"{Config.APP_NAME} just minimized to tray!",
                QSystemTrayIcon.Information, 1500
            )

class ClickerEngine:
    def __init__(self, parent):
        self.parent = parent
        self.running = False
        self.thread = None
    
    def start(self):
        if self.running:
            return
        self.running = True
        if hasattr(self.parent, 'start_btn'):
            self.parent.start_btn.setEnabled(False)
        if hasattr(self.parent, 'stop_btn'):
            self.parent.stop_btn.setEnabled(True)
        if 'progress_label' in self.parent.ui.widgets:
            self.parent.ui.widgets['progress_label'].setText("Cycles: 0")
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()
        self.parent.log("▶️ Started clicking")
    
    def stop(self):
        self.running = False
        if hasattr(self.parent, 'start_btn'):
            self.parent.start_btn.setEnabled(True)
        if hasattr(self.parent, 'stop_btn'):
            self.parent.stop_btn.setEnabled(False)
        self.parent.log("⏹️ Stopped clicking")
    
    def _click_loop(self):
        try:
            settings = self._get_settings()
            cycle_count = 0
            while (self.running and (settings['max_loops'] == 0 or cycle_count < settings['max_loops'])):
                for _ in range(settings['clicks']):
                    if not self.running:
                        break
                    pyautogui.click()
                    self.parent.log("🖱️ Clicked")
                    time.sleep(settings['click_delay'])
                cycle_count += 1
                if 'progress_label' in self.parent.ui.widgets:
                    self.parent.ui.widgets['progress_label'].setText(f"Cycles: {cycle_count}")
                self.parent.log(f"Cycle {cycle_count} complete")
                time.sleep(settings['cycle_delay'])
        except Exception as e:
            self.parent.log(f"❌ Clicker error: {e}")
        finally:
            self.stop()
    
    def _get_settings(self) -> Dict[str, Any]:
        widgets = self.parent.ui.widgets
        def safe_int(widget, default):
            try: return int(widget.text() or default)
            except: return default
        def safe_float(widget, default):
            try: return float(widget.text() or default)
            except: return default
        return {
            'clicks': max(1, safe_int(widgets.get('click_count'), 1)),
            'max_loops': safe_int(widgets.get('loop_count'), 0),
            'click_delay': max(0.01, safe_float(widgets.get('click_delay'), 1.0)),
            'cycle_delay': max(0.01, safe_float(widgets.get('cycle_delay'), 0.5))
        }

class AutoClickerApp(QMainWindow):
    def __init__(self, lock: SingletonLock):
        super().__init__()
        self.lock = lock
        self.current_version = VersionManager.get_current_version()
        
        self.latest_version = self.current_version
        self.update_checker = None
        self.current_appearance = "Dark"
        self.current_color_theme = "Blue"
        
        self.ui = UIManager(self)
        self.tray = SystemTrayManager(self)
        self.clicker = ClickerEngine(self)
        
        # Connect lock activation signal AFTER creating the window
        self.lock.activation_requested.connect(self.show_normal)
        
        self._init_ui()
        self._setup_timers()
        self._setup_hotkeys()
        self.ui.set_update_logs()
        self.update_theme()
    
    def _init_ui(self):
        self.setWindowTitle(f"{Config.APP_NAME} v{self.current_version}")
        self.setFixedSize(640, 580)
        self.setStyleSheet(Styles.get_base_style(self.current_appearance))
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        layout.addWidget(self.ui.create_header())
        self._setup_tabs(layout)
        self._setup_controls(layout)
        
        self.ui.update_version_display(self.current_version)
        Styles.apply_theme_to_all_buttons(self, self.current_color_theme, self.current_appearance)
    
    def _setup_tabs(self, layout):
        tabs = QTabWidget()
        
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.addWidget(self.ui.create_click_settings())
        settings_layout.addWidget(self.ui.create_theme_settings())
        settings_layout.addStretch()
        tabs.addTab(settings_tab, "Settings")
        
        updates_tab = self.ui.create_update_tab()
        tabs.addTab(updates_tab, "Updates")
        
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        tabs.addTab(log_tab, "Activity Log")
        
        layout.addWidget(tabs)
    
    def _setup_controls(self, layout):
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton(f"▶️ Start ({Config.HOTKEY})")
        self.stop_btn = QPushButton(f"⏹️ Stop ({Config.HOTKEY})")
        self.stop_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self.toggle_clicking)
        self.stop_btn.clicked.connect(self.clicker.stop)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
    
    def _setup_timers(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_for_updates_silent)
        self.update_timer.start(Config.UPDATE_CHECK_INTERVAL)
        QTimer.singleShot(3000, self.check_for_updates)
    
    def _setup_hotkeys(self):
        try:
            keyboard.add_hotkey(Config.HOTKEY, self.toggle_clicking)
            print(f"Hotkey {Config.HOTKEY} registered")
        except Exception as e:
            print(f"Failed to setup hotkey: {e}")
    
    def toggle_clicking(self):
        if self.clicker.running:
            self.clicker.stop()
        else:
            self.clicker.start()
    
    def check_for_updates(self, silent: bool = False):
        if self.update_checker and self.update_checker.isRunning():
            return
        if not silent:
            self.log("🔄 Checking for updates...")
        self.update_checker = UpdateChecker(self.current_version)
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.check_completed.connect(self._on_check_completed)
        self.update_checker.version_fetched.connect(self._on_version_fetched)
        self.update_checker.start()
    
    def check_for_updates_silent(self):
        self.check_for_updates(silent=True)
    
    def update_theme(self, appearance: str = None):
        if appearance is None and 'appearance_combo' in self.ui.widgets:
            appearance = self.ui.widgets['appearance_combo'].currentText()
        self.current_appearance = appearance or "Dark"
        self.setStyleSheet(Styles.get_base_style(self.current_appearance))
        Styles.apply_theme_to_all_buttons(self, self.current_color_theme, self.current_appearance)
        self.update_color_theme()
    
    def update_color_theme(self, theme: str = None):
        if theme is None and 'color_combo' in self.ui.widgets:
            theme = self.ui.widgets['color_combo'].currentText()
        self.current_color_theme = theme or "Blue"
        Styles.apply_theme_to_all_buttons(self, self.current_color_theme, self.current_appearance)
    
    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def _on_version_fetched(self, latest_version: str):
        self.latest_version = latest_version
        self.ui.update_version_display(self.current_version, self.latest_version)
        if 'last_check_label' in self.ui.widgets:
            self.ui.widgets['last_check_label'].setText(
                f"Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        FileManager.update_last_check()
    
    def _on_update_available(self, info: dict):
        reply = QMessageBox.question(
            self, "Update Available",
            f"New version {info['version']} available!\n\n"
            f"Current: v{self.current_version}\nLatest: v{info['version']}\n\n"
            f"Visit GitHub for download?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            webbrowser.open(info['download_url'])
        self.log(f"🆕 Update available: v{info['version']}")
    
    def _on_check_completed(self, success: bool, message: str):
        status = "✅" if success else "ℹ️"
        self.log(f"{status} {message}")
    
    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if self.tray and self.tray.tray_icon:
            self.tray.show_minimize_notification()
    
    def quit_app(self):
        self.log("👋 Shutting down...")
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if self.tray and self.tray.tray_icon:
            self.tray.tray_icon.hide()
        try:
            keyboard.unhook_all()
            QApplication.quit()
        except:
            pass

class initializer:
    def __init__(self):
        super().__init__()
        pass

    def activate_existing_instance(self, lockfile_path: Path):
        """Attempt to activate existing instance using port from lockfile"""
        try:
            port = None
            if lockfile_path.exists():
                try:
                    port = int(lockfile_path.read_text().strip())
                except (ValueError, OSError):
                    return False
            if not port:
                return False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((Config.PORTS, port))
            sock.send(b"ACTIVATE")
            sock.close()
            return True
        except Exception:
            return False

    def run(self):
        """Application entry point with singleton enforcement"""
        try:
            memory = psutil.virtual_memory()
            memory_is_available = memory.available < 256 * 1024 * 1024 # Less than 256MB
            if memory_is_available:
                print("Warning: Low memory available")
        except ImportError:
            print("psutil not available, skipping resource check")

        FileManager.ensure_app_directory()
        lock = SingletonLock()

        with lock.acquire() as acquired_lock:
            if acquired_lock is None:
                print("Another instance detected")
                reply = QMessageBox.question(
                    None, "Instance Already Running",
                    "Sigma Auto Clicker is already running.\nActivate existing instance?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    if self.activate_existing_instance(lock.lockfile_path):
                        print("Activation signal sent")
                    else:
                        QMessageBox.warning(
                            None,
                            "Error", 
                            "Could not activate existing instance"
                        )
                sys.exit(0)
        
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName(Config.APP_NAME)
        app.setOrganizationName(Config.AUTHORNAME)
        
        try:
            icon_path = FileManager.download_icon()
            app_icon = QIcon(icon_path)
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
            window = AutoClickerApp(lock)
            window.show()
            sys.exit(app.exec())
        except Exception as e:
            print(f"Application error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    Appinitializer = initializer()
    Appinitializer.run()
