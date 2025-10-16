import os
import shutil
import sys
import PyInstaller.__main__
from time import sleep
from typing import Optional
from src.Packages.CustomLogging import Logging

class PyInstallerBuilder:
    """Handles cleaning build directories and building executables using PyInstaller."""
    def __init__(self, script_file: Optional[str] | None = None):
        self.Logging = Logging.Log
        self.FirePyinstaller = PyInstaller.__main__
        self.script_file = (script_file or (sys.argv[1] if len(sys.argv) > 1 else "autoclicker.py"))

    def cleanup_dirs(self, dirs=["build", "dist"]) -> None:
        """Remove specified directories if they exist."""
        for folder in dirs:
            folder_is_exists = os.path.exists(folder)
            if folder_is_exists:
                self.Logging("info", f"Removing '{folder}' directory...")
                sleep(2)
                try:
                    shutil.rmtree(folder)
                except Exception as e:
                    self.Logging("warning", f"Failed to remove {folder}: {e}")
            else:
                self.Logging("warning", f"'{folder}' directory not found — skipping.")

    def load_version(self, path: str) -> None:
        try:
            with open(path, 'r') as file:
                return file.read().strip()  # Read and remove any surrounding whitespace
        except Exception as e:
            pass

    def build_executable(self) -> None:
        """Build the executable using PyInstaller."""
        self.Logging("info", f"Building executable for '{self.script_file}'...")
        sleep(2)
        try:
            pyinstaller_args = [
                "--noconfirm",
                "--onefile",
                f"--name=Sigma Auto Clicker ({self.load_version("VERSION.txt")})",
                "--windowed",
                "--icon=src\\Assets\\icons\\mousepointer.ico",
                "--optimize=2",
                "--strip",
                "--clean",
                self.script_file
            ]
            self.FirePyinstaller.run(pyinstaller_args)
            self.Logging("success", "Build completed successfully.")
        except Exception as e:
            self.Logging("error", f"PyInstaller build failed: {e}")

    def exit_script(self, duration, lvl=1):
        """Exit the script with a message."""
        self.Logging("info", "Exiting script.")
        sleep(duration)
        sys.exit(lvl)

    def run(self) -> None:
        self.Logging("info", f"Building executable for '{self.script_file}'...")
        sleep(2)
        try:
            self.cleanup_dirs()
            self.build_executable()
        except Exception as e:
            self.Logging("error", f"An error occurred: {e}")
            self.exit_script(2)

if __name__ == "__main__":
    PyConverter = PyInstallerBuilder()
    PyConverter.run()