import os

from PyQt5.QtCore import QThread, pyqtSignal

from .constants import SUPPORTED_EXTENSIONS


class SearchWorker(QThread):
    """Recursively searches a directory for files matching a query string."""

    results_ready = pyqtSignal(list)

    def __init__(self, root_path, query, parent=None):
        super().__init__(parent)
        self.root_path = root_path
        self.query = query.lower()
        self._cancelled = False

    def run(self):
        results = []
        for dirpath, _dirnames, filenames in os.walk(self.root_path):
            if self._cancelled:
                self.results_ready.emit(results)
                return
            for filename in filenames:
                if self._cancelled:
                    self.results_ready.emit(results)
                    return
                if self.query in filename.lower():
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        results.append(os.path.join(dirpath, filename))
        self.results_ready.emit(results)

    def cancel(self):
        self._cancelled = True
