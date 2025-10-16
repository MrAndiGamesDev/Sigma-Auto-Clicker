import sys
import os
import time
import platform
import threading
import subprocess
import urllib.request
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pyautogui
import keyboard
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QFileDialog,
    QComboBox, QSystemTrayIcon, QMenu, QFormLayout, QMessageBox, QProgressBar
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QEvent, QThread, Signal as pyqtSignal

# ======================
# CONSTANTS & CONFIG
# ======================
class Config:
    APP_NAME = "Sigma Auto Clicker"
    HOTKEY = "F3"
    ICON_URL = "https://raw.githubusercontent.com/MrAndiGamesDev/My-App-Icons/refs/heads/main/mousepointer.ico"
    GITHUB_REPO = "MrAndiGamesDev/SigmaAutoClicker"
    UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000  # 24 hours in ms
    DEFAULT_VERSION = "1.0.0"
    UPDATE_LOGS = [
        "2025-10-16: Added automatic update checking and version management and some UI/Code improvements",
        "2025-10-15: Fixed Light Mode support and UI improvements",
        "2025-10-14: Added Update Logs tab and color themes",
        "2025-10-13: Initial release"
    ]
    
    # Paths
    SYSTEM = platform.system()
    HOME_DIR = Path.home()
    APPDATA_DIR = HOME_DIR / "AppData" / "Roaming" / "SigmaAutoClicker" if SYSTEM == "Windows" else HOME_DIR / ".sigma_autoclicker"
    APP_ICON = APPDATA_DIR / "mousepointer.ico"
    UPDATE_CHECK_FILE = APPDATA_DIR / "last_update_check.txt"
    VERSION_CACHE_FILE = APPDATA_DIR / "version_cache.txt"

# PyAutoGUI settings
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# ======================
# UTILITY FUNCTIONS
# ======================
class FileUtils:
    @staticmethod
    def path_exists(path: Path) -> bool:
        return path.exists()

    @staticmethod
    def ensure_directory(path: Path):
        path.mkdir(parents=True, exist_ok=True)
        if Config.SYSTEM == "Windows" and path.exists():
            try:
                subprocess.run(["attrib", "+H", str(path)], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass  # Non-critical

    @staticmethod
    def download_icon() -> str:
        FileUtils.ensure_directory(Config.APPDATA_DIR)
        if not FileUtils.path_exists(Config.APP_ICON):
            try:
                urllib.request.urlretrieve(Config.ICON_URL, Config.APP_ICON)
                if Config.SYSTEM == "Windows":
                    subprocess.run(["attrib", "+H", str(Config.APP_ICON)], 
                                 check=True, capture_output=True)
            except Exception as e:
                print(f"Failed to download icon: {e}")
        return str(Config.APP_ICON)

class VersionManager:
    @staticmethod
    def load_local_version() -> Optional[str]:
        version_file = Path('VERSION.txt')
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version and version != Config.DEFAULT_VERSION:
                        return version
            except Exception as e:
                print(f"Error reading VERSION.txt: {e}")
        return None

    @staticmethod
    def get_cached_version() -> Optional[str]:
        if not Config.VERSION_CACHE_FILE.exists():
            return None
        
        try:
            content = Config.VERSION_CACHE_FILE.read_text(encoding='utf-8').strip().split('\n')
            if len(content) >= 1:
                version = content[0].strip()
                if version and version != "unknown":
                    # Check cache age (7 days)
                    if len(content) >= 2:
                        cache_time = int(content[1])
                        if (time.time() - cache_time) / 86400 <= 7:
                            return version
        except Exception:
            pass
        return None

    @staticmethod
    def cache_version(version: str):
        try:
            Config.APPDATA_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            Config.VERSION_CACHE_FILE.write_text(f"{version}\n{timestamp}", encoding='utf-8')
        except Exception:
            pass

    @staticmethod
    def fetch_github_version() -> Optional[Dict[str, Any]]:
        try:
            headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': Config.APP_NAME}
            response = requests.get(
                f"https://api.github.com/repos/{Config.GITHUB_REPO}/releases/latest",
                headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                version = data.get('tag_name', 'unknown').lstrip('v')
                return {
                    'version': version,
                    'download_url': data.get('html_url'),
                    'release_notes': data.get('body', 'No release notes'),
                    'success': True
                }
        except Exception as e:
            print(f"GitHub API error: {e}")
        return {'success': False, 'error': 'Failed to fetch'}

    @staticmethod
    def get_current_version() -> str:
        # Try local first
        version = VersionManager.load_local_version()
        if version:
            return version
        
        # Try cache
        version = VersionManager.get_cached_version()
        if version:
            return version
        
        # Fetch from GitHub
        github_info = VersionManager.fetch_github_version()
        if github_info and github_info['success']:
            VersionManager.cache_version(github_info['version'])
            return github_info['version']
        
        return Config.DEFAULT_VERSION

    @staticmethod
    def is_newer_version(new: str, current: str) -> bool:
        try:
            def version_tuple(v: str) -> tuple:
                return tuple(map(int, v.split('.')))
            return version_tuple(new) > version_tuple(current)
        except:
            return new > current

# ======================
# UPDATE SYSTEM
# ======================
class UpdateChecker(QThread):
    update_available = pyqtSignal(dict)
    check_completed = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self._current_version = VersionManager.get_current_version()

    def run(self):
        try:
            # Check if recent check exists
            if Config.UPDATE_CHECK_FILE.exists():
                last_check = datetime.fromtimestamp(Config.UPDATE_CHECK_FILE.stat().st_mtime)
                if (datetime.now() - last_check).total_seconds() < 24 * 3600:
                    self.check_completed.emit(False, "Checked recently")
                    return

            github_info = VersionManager.fetch_github_version()
            if github_info['success']:
                if VersionManager.is_newer_version(github_info['version'], self._current_version):
                    self.update_available.emit(github_info)
                else:
                    self.check_completed.emit(True, "Up to date")
            else:
                self.check_completed.emit(False, github_info['error'])

            # Update check timestamp
            Config.UPDATE_CHECK_FILE.write_text(datetime.now().isoformat())
            
        except Exception as e:
            self.check_completed.emit(False, f"Update check failed: {str(e)}")

# ======================
# UI STYLES
# ======================
class Styles:
    BASE_STYLES = {
        "Dark": """
            QMainWindow { background-color: #1e1e2e; color: #ffffff; }
            QGroupBox { font-weight: bold; border: 1px solid #333; border-radius: 8px; 
                       margin-top: 10px; padding: 10px; color: #fff; }
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
            QProgressBar { border: 1px solid #444; border-radius: 5px; 
                          background-color: #2e2e3e; color: #fff; text-align: center; }
            QProgressBar::chunk { background-color: #0a84ff; border-radius: 3px; }
        """,
        "Light": """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; 
                       margin-top: 10px; padding: 10px; color: #000; }
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
            QProgressBar { border: 1px solid #aaa; border-radius: 5px; 
                          background-color: #f0f0f0; color: #000; text-align: center; }
            QProgressBar::chunk { background-color: #0078d7; border-radius: 3px; }
        """
    }

    COLOR_THEMES = {
        "Blue": "#0a84ff", "Green": "#28a745", "Dark-Blue": "#0b5ed7", "Red": "#d32f2f",
        "Orange": "#ff9800", "Purple": "#9c27b0", "Teal": "#009688", "Pink": "#e91e63",
        "Yellow": "#fbc02d", "Cyan": "#00bcd4", "Gray": "#6c757d", "Indigo": "#3f51b5",
        "Lime": "#cddc39", "Amber": "#ffc107", "Deep-Purple": "#673ab7", "Brown": "#795548",
        "Mint": "#4caf50", "Coral": "#ff6f61",
    }

    @classmethod
    def get_base_style(cls, mode: str) -> str:
        return cls.BASE_STYLES.get(mode, cls.BASE_STYLES["Dark"])

# ======================
# MAIN APPLICATION
# ======================
class AutoClickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_app()
        self._setup_ui()
        self._setup_event_handlers()
        self.running = False
        self.cycle_count = 0
        self.click_thread = None

    def _init_app(self):
        self.version = VersionManager.get_current_version()
        self.setWindowTitle(f"{Config.APP_NAME} ({self.version})")
        self.setFixedSize(640, 580)
        self.setStyleSheet(Styles.get_base_style("Dark"))
        self.setWindowIcon(QIcon(FileUtils.download_icon()))
        FileUtils.ensure_directory(Config.APPDATA_DIR)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self._build_header(layout)
        self._build_tabs(layout)
        self._build_controls(layout)

    def _build_header(self, layout):
        header_layout = QHBoxLayout()
        
        self.header = QLabel(f"⚙️ {Config.APP_NAME} ({self.version})")
        self.header.setStyleSheet("font-size: 22px; font-weight: bold;")
        
        update_btn = QPushButton("🔄 Check Updates")
        update_btn.clicked.connect(self.check_for_updates)
        update_btn.setStyleSheet("font-size: 12px; padding: 5px; border-radius: 4px;")
        
        header_layout.addWidget(self.header)
        header_layout.addStretch()
        header_layout.addWidget(update_btn)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

    def _build_tabs(self, layout):
        self.tabs = QTabWidget()
        self.settings_tab = self._create_settings_tab()
        self.log_tab = self._create_log_tab()
        self.update_tab = self._create_update_tab()

        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.log_tab, "Activity Log")
        self.tabs.addTab(self.update_tab, "Updates")
        layout.addWidget(self.tabs)

    def _create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Click settings
        click_group = self._create_click_settings()
        layout.addWidget(click_group)

        # Theme settings
        theme_group = self._create_theme_settings()
        layout.addWidget(theme_group)

        layout.addStretch()
        return widget

    def _create_click_settings(self) -> QGroupBox:
        group = QGroupBox("🖱️ Click Settings")
        form = QFormLayout()
        
        self.click_count = QLineEdit("1")
        self.loop_count = QLineEdit("0")
        self.click_delay = QLineEdit("1")
        self.cycle_delay = QLineEdit("0.5")
        
        form.addRow("Clicks per Cycle:", self.click_count)
        form.addRow("Max Cycles (0=∞):", self.loop_count)
        form.addRow("Delay Between Clicks (s):", self.click_delay)
        form.addRow("Delay Between Cycles (s):", self.cycle_delay)
        group.setLayout(form)
        return group

    def _create_theme_settings(self) -> QGroupBox:
        group = QGroupBox("🎨 Interface")
        form = QFormLayout()
        
        self.appearance_combo = QComboBox()
        self.appearance_combo.addItems(["Dark", "Light"])
        self.appearance_combo.currentTextChanged.connect(self.update_theme)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(list(Styles.COLOR_THEMES.keys()))
        self.color_combo.currentTextChanged.connect(self.update_color_theme)
        
        self.progress_label = QLabel("Cycles: 0")
        self.progress_label.setAlignment(Qt.AlignRight)
        
        form.addRow("Appearance Mode:", self.appearance_combo)
        form.addRow("Color Theme:", self.color_combo)
        form.addRow("Progress:", self.progress_label)
        group.setLayout(form)
        return group

    def _create_log_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        export_btn = QPushButton("💾 Export Log")
        export_btn.clicked.connect(self.export_log)
        layout.addWidget(export_btn, alignment=Qt.AlignRight)
        return widget

    def _create_update_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Version info
        version_group = QGroupBox("📋 Version Information")
        v_layout = QVBoxLayout()
        self.version_label = QLabel(f"Current Version: {self.version}")
        self.last_check_label = QLabel("Last Update Check: Never")
        v_layout.addWidget(self.version_label)
        v_layout.addWidget(self.last_check_label)
        version_group.setLayout(v_layout)
        layout.addWidget(version_group)
        
        # Update logs
        self.update_text = QTextEdit()
        self.update_text.setReadOnly(True)
        self.set_update_logs(Config.UPDATE_LOGS)
        layout.addWidget(self.update_text)
        
        return widget

    def _build_controls(self, layout):
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(f"▶️ Start ({Config.HOTKEY})")
        self.stop_btn = QPushButton(f"⏹️ Stop ({Config.HOTKEY})")
        self.stop_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self.toggle_clicking)
        self.stop_btn.clicked.connect(self.stop_clicking)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

    def _setup_event_handlers(self):
        keyboard.add_hotkey(Config.HOTKEY, self.toggle_clicking)
        self._setup_update_checker()
        self._setup_tray()
        self.update_theme()

    def _setup_update_checker(self):
        self.update_checker = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._periodic_update_check)
        self.update_timer.start(Config.UPDATE_CHECK_INTERVAL)
        self.check_for_updates(silent=True)

    def _setup_tray(self):
        tray_icon = QSystemTrayIcon(QIcon(str(Config.APP_ICON)))
        tray_icon.setToolTip(f"{Config.APP_NAME} ({self.version})")
        
        menu = QMenu()
        menu.addAction("Show", self.show_normal)
        menu.addAction("Start/Stop", self.toggle_clicking)
        menu.addAction("Check Updates", self.check_for_updates)
        menu.addSeparator()
        menu.addAction("Quit", self.quit_app)
        
        tray_icon.setContextMenu(menu)
        tray_icon.show()
        self.tray_icon = tray_icon

    # Public methods
    def check_for_updates(self, silent: bool = False):
        if self.update_checker and self.update_checker.isRunning():
            return
        
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.check_completed.connect(self._on_check_completed)
        self.update_checker.start()
        
        if not silent:
            self.log("Checking for updates...")

    def toggle_clicking(self):
        self.running = not self.running
        if self.running:
            self.start_clicking()
        else:
            self.stop_clicking()

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def export_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Log", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log("Log exported successfully")
            except Exception as e:
                self.log(f"Export failed: {e}")

    def update_theme(self):
        mode = self.appearance_combo.currentText()
        self.setStyleSheet(Styles.get_base_style(mode))
        self.update_color_theme()

    def update_color_theme(self):
        color = self.color_combo.currentText()
        if color in Styles.COLOR_THEMES:
            btn_color = Styles.COLOR_THEMES[color]
            style = f"background-color: {btn_color}; color: white; border-radius: 6px; padding: 8px; font-weight: bold;"
            self.start_btn.setStyleSheet(style)
            self.tabs.setStyleSheet(f"QTabBar::tab:selected {{ background: {btn_color}; color: white; }}")

    def set_update_logs(self, logs: list[str]):
        self.update_text.setPlainText("\n\n".join(logs))

    # Private methods
    def _periodic_update_check(self):
        self.check_for_updates(silent=True)

    def _on_update_available(self, info: dict):
        reply = QMessageBox.question(
            self, "Update Available",
            f"New version {info['version']} available!\n\nCurrent: {self.version}\nLatest: {info['version']}\n\nView release?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(info['download_url'])
        self.log(f"Update available: v{info['version']}")

    def _on_check_completed(self, success: bool, message: str):
        status = "✅" if success else "⚠️"
        self.log(f"{status} {message}")

    def start_clicking(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.cycle_count = 0
        self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.click_thread.start()
        self.log("Started clicking")

    def stop_clicking(self):
        self.running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("Stopped clicking")

    def _click_loop(self):
        try:
            clicks = int(self.click_count.text() or 1)
            max_loops = int(self.loop_count.text() or 0)
            click_delay = float(self.click_delay.text() or 1)
            cycle_delay = float(self.cycle_delay.text() or 0.5)

            while self.running and (max_loops == 0 or self.cycle_count < max_loops):
                for _ in range(clicks):
                    if not self.running:
                        break
                    pyautogui.click()
                    self.log("🖱️ Clicked")
                    time.sleep(click_delay)

                self.cycle_count += 1
                self.progress_label.setText(f"Cycles: {self.cycle_count}")
                self.log(f"Cycle {self.cycle_count} complete")
                time.sleep(cycle_delay)
        except ValueError as e:
            self.log(f"Invalid settings: {e}")
        finally:
            self.stop_clicking()

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def quit_app(self):
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerApp()
    window.show()
    sys.exit(app.exec())
