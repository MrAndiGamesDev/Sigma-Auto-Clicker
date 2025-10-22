import time
from typing import Optional
from PySide6.QtWidgets import QTextEdit

class Logger:
    """Centralized logging for the application."""
    def __init__(self, log_widget: Optional[QTextEdit] = None):
        self.log_widget = log_widget

    def log(self, message: str) -> None:
        """Log a message to the Activity Log tab or print if no widget is set."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}]: {message}"
        if self.log_widget:
            self.log_widget.append(formatted_message)
            self.log_widget.verticalScrollBar().setValue(self.log_widget.verticalScrollBar().maximum())
        else:
            print(formatted_message)