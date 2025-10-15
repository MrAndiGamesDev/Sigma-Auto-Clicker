import subprocess
import sys
from time import sleep
from pathlib import Path
from src.Packages.CustomLogging import Logging

class VirtualEnvManager:
    """Manages creation, activation, and package installation for a virtual environment."""

    def __init__(self, venv_path: str, requirements_file: str = "requirements.txt"):
        """Initialize with virtual environment path and optional requirements file."""
        self.logger = Logging.Log  # Store custom logger
        self.venv_path = Path(venv_path)
        self.requirements_file = Path(requirements_file)
        self.activate_script = self._get_activate_script()

    def _get_activate_script(self) -> Path:
        """Determine the appropriate activation script based on the platform."""
        if sys.platform.startswith("win"):
            return self.venv_path / "Scripts" / "Activate.ps1"
        return self.venv_path / "bin" / "activate"

    def setup_venv(self) -> bool:
        """Create a virtual environment if it doesn't exist."""
        if self.venv_path.exists():
            self.logger("info", f"Virtual environment already exists at {self.venv_path}")
            return True
        try:
            self.logger("info", f"Creating virtual environment at {self.venv_path}...")
            subprocess.check_call([sys.executable, "-m", "venv", str(self.venv_path)])
            return True
        except subprocess.CalledProcessError as e:
            self.logger("error", f"Failed to create virtual environment: {e}")
            return False
        except Exception as e:
            self.logger("error", f"Unexpected error during virtual environment creation: {e}")
            return False

    def activate_venv(self) -> bool:
        """Activate the virtual environment."""
        if not self.activate_script.exists():
            self.logger("warning", f"Activation script not found at {self.activate_script}")
            return False
        try:
            self.logger("info", f"Activating virtual environment at {self.venv_path}")
            if sys.platform.startswith("win"):
                subprocess.check_call(
                    ["powershell", "-ExecutionPolicy", "Bypass", str(self.activate_script)]
                )
            else:
                # For Unix-like systems, source the activate script
                subprocess.check_call(["bash", "-c", f"source {self.activate_script}"])
            return True
        except subprocess.CalledProcessError as e:
            self.logger("error", f"Failed to activate virtual environment: {e}")
            return False
        except Exception as e:
            self.logger("error", f"Unexpected error during activation: {e}")
            return False

    def install_requirements(self) -> bool:
        """Install requirements from the requirements file if it exists."""
        if not self.requirements_file.exists():
            self.logger("warning", f"Requirements file not found at {self.requirements_file}")
            return False
        try:
            self.logger("info", f"Installing requirements from {self.requirements_file}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)]
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger("error", f"Failed to install requirements: {e}")
            return False
        except Exception as e:
            self.logger("error", f"Unexpected error during requirements installation: {e}")
            return False

    def manage_venv(self) -> bool:
        """Manage the virtual environment: create, activate, and install packages."""
        if self.activate_script.exists():
            self.logger("info", "Virtual environment detected. Proceeding with activation and installation...")
        else:
            self.logger("info", "Virtual environment not found. Setting up environment...")
            if not self.setup_venv():
                return False

        if not self.activate_venv():
            return False
        return self.install_requirements()

def exit():
    """Exit the script with a message."""
    Logging.Log("info", "Exiting script.")
    sleep(1)
    sys.exit(1)

def run():
    """Main entry point for the script."""
    try:
        venv_manager = VirtualEnvManager("AutoClickerPy")
        success = venv_manager.manage_venv()
        if not success:
            exit()
    except Exception as e:
        Logging.Log("error", f"Unexpected error in main: {e}")
        exit()

if __name__ == "__main__":
    run()
