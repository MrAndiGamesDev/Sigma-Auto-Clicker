import subprocess
import sys

def update_packages():
    # Get list of outdated packages
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=freeze'],
        capture_output=True, text=True
    )
    outdated = result.stdout.strip().split('\n')
    packages = [line.split('==')[0] for line in outdated if line]

    if not packages:
        print("All packages are up to date.")
        return

    for package in packages:
        print(f"Updating {package}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', package])

if __name__ == "__main__":
    update_packages()