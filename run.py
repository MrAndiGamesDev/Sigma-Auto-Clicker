IsDev = True

if __name__ == '__main__':
    try:
        if IsDev == True:
            from src.Public.sigma_auto_clicker_dev import AppLauncher
            launcher = AppLauncher()
        else:
            from src.Public.sigma_auto_clicker import AppLauncher
            launcher = AppLauncher()
        launcher.run()
    except ImportError as e:
        print(f"Failed to import AppLauncher: {e}")