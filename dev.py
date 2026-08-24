import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start()

    def start(self):
        self.process = subprocess.Popen(["python3", "main.py"])

    def restart(self):
        self.process.terminate()
        self.process.wait()
        self.start()

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            self.restart()


handler = ReloadHandler()

observer = Observer()
observer.schedule(handler, ".", recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()