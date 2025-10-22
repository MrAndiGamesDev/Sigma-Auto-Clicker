import os
import shutil
import sys
import PyInstaller.__main__
from time import sleep
from typing import Optional, List
from src.Packages.CustomLogging import Logging

class PyInstallerBuilder:
    """Manages the build process for creating executables using PyInstaller."""
    
    def __init__(self, script_file: Optional[str] = None):
        """
        Initialize the PyInstallerBuilder with script file and configuration.

        Args:
            script_file (Optional[str]): Path to the main script file to build.
                Defaults to sys.argv[1] or 'autoclicker.py'.
        """
        self.logger = Logging.Log
        self.script_file = script_file or (sys.argv[1] if len(sys.argv) > 1 else "autoclicker.py")
        self.app_name = "Sigma Auto Clicker"
        self.version_file = "VERSION.txt"
        self.icon_path = "src/icons/mousepointer.ico"
        
        # Validate critical paths
        self._validate_script_file()
        
        # PyInstaller configuration
        self.pyinstaller_args = [
            self.script_file,
            "--noconfirm",
            "--onefile",
            "--windowed",
            f"--name={self._get_executable_name()}",
            f"--icon={self.icon_path}",
            "--optimize=2",
            "--clean",
            f"--add-data={self.icon_path};src/icons/",
            f"--add-data={self.version_file};.",
            "--hidden-import=PySide6",
            "--hidden-import=pyautogui",
            "--hidden-import=keyboard",
            "--hidden-import=psutil",
            "--hidden-import=requests"
        ]

    def _validate_script_file(self) -> None:
        """Validate that the script file exists."""
        if not os.path.exists(self.script_file):
            self.logger("error", f"Script file '{self.script_file}' not found.")
            self._exit_script()

    def _get_executable_name(self) -> str:
        """Generate executable name with version if available."""
        version = self._load_version()
        return f"{self.app_name} (v{version})" if version else self.app_name

    def _load_version(self) -> str:
        """Load version from VERSION.txt, return empty string if failed."""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r', encoding='utf-8') as file:
                    return file.read().strip()
            self.logger("warning", f"Version file '{self.version_file}' not found.")
            return ""
        except Exception as e:
            self.logger("warning", f"Failed to load version from '{self.version_file}': {e}")
            return ""

    def _remove_directory(self, path: str) -> None:
        """Remove a directory if it exists."""
        if os.path.exists(path):
            self.logger("info", f"Removing '{path}' directory...")
            try:
                shutil.rmtree(path, ignore_errors=True)
                self.logger("success", f"'{path}' directory removed successfully.")
            except Exception as e:
                self.logger("warning", f"Failed to remove '{path}': {e}")
        else:
            self.logger("info", f"'{path}' directory not found — skipping.")

    def _remove_file(self, file_path: str) -> bool:
        """Remove a file if it exists, return True if removed."""
        if os.path.exists(file_path):
            self.logger("info", f"Removing '{file_path}'...")
            try:
                os.remove(file_path)
                self.logger("success", f"'{file_path}' removed successfully.")
                return True
            except Exception as e:
                self.logger("warning", f"Failed to remove '{file_path}': {e}")
        return False

    def cleanup_dirs(self) -> None:
        """Remove build, dist directories, and .spec files."""
        # Clean directories
        for folder in ["build", "dist"]:
            self._remove_directory(folder)

        # Clean .spec files
        possible_spec_names = [
            f"{os.path.splitext(self.script_file)[0]}.spec",
            "Sigma_Auto_Clicker.spec",
            "SigmaAutoClicker.spec",
            f"{self._get_executable_name().replace(' ', '_').replace('(', '').replace(')', '')}.spec"
        ]

        removed_count = 0
        # Remove known spec files
        for spec_file in possible_spec_names:
            if self._remove_file(spec_file):
                removed_count += 1

        # Remove any additional .spec files
        for file in os.listdir('.'):
            if file.endswith('.spec') and file not in possible_spec_names:
                if self._remove_file(file):
                    removed_count += 1

        if removed_count == 0:
            self.logger("info", "No .spec files found to remove.")

    def build_executable(self) -> None:
        """Build the executable using PyInstaller."""
        self.logger("info", f"Building executable for '{self.script_file}'...")
        try:
            self.logger("info", "Running PyInstaller with arguments: " + " ".join(self.pyinstaller_args))
            PyInstaller.__main__.run(self.pyinstaller_args)
            self.logger("success", f"Executable '{self._get_executable_name()}' built successfully in 'dist' folder.")
        except Exception as e:
            self.logger("error", f"PyInstaller build failed: {e}")
            self._exit_script(2)

    def _exit_script(self, duration: int = 1, exit_code: int = 1) -> None:
        """Exit the script with a message."""
        self.logger("info", "Exiting script.")
        sleep(duration)
        sys.exit(exit_code)

    def run(self, cleanup_delay: float = 0.5) -> None:
        """
        Execute the build process: clean directories and build executable.

        Args:
            cleanup_delay (float): Delay between cleanup operations in seconds.
        """
        self.logger("info", f"Starting build process for '{self.script_file}'...")
        try:
            self.cleanup_dirs()
            sleep(cleanup_delay)
            self.build_executable()
            self.logger("success", "Build process completed successfully.")
        except Exception as e:
            self.logger("error", f"Build process failed: {e}")
            self._exit_script(cleanup_delay)

if __name__ == "__main__":
    builder = PyInstallerBuilder()
    builder.run()