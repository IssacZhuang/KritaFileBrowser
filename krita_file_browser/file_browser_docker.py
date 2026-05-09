from krita import DockWidget


class FileBrowserDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Browser")

    def canvasChanged(self, canvas):
        pass
