import subprocess
import sys
from typing import List, Optional
from time import sleep
from src.Packages.CustomLogging import Logging

class PackageUpdater:
    """Manages updating outdated Python packages using pip."""
    def __init__(self):
        """Initialize with custom logger."""
        self.logger = Logging.Log

    def _log(self, level: str, message: str) -> None:
        """Log a message using the custom logger."""
        self.logger(level, message)

    def _get_outdated_packages(self) -> List[str]:
        """Retrieve a list of outdated package names."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated"],
                capture_output=True,
                text=True,
                check=True,
            )
            outdated = result.stdout.strip().split("\n")
            # Parse package names, ignoring empty lines or malformed output
            packages = [line.split("==")[0] for line in outdated if line and "==" in line]
            return packages
        except subprocess.CalledProcessError as e:
            self._log("error", f"Failed to list outdated packages: {e.stderr}")
            raise RuntimeError(f"Failed to list outdated packages: {e.stderr}") from e
        except Exception as e:
            self._log("error", f"Unexpected error while listing outdated packages: {e}")
            raise RuntimeError(f"Unexpected error: {e}") from e

    def _update_packages(self, packages: List[str]) -> bool:
        """Update the specified packages to their latest versions."""
        if not packages:
            self._log("info", "All packages are up to date.")
            return True

        try:
            self._log("info", f"Updating {len(packages)} package(s): {', '.join(packages)}")
            # Upgrade all packages in one command for efficiency
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade"] + packages,
                capture_output=True,
                text=True,
                check=True,
            )
            self._log("info", f"Update completed: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            self._log("error", f"Failed to update packages: {e.stderr}")
            return False
        except Exception as e:
            self._log("error", f"Unexpected error during package update: {e}")
            return False

    def update(self) -> bool:
        """Update all outdated packages and return success status."""
        try:
            packages = self._get_outdated_packages()
            return self._update_packages(packages)
        except RuntimeError:
            return False
        
    def exit_script(self, duration, lvl=1):
        """Exit the script with a message."""
        self._log("info", "Exiting script.")
        sleep(duration)
        sys.exit(lvl)

def run():
    """Main entry point for the script."""
    try:
        updater = PackageUpdater()
        success = updater.update()
        if not success:
            updater.exit_script(2)
    except Exception as e:
        Logging.Log("error", f"Unexpected error in main: {e}")
        updater.exit_script(2)

if __name__ == "__main__":
    run()
