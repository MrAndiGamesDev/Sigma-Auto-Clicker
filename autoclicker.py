import sys
import threading
import time
import pyautogui
import platform
import os
import urllib.request
import subprocess
import keyboard
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit, QFileDialog,
    QComboBox, QSystemTrayIcon, QMenu, QFormLayout
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

# ======================
# CONFIG
# ======================
APP_TITLE = "Sigma Auto Clicker"
HOTKEY = "F3"
ICON_URL = "https://raw.githubusercontent.com/MrAndiGamesDev/My-App-Icons/refs/heads/main/mousepointer.ico"

SYSTEM = platform.system()
HOME_DIR = os.path.expanduser("~")
APPDATA_DIR = os.path.join(HOME_DIR, "AppData", "Roaming", "SigmaAutoClicker") 
APP_ICON = os.path.join(APPDATA_DIR, "mousepointer.ico")

# ======================
# SPEED CONFIG
# ======================
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# ======================
# THEMES & COLORS
# ======================
BASE_STYLE = {
    "Dark": """
        QMainWindow { background-color: #1e1e2e; }
        QGroupBox { font-weight: bold; border: 1px solid #333; border-radius: 8px; margin-top: 10px; padding: 10px; color: #fff; }
        QLabel { color: #ffffff; }
        QLineEdit { background-color: #2e2e3e; border: 1px solid #444; border-radius: 5px; padding: 3px; color: #fff; }
        QPushButton { background-color: #0a84ff; color: white; border-radius: 6px; padding: 5px; }
        QPushButton:hover { background-color: #1c9bff; }
        QTextEdit { background-color: #2e2e3e; color: #fff; border: 1px solid #444; border-radius: 5px; }
        QTabWidget::pane { border: 1px solid #333; border-radius: 6px; }
        QTabBar::tab { background: #2e2e3e; color: #aaa; padding: 8px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #0a84ff; color: white; }
        QComboBox { background-color: #2e2e3e; color: white; border: 1px solid #444; border-radius: 5px; padding: 3px; }
    """,
    "Light": """
        QMainWindow { background-color: #f0f0f0; }
        QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; padding: 10px; color: #000; }
        QLabel { color: #000; }
        QLineEdit { background-color: #fff; border: 1px solid #aaa; border-radius: 5px; padding: 3px; color: #000; }
        QPushButton { background-color: #0078d7; color: white; border-radius: 6px; padding: 5px; }
        QPushButton:hover { background-color: #005a9e; }
        QTextEdit { background-color: #fff; color: #000; border: 1px solid #aaa; border-radius: 5px; }
        QTabWidget::pane { border: 1px solid #ccc; border-radius: 6px; }
        QTabBar::tab { background: #e0e0e0; color: #444; padding: 8px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #0078d7; color: white; }
        QComboBox { background-color: #fff; color: #000; border: 1px solid #aaa; border-radius: 5px; padding: 3px; }
    """
}

COLOR_THEMES = {
    "Blue": "#0a84ff",
    "Green": "#28a745",
    "Dark-Blue": "#0b5ed7",
    "Red": "#d32f2f",
    "Orange": "#ff9800",
    "Purple": "#9c27b0",
    "Teal": "#009688",
    "Pink": "#e91e63",
    "Yellow": "#fbc02d",
    "Cyan": "#00bcd4",
    "Gray": "#6c757d",
    "Indigo": "#3f51b5",
}

# ======================
# HELPER FUNCTIONS
# ======================
def ensure_hidden_directory(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    if SYSTEM == "Windows":
        subprocess.run(["attrib", "+H", path], check=True)

def download_icon():
    ensure_hidden_directory(APPDATA_DIR)
    if not os.path.exists(APP_ICON):
        urllib.request.urlretrieve(ICON_URL, APP_ICON)
        if SYSTEM == "Windows":
            subprocess.run(["attrib", "+H", APP_ICON], check=True)
    return APP_ICON

# ======================
# MAIN APP
# ======================
class AutoClickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setFixedSize(640, 580)
        self.setStyleSheet(BASE_STYLE["Dark"])
        self.setWindowIcon(QIcon(download_icon()))

        # State
        self.running = False
        self.cycle_count = 0
        self.click_thread = None

        # Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # Header
        self.header = QLabel(f"⚙️ {APP_TITLE}")
        self.header.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.main_layout.addWidget(self.header, alignment=Qt.AlignLeft)

        # Tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Build tabs
        self.settings_tab = QWidget()
        self.log_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.log_tab, "Activity Log")

        self.build_settings_tab()
        self.build_log_tab()

        # Bottom controls
        self.start_btn = QPushButton(f"▶️ Start ({HOTKEY})")
        self.stop_btn = QPushButton(f"⏹️ Stop ({HOTKEY})")
        self.stop_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.toggle_clicking)
        self.stop_btn.clicked.connect(self.stop_clicking)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        self.main_layout.addLayout(btn_layout)

        # Hotkey
        keyboard.add_hotkey(HOTKEY, self.toggle_clicking)

        # System tray
        self.setup_tray()

        # Theme handlers
        self.appearance_combo.currentTextChanged.connect(self.update_theme)
        self.color_combo.currentTextChanged.connect(self.update_color_theme)
        self.update_theme()
        self.update_color_theme()

    # ----------------------
    # Build Settings Tab
    # ----------------------
    def build_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Click settings
        click_group = QGroupBox("🖱️ Click Settings")
        click_form = QFormLayout()
        click_group.setLayout(click_form)
        self.click_count = QLineEdit("1")
        self.loop_count = QLineEdit("0")
        self.click_delay = QLineEdit("0.05")
        self.cycle_delay = QLineEdit("0.5")
        click_form.addRow("Clicks per Cycle:", self.click_count)
        click_form.addRow("Max Cycles (0=∞):", self.loop_count)
        click_form.addRow("Delay Between Clicks (s):", self.click_delay)
        click_form.addRow("Delay Between Cycles (s):", self.cycle_delay)
        layout.addWidget(click_group)

        # Interface
        theme_group = QGroupBox("🎨 Interface")
        theme_form = QFormLayout()
        theme_group.setLayout(theme_form)
        self.appearance_combo = QComboBox()
        self.appearance_combo.addItems(["System", "Light", "Dark"])
        self.color_combo = QComboBox()
        self.color_combo.addItems(list(COLOR_THEMES.keys()))
        self.progress_label = QLabel("Cycles: 0")
        self.progress_label.setAlignment(Qt.AlignRight)
        theme_form.addRow("Appearance Mode:", self.appearance_combo)
        theme_form.addRow("Color Theme:", self.color_combo)
        theme_form.addRow("Progress:", self.progress_label)
        layout.addWidget(theme_group)

    # ----------------------
    # Build Log Tab
    # ----------------------
    def build_log_tab(self):
        layout = QVBoxLayout(self.log_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        export_btn = QPushButton("💾 Export Log")
        export_btn.clicked.connect(self.export_log)
        layout.addWidget(export_btn, alignment=Qt.AlignRight)

    # ----------------------
    # Click Logic
    # ----------------------
    def toggle_clicking(self):
        if self.running:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        self.running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.cycle_count = 0
        self.progress_label.setText("Cycles: 0")
        self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.click_thread.start()
        self.log("Started clicking")

    def stop_clicking(self):
        self.running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("Stopped clicking")

    def _click_loop(self):
        click_delay = float(self.click_delay.text() or 0.05)
        cycle_delay = float(self.cycle_delay.text() or 0.5)
        clicks_per_cycle = int(self.click_count.text() or 1)
        max_loops = int(self.loop_count.text() or 0)

        while self.running and (max_loops == 0 or self.cycle_count < max_loops):
            for _ in range(clicks_per_cycle):
                if not self.running:
                    break
                pyautogui.click()
                self.log("Clicked mouse")
                time.sleep(click_delay)

            self.cycle_count += 1
            self.progress_label.setText(f"Cycles: {self.cycle_count}")
            self.log(f"Cycle {self.cycle_count} complete")
            time.sleep(cycle_delay)

        self.stop_clicking()

    # ----------------------
    # Logging
    # ----------------------
    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def export_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Log", "", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                f.write(self.log_text.toPlainText())

    # ----------------------
    # Theme Updates
    # ----------------------
    def update_theme(self):
        mode = self.appearance_combo.currentText()
        self.setStyleSheet(BASE_STYLE.get(mode, BASE_STYLE["Dark"]))
        self.update_color_theme()

    def update_color_theme(self):
        color = self.color_combo.currentText()
        if color in COLOR_THEMES:
            btn_color = COLOR_THEMES[color]
            self.start_btn.setStyleSheet(
                f"background-color: {btn_color}; color: white; border-radius: 6px; padding: 5px;"
            )
            self.stop_btn.setStyleSheet(
                f"background-color: #D32F2F; color: white; border-radius: 6px; padding: 5px;"
            )
            # Update tabs
            tab_style = f"""
                QTabBar::tab:selected {{ background: {btn_color}; color: white; }}
                QTabBar::tab {{ background: #2e2e3e; color: #aaa; padding: 8px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            """
            self.tabs.setStyleSheet(tab_style)

    # ----------------------
    # System Tray
    # ----------------------
    def setup_tray(self):
        tray_icon = QSystemTrayIcon(QIcon(APP_ICON if APP_ICON else QIcon()))
        tray_icon.setToolTip(APP_TITLE)
        
        tray_menu = QMenu()
        
        # Show the main window
        tray_menu.addAction(QAction("Show Window", self, triggered=self.show_normal))
        
        # Start / Stop clicking
        tray_menu.addAction(QAction("Start / Stop", self, triggered=self.toggle_clicking))
        
        # Quit the app completely
        tray_menu.addAction(QAction("Quit", self, triggered=self.quit_app))
        
        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()
        
        self.tray_icon = tray_icon

    def show_normal(self):
        """Show window and bring to front"""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Intercept close button: hide window instead of quitting"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_TITLE,
            "App minimized to tray. Use the tray icon to quit.",
            QSystemTrayIcon.Information,
            2000
        )

    def quit_app(self):
        """Fully quit the app"""
        self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerApp()
    window.show()
    sys.exit(app.exec())