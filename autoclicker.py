import sys
import time
import platform
import threading
import subprocess
import urllib.request
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import pyautogui
import keyboard
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QFileDialog,
    QComboBox, QSystemTrayIcon, QMenu, QFormLayout, QMessageBox
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal as pyqtSignal

# PyAutoGUI settings
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

class Config:
    """Application configuration constants"""
    APP_NAME = "Sigma Auto Clicker"
    HOTKEY = "Ctrl+F"
    ICON_URL = "https://raw.githubusercontent.com/MrAndiGamesDev/My-App-Icons/main/mousepointer.ico"
    GITHUB_REPO = "MrAndiGamesDev/SigmaAutoClicker"
    UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000  # 24 hours in ms
    DEFAULT_VERSION = "1.0.0"
    
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
        "2025-10-16: Fixed An Update Management Bug and much more!",
        "2025-10-16: Added automatic update checking Version management UI/Code improvements UI Improvements And Much More!",
        "2025-10-15: Fixed Light Mode support and UI improvements",
        "2025-10-14: Added Update Logs tab and color themes",
        "2025-10-13: Initial release"
    ]

class FileManager:
    """Handles file operations and persistence"""
    
    @staticmethod
    def ensure_app_directory():
        """Create and configure app directory"""
        Config.APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        if Config.SYSTEM == "Windows":
            try:
                subprocess.run(["attrib", "+H", str(Config.APPDATA_DIR)], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass
    
    @staticmethod
    def download_icon() -> str:
        """Download and cache application icon with fallback"""
        FileManager.ensure_app_directory()
        if not Config.APP_ICON.exists():
            try:
                urllib.request.urlretrieve(Config.ICON_URL, Config.APP_ICON)
                if Config.SYSTEM == "Windows":
                    subprocess.run(["attrib", "+H", str(Config.APP_ICON)], 
                                 check=True, capture_output=True)
            except Exception as e:
                print(f"Failed to download icon: {e}")
                Config.APP_ICON.touch()
        return str(Config.APP_ICON)
    
    @staticmethod
    def read_version_file(filepath: Path) -> Optional[str]:
        """Safely read version from file"""
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
        """Write version to file"""
        try:
            FileManager.ensure_app_directory()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(version)
        except Exception as e:
            print(f"Error writing version file {filepath}: {e}")

    @staticmethod
    def update_last_check():
        """Update last update check timestamp"""
        try:
            Config.UPDATE_CHECK_FILE.write_text(datetime.now().isoformat())
        except Exception:
            pass

class VersionManager:
    """Manages application versioning and updates"""
    
    @staticmethod
    def load_local_version() -> Optional[str]:
        """Load version from local VERSION.txt or cached current version"""
        local_file = Path('VERSION.txt')
        version = FileManager.read_version_file(local_file)
        if version:
            FileManager.write_version_file(Config.VERSION_FILE, version)
            return version
        return FileManager.read_version_file(Config.VERSION_FILE)
    
    @staticmethod
    def get_cached_latest() -> Optional[str]:
        """Get cached latest version with age validation"""
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
        """Cache latest version with timestamp"""
        try:
            timestamp = int(time.time())
            Config.VERSION_CACHE_FILE.write_text(f"{version}\n{timestamp}", encoding='utf-8')
        except Exception:
            pass
    
    @staticmethod
    def fetch_latest_release() -> Dict[str, Any]:
        """Fetch latest release info from GitHub API"""
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': Config.APP_NAME
            }
            url = f"https://api.github.com/repos/{Config.GITHUB_REPO}/releases/latest"
            print(f"Fetching latest release from: {url}")  # Debug log
            
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
                else:
                    print("No tag_name found in response")
                    
            elif response.status_code == 404:
                print(f"Repository not found: {Config.GITHUB_REPO}")
            else:
                print(f"GitHub API error: HTTP {response.status_code} - {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching releases: {e}")
        except Exception as e:
            print(f"Unexpected error fetching releases: {e}")
        
        # Fallback response
        return {
            'version': Config.DEFAULT_VERSION,
            'download_url': f"https://github.com/{Config.GITHUB_REPO}",
            'release_notes': 'Unable to fetch latest release. Please check GitHub manually.',
            'success': False,
            'error': 'Failed to fetch from GitHub API'
        }
    
    @staticmethod
    def get_current_version() -> str:
        """Get the currently running version"""
        # First try local VERSION.txt
        version = VersionManager.load_local_version()
        if version:
            print(f"Using local version: {version}")
            return version
        
        # Try cached latest version
        cached = VersionManager.get_cached_latest()
        if cached and cached != Config.DEFAULT_VERSION:
            print(f"Using cached version: {cached}")
            FileManager.write_version_file(Config.VERSION_FILE, cached)
            return cached
        
        # Fetch from GitHub if no local version found
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
        """Compare two version strings"""
        try:
            def to_tuple(v: str) -> tuple:
                parts = [int(p) if p.isdigit() else 0 for p in v.split('.')[:3]]
                return tuple(parts) + (0, 0, 0)[:3-len(parts)]
            return to_tuple(new) > to_tuple(current)
        except:
            return new > current


class UpdateChecker(QThread):
    """Background thread for checking updates"""
    
    update_available = pyqtSignal(dict)
    check_completed = pyqtSignal(bool, str)
    version_fetched = pyqtSignal(str)
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        """Execute update check"""
        try:
            print("Starting update check...")
            release_info = VersionManager.fetch_latest_release()
            latest_version = release_info.get('version', self.current_version)
            print(f"Latest version found: {latest_version}, Current: {self.current_version}")
            
            self.version_fetched.emit(latest_version)
            
            if release_info.get('success', False):
                if VersionManager.is_newer_version(latest_version, self.current_version):
                    print(f"Update available: {latest_version} > {self.current_version}")
                    self.update_available.emit(release_info)
                    self.check_completed.emit(True, f"Update available: v{latest_version}")
                else:
                    print("No update available")
                    self.check_completed.emit(True, f"You're up to date! (v{self.current_version})")
            else:
                self.check_completed.emit(True, "Update check unavailable - continuing with current version")
                VersionManager.cache_latest_version(latest_version)
                
        except Exception as e:
            print(f"Update check error: {e}")
            self.check_completed.emit(False, f"Update check failed: {str(e)}")


# [Rest of the classes remain the same: Styles, UIManager, SystemTrayManager, ClickerEngine, AutoClickerApp]
class Styles:
    """UI styling management"""
    BASE_STYLES = {
        "Dark": """
            QMainWindow { background-color: #1e1e2e; color: #ffffff; }
            QGroupBox { font-weight: bold; border: 1px solid #333; border-radius: 8px; 
                       margin-top: 10px; padding: 10px; color: #fff; background-color: #2e2e3e; }
            QLabel { color: #ffffff; }
            QLineEdit { background-color: #2e2e3e; border: 1px solid #444; 
                       border-radius: 5px; padding: 5px; color: #fff; }
            QPushButton { background-color: #0a84ff; color: white; border: none; 
                         border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1c9bff; }
            QPushButton:disabled { background-color: #555; color: #888; }
            QTextEdit { background-color: #2e2e3e; color: #fff; border: 1px solid #444; 
                       border-radius: 5px; padding: 5px; }
            QTabWidget::pane { border: 1px solid #333; border-radius: 6px; background: #2e2e3e; }
            QTabBar::tab { background: #2e2e3e; color: #aaa; padding: 8px; 
                          border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #0a84ff; color: white; }
            QComboBox { background-color: #2e2e3e; color: white; border: 1px solid #444; 
                       border-radius: 5px; padding: 5px; }
        """,
        "Light": """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; 
                       margin-top: 10px; padding: 10px; color: #000; background-color: #ffffff; }
            QLabel { color: #000; }
            QLineEdit { background-color: #fff; border: 1px solid #aaa; 
                       border-radius: 5px; padding: 5px; color: #000; }
            QPushButton { background-color: #0078d7; color: white; border: none; 
                         border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:disabled { background-color: #ccc; color: #666; }
            QTextEdit { background-color: #fff; color: #000; border: 1px solid #aaa; 
                       border-radius: 5px; padding: 5px; }
            QTabWidget::pane { border: 1px solid #ccc; border-radius: 6px; background: #fff; }
            QTabBar::tab { background: #e0e0e0; color: #444; padding: 8px; 
                          border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #0078d7; color: white; }
            QComboBox { background-color: #fff; color: #000; border: 1px solid #aaa; 
                       border-radius: 5px; padding: 5px; }
        """
    }
    
    COLOR_THEMES = {
        "Blue": "#0a84ff", "Green": "#28a745", "Red": "#d32f2f",
        "Orange": "#ff9800", "Purple": "#9c27b0", "Teal": "#009688"
    }
    
    @classmethod
    def get_base_style(cls, mode: str) -> str:
        return cls.BASE_STYLES.get(mode, cls.BASE_STYLES["Dark"])
    
    @classmethod
    def get_button_style(cls, theme: str) -> str:
        color = cls.COLOR_THEMES.get(theme, "#0a84ff")
        return f"QPushButton {{ background-color: {color}; color: white; border: none; border-radius: 6px; padding: 8px; font-weight: bold; }} QPushButton:hover {{ background-color: {color[:-2]}cc; }}"


# [UIManager, SystemTrayManager, ClickerEngine, AutoClickerApp classes remain the same as in your original code]
class UIManager:
    def __init__(self, parent):
        self.parent = parent
        self.widgets = {}
    
    def create_header(self) -> QWidget:
        layout = QHBoxLayout()
        header_label = QLabel(f"⚙️ {Config.APP_NAME}")
        header_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        
        self.widgets['version_display'] = QLabel(f"v{self.parent.current_version}")
        self.widgets['version_display'].setStyleSheet("font-size: 18px; font-weight: bold; color: #0a84ff;")
        
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
        layout = QVBoxLayout(widget)
        
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
        
        return widget
    
    def update_version_display(self, current: str, latest: str = None):
        if 'version_display' in self.widgets:
            self.widgets['version_display'].setText(f"v{current}")
        if 'current_version_label' in self.widgets:
            self.widgets['current_version_label'].setText(f"Current: v{current}")
        if latest and 'latest_version_label' in self.widgets:
            self.widgets['latest_version_label'].setText(f"Latest: v{latest}")
        
        if hasattr(self.parent, 'tray') and self.parent.tray.tray_icon:
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
            print("System tray icon created successfully")
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
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick or \
           reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.parent.show_normal()
    
    def show_minimize_notification(self):
        if self.tray_icon:
            self.tray_icon.showMessage(
                Config.APP_NAME,
                f"{Config.APP_NAME} minimized to tray",
                QSystemTrayIcon.Information,
                2000
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
        self.parent.start_btn.setEnabled(False)
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
            
            while (self.running and 
                   (settings['max_loops'] == 0 or cycle_count < settings['max_loops'])):
                
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
                
        except ValueError as e:
            self.parent.log(f"❌ Invalid settings: {e}")
        except Exception as e:
            self.parent.log(f"❌ Clicker error: {e}")
        finally:
            self.stop()
    
    def _get_settings(self) -> Dict[str, Any]:
        widgets = self.parent.ui.widgets
        return {
            'clicks': max(1, int(widgets.get('click_count', QLineEdit("1")).text() or 1)),
            'max_loops': int(widgets.get('loop_count', QLineEdit("0")).text() or 0),
            'click_delay': max(0.01, float(widgets.get('click_delay', QLineEdit("1")).text() or 1)),
            'cycle_delay': max(0.01, float(widgets.get('cycle_delay', QLineEdit("0.5")).text() or 0.5))
        }

class AutoClickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_version = VersionManager.get_current_version()
        print(f"Application starting with version: {self.current_version}")
        self.latest_version = self.current_version
        self.update_checker = None
        
        self.ui = UIManager(self)
        self.tray = SystemTrayManager(self)
        self.clicker = ClickerEngine(self)
        
        self._init_ui()
        self._setup_timers()
        self._setup_hotkeys()
        self.ui.set_update_logs()
    
    # [Rest of AutoClickerApp methods remain the same as in your original code]
    def _init_ui(self):
        self.setWindowTitle(f"{Config.APP_NAME} v{self.current_version}")
        self.setFixedSize(640, 580)
        self.setStyleSheet(Styles.get_base_style("Dark"))
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        layout.addWidget(self.ui.create_header())
        self._setup_tabs(layout)
        self._setup_controls(layout)
        
        self.ui.update_version_display(self.current_version)
    
    def _setup_tabs(self, layout):
        tabs = QTabWidget()
        
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(10, 10, 10, 10)
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
    
    def update_theme(self):
        if 'appearance_combo' in self.ui.widgets:
            mode = self.ui.widgets['appearance_combo'].currentText()
            self.setStyleSheet(Styles.get_base_style(mode))
            self.update_color_theme()
    
    def update_color_theme(self):
        if 'color_combo' in self.ui.widgets:
            theme = self.ui.widgets['color_combo'].currentText()
            style = Styles.get_button_style(theme)
            if hasattr(self, 'start_btn'):
                self.start_btn.setStyleSheet(style)
    
    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
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
            import webbrowser
            webbrowser.open(info['download_url'])
        self.log(f"🆕 Update available: v{info['version']}")
    
    def _on_check_completed(self, success: bool, message: str):
        status = "✅" if success else "ℹ️"
        self.log(f"{status} {message}")
        FileManager.update_last_check()
    
    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if self.tray.tray_icon:
            self.tray.show_minimize_notification()
    
    def quit_app(self):
        self.log("👋 Shutting down...")
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if self.tray.tray_icon:
            self.tray.tray_icon.hide()
        try:
            keyboard.unhook_all()
        except:
            pass
        QApplication.quit()

def main():
    """Application entry point"""
    FileManager.ensure_app_directory()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = AutoClickerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
