import os

from PyQt5.QtWidgets import QMessageBox, QInputDialog
from krita import Krita


SUPPORTED_EXTENSIONS = {
    ".kra", ".krz",
    ".ora", ".psd", ".xcf", ".svg",
    ".png", ".jpg", ".jpeg", ".gif",
    ".tif", ".tiff", ".bmp",
    ".exr", ".webp", ".heif", ".heic",
    ".jp2", ".jxl", ".tga", ".hdr", ".pdf",
}


def open_file(filepath, parent=None):
    """Open a file in Krita. Returns the Document on success, None on failure."""
    app = Krita.instance()
    doc = app.openDocument(filepath)
    if doc is not None:
        window = app.activeWindow()
        if window is not None:
            window.addView(doc)
        return doc

    QMessageBox.critical(
        parent,
        "Open File Error",
        f"Could not open file:\n{filepath}",
    )
    return None


def create_file(directory, parent=None):
    """Create a new .kra file in the given directory. Returns True on success."""
    name, ok = QInputDialog.getText(
        parent,
        "New File",
        "File name:",
        text="Untitled.kra",
    )
    if not ok or not name.strip():
        return False

    name = name.strip()
    if not name.endswith(".kra"):
        name += ".kra"

    filepath = os.path.join(directory, name)

    if os.path.exists(filepath):
        QMessageBox.warning(
            parent,
            "File Exists",
            f"A file named '{name}' already exists in this directory.",
        )
        return False

    app = Krita.instance()
    doc = app.createDocument(1920, 1080, name, "RGBA", "U8", "", 150.0)
    if doc is None:
        QMessageBox.critical(parent, "Error", "Failed to create document.")
        return False

    window = app.activeWindow()
    if window is not None:
        window.addView(doc)

    doc.saveAs(filepath)
    return True


def delete_file(filepath, parent=None):
    """Delete a file after user confirmation. Returns True on success."""
    filename = os.path.basename(filepath)
    reply = QMessageBox.question(
        parent,
        "Delete File",
        f"Are you sure you want to delete '{filename}'?\n\nThis action cannot be undone.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
        return False

    try:
        os.remove(filepath)
        return True
    except OSError as e:
        QMessageBox.critical(
            parent,
            "Delete Error",
            f"Could not delete file:\n{e}",
        )
        return False
