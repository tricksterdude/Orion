from datetime import datetime
from pathlib import Path


class Logger:

    def __init__(self):
        self.log_file = Path("logs/orion.log")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"

        # Display on screen
        print(line)

        # Save to file
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(line + "\n")