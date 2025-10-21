import os
import shutil
import sys
import PyInstaller.__main__
from time import sleep
from typing import Optional
from src.Packages.CustomLogging import Logging

class PyInstallerBuilder:
    """Handles cleaning build directories and building executables using PyInstaller."""
    def __init__(self, script_file: Optional[str] = None):
        """
        Initialize the PyInstallerBuilder.

        Args:
            script_file (Optional[str]): Path to the main script file to build. Defaults to sys.argv[1] or 'autoclicker.py'.
        """
        self.Logging = Logging.Log
        self.FirePyinstaller = PyInstaller.__main__
        self.script_file = script_file or (sys.argv[1] if len(sys.argv) > 1 else "autoclicker.py")
        self.app_name = "Sigma Auto Clicker"

    def cleanup_dirs(self) -> None:
        """Remove build, dist directories, and .spec files if they exist."""
        # Clean directories
        folders = ["build", "dist"]
        for folder in folders:
            Exists = os.path.exists(folder)
            if Exists:
                self.Logging("info", f"Removing '{folder}' directory...")
                sleep(1)  # Reduced sleep for faster cleanup
                try:
                    shutil.rmtree(folder, ignore_errors=True)
                    self.Logging("success", f"'{folder}' directory removed successfully.")
                except Exception as e:
                    self.Logging("warning", f"Failed to remove '{folder}': {e}")
            else:
                self.Logging("info", f"'{folder}' directory not found — skipping.")

        # Clean spec files
        self.cleanup_spec_files()

    def cleanup_spec_files(self) -> None:
        """Remove all possible .spec files that might have been generated."""
        possible_spec_names = [
            f"{os.path.splitext(self.script_file)[0]}.spec",
            "Sigma_Auto_Clicker.spec",
            "SigmaAutoClicker.spec"
        ]

        # Add versioned spec name
        version = self.load_version("VERSION.txt")
        if version:
            safe_name = "".join(c for c in f"{self.app_name} v{version}" if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').replace('(', '').replace(')', '')
            possible_spec_names.append(f"{safe_name}.spec")

        removed_count = 0
        for spec_file in possible_spec_names:
            if os.path.exists(spec_file):
                self.Logging("info", f"Removing '{spec_file}' spec file...")
                sleep(0.5)  # Reduced sleep for faster cleanup
                try:
                    os.remove(spec_file)
                    self.Logging("success", f"'{spec_file}' removed successfully.")
                    removed_count += 1
                except Exception as e:
                    self.Logging("warning", f"Failed to remove '{spec_file}': {e}")

        # Handle any additional .spec files in the directory
        for file in os.listdir('.'):
            if file.endswith('.spec') and file not in possible_spec_names:
                self.Logging("info", f"Removing additional spec file '{file}'...")
                sleep(0.5)
                try:
                    os.remove(file)
                    self.Logging("success", f"'{file}' removed successfully.")
                    removed_count += 1
                except Exception as e:
                    self.Logging("warning", f"Failed to remove '{file}': {e}")

        if removed_count == 0:
            self.Logging("info", "No .spec files found to remove.")

    def load_version(self, path: str) -> str:
        """Load version from file, return empty string if failed."""
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as file:
                    return file.read().strip()
            else:
                self.Logging("warning", f"Version file '{path}' not found.")
                return ""
        except Exception as e:
            self.Logging("warning", f"Failed to load version from '{path}': {e}")
            return ""

    def build_executable(self) -> None:
        """Build the executable using PyInstaller with no console."""
        self.Logging("info", f"Building executable for '{self.script_file}'...")
        sleep(1)  # Reduced sleep for faster execution

        version = self.load_version("VERSION.txt")
        executable_name = f"{self.app_name} (v{version})" if version else self.app_name

        # Ensure script file exists
        if not os.path.exists(self.script_file):
            self.Logging("error", f"Script file '{self.script_file}' not found.")
            self.exit_script(2)

        # Define PyInstaller arguments
        pyinstaller_args = [
            self.script_file,
            "--noconfirm",                                                              # Overwrite output without confirmation
            "--onefile",                                                                # Create a single executable file
            "--windowed",                                                               # Ensure no console window (same as --noconsole)
            f"--name={executable_name}",                                                # Set executable name
            "--icon=src\\Assets\\icons\\mousepointer.ico",                              # Icon path
            "--optimize=2",                                                             # Optimize bytecode
            "--clean",                                                                  # Clean PyInstaller cache
            "--add-data=src\\Assets\\icons\\mousepointer.ico;src\\Assets\\icons\\",     # Include icon
            "--add-data=VERSION.txt;.",                                                 # Include VERSION.txt
            "--hidden-import=PySide6",                                                  # Ensure PySide6 is included
            "--hidden-import=pyautogui",                                                # Ensure pyautogui is included
            "--hidden-import=keyboard",                                                 # Ensure keyboard is included
            "--hidden-import=psutil",                                                   # Ensure psutil is included
            "--hidden-import=requests"                                                  # Ensure requests is included
        ]

        try:
            self.Logging("info", "Running PyInstaller with arguments: " + " ".join(pyinstaller_args))
            self.FirePyinstaller.run(pyinstaller_args)
            self.Logging("success", f"Executable '{executable_name}' built successfully in 'dist' folder.")
        except Exception as e:
            self.Logging("error", f"PyInstaller build failed: {e}")
            self.exit_script(2)

    def exit_script(self, duration: int = 2, lvl: int = 1) -> None:
        """Exit the script with a message."""
        self.Logging("info", "Exiting script.")
        sleep(duration)
        sys.exit(lvl)

    def run(self, Duration=2) -> None:
        """Main method to clean directories and build the executable."""
        self.Logging("info", f"Starting build process for '{self.script_file}'...")
        try:
            self.cleanup_dirs()
            self.build_executable()
            self.Logging("success", "Build process completed successfully.")
        except Exception as e:
            self.Logging("error", f"Build process failed: {e}")
            self.exit_script(Duration)

if __name__ == "__main__":
    PyConverter = PyInstallerBuilder()
    PyConverter.run()