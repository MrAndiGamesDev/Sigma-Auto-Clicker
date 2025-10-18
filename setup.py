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

    def cleanup_dirs(self) -> None:
        """Remove specified directories and .spec files if they exist."""
        # Clean directories (existing code)
        for folder in ["build", "dist"]:
            folder_exists = os.path.exists(folder)
            if folder_exists:
                self.Logging("info", f"Removing '{folder}' directory...")
                sleep(2)
                try:
                    shutil.rmtree(folder)
                    self.Logging("success", f"'{folder}' directory removed successfully.")
                except Exception as e:
                    self.Logging("warning", f"Failed to remove {folder}: {e}")
            else:
                self.Logging("warning", f"'{folder}' directory not found — skipping.")
        
        # Clean spec files
        self.cleanup_spec_files()  # Call the new method

    def cleanup_spec_files(self) -> None:
        """Remove all possible .spec files that might have been generated."""
        possible_spec_names = []
        
        # Default spec file based on script name
        spec_base = os.path.splitext(self.script_file)[0]
        possible_spec_names.append(f"{spec_base}.spec")
        
        # Try spec file with versioned name
        version = self.load_version("VERSION.txt")
        if version:
            # Create safe filename by replacing invalid characters
            safe_name = "".join(c for c in f"Sigma Auto Clicker (v{version})" 
                            if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').replace('(', '').replace(')', '')
            possible_spec_names.append(f"{safe_name}.spec")
        
        # Also try common variations
        possible_spec_names.extend([
            "Sigma_Auto_Clicker.spec",
            "SigmaAutoClicker.spec",
            "*.spec"  # We'll handle wildcard logic below
        ])
        
        removed_count = 0
        for spec_candidate in possible_spec_names:
            if spec_candidate == "*.spec":
                # Handle wildcard by finding all .spec files in current directory
                spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
                for spec_file in spec_files:
                    spec_path = os.path.join('.', spec_file)
                    if os.path.exists(spec_path):
                        self.Logging("info", f"Removing found spec file '{spec_file}'...")
                        sleep(1)
                        try:
                            os.remove(spec_path)
                            self.Logging("success", f"'{spec_file}' spec file removed successfully.")
                            removed_count += 1
                        except Exception as e:
                            self.Logging("warning", f"Failed to remove {spec_file}: {e}")
            else:
                spec_file = spec_candidate
                if os.path.exists(spec_file):
                    self.Logging("info", f"Removing '{spec_file}' spec file...")
                    sleep(1)
                    try:
                        os.remove(spec_file)
                        self.Logging("success", f"'{spec_file}' spec file removed successfully.")
                        removed_count += 1
                    except Exception as e:
                        self.Logging("warning", f"Failed to remove {spec_file}: {e}")
        
        if removed_count == 0:
            self.Logging("info", "No .spec files found to remove.")

    def load_version(self, path: str) -> str:
        """Load version from file, return empty string if failed."""
        try:
            with open(path, 'r') as file:
                return file.read().strip()  # Read and remove any surrounding whitespace
        except Exception as e:
            self.Logging("warning", f"Failed to load version from {path}: {e}")
            return ""

    def build_executable(self) -> None:
        """Build the executable using PyInstaller."""
        self.Logging("info", f"Building executable for '{self.script_file}'...")
        sleep(2)
        
        version = self.load_version("VERSION.txt")
        executable_name = f"Sigma Auto Clicker (v{version})" if version else "Sigma Auto Clicker"
        
        try:
            pyinstaller_args = [
                "--noconfirm",
                "--onefile",
                "--noconsole",
                "--windowed",
                f"--name={executable_name}",
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

    def exit_script(self, duration: int, lvl=1):
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
