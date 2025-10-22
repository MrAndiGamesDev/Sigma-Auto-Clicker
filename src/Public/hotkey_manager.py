import keyboard
from src.Public.logger import Logger
from src.Public.config import Config

class HotkeyManager:
    """Manages hotkey registration and validation."""
    def __init__(self, logger: Logger):
        self.logger = logger
        self.current_hotkey = Config.load_hotkey()

    def register_hotkey(self, hotkey: str, callback: callable) -> bool:
        """Register a hotkey with the keyboard library."""
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(hotkey, callback)
            self.current_hotkey = hotkey
            self.logger.log(f"Hotkey '{hotkey}' registered")
            return True
        except Exception as e:
            self.logger.log(f"Failed to register hotkey '{hotkey}': {e}")
            return False

    def validate_hotkey(self, hotkey: str) -> bool:
        """Validate hotkey format."""
        try:
            keys = [k.strip().lower() for k in hotkey.split('+')]
            if not keys:
                return False
            valid_modifiers = {'ctrl', 'alt', 'shift', 'cmd', 'win', 'control', 'command'}
            main_key = keys[-1]
            modifiers = keys[:-1] if len(keys) > 1 else []
            if not (main_key.isalnum() or main_key in keyboard.all_modifiers or len(main_key) == 1):
                return False
            return all(mod in valid_modifiers for mod in modifiers)
        except Exception:
            return False

    def update_hotkey(self, new_hotkey: str, callback: callable) -> bool:
        """Update the current hotkey."""
        if not new_hotkey:
            self.logger.log("❌ No hotkey provided")
            return False
        if not self.validate_hotkey(new_hotkey):
            self.logger.log(f"❌ Invalid hotkey format: '{new_hotkey}'. Use format like 'Ctrl+F' or 'Alt+Shift+G'")
            return False
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(new_hotkey, lambda: None)  # Test registration
            keyboard.unhook_all()
            Config.save_hotkey(new_hotkey)
            self.register_hotkey(new_hotkey, callback)
            self.logger.log(f"✅ Hotkey updated to '{new_hotkey}'")
            return True
        except Exception as e:
            self.logger.log(f"❌ Failed to set hotkey '{new_hotkey}': {e}")
            self.register_hotkey(self.current_hotkey, callback)
            return False