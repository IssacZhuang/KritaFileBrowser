import os
import re
import shutil

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from krita import Krita


def open_file(filepath, parent=None):
    """Open a file in Krita. Returns the Document on success, None on failure."""
    app = Krita.instance()
    try:
        doc = app.openDocument(filepath)
    except Exception:
        doc = None

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


class NewFileDialog(QDialog):
    """Dialog for creating a new .kra file with custom document properties."""

    COLOR_MODELS = ["RGBA", "CMYKA", "GRAYA", "LABA", "XYZA", "YCbCrA", "A"]
    COLOR_DEPTHS = ["U8", "U16", "F16", "F32"]

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New File")
        self._directory = directory
        self._app = Krita.instance()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- File name ---
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("File name:"))
        self._name_edit = QLineEdit("Untitled.kra")
        name_layout.addWidget(self._name_edit)
        layout.addLayout(name_layout)

        # --- Dimensions group ---
        dim_group = QWidget()
        dim_layout = QFormLayout(dim_group)
        dim_layout.setContentsMargins(0, 0, 0, 0)

        dim_row = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 99999)
        self._width_spin.setValue(1920)
        self._width_spin.setSuffix(" px")
        dim_row.addWidget(self._width_spin)
        dim_row.addWidget(QLabel("x"))
        self._height_spin = QSpinBox()
        self._height_spin.setRange(1, 99999)
        self._height_spin.setValue(1080)
        self._height_spin.setSuffix(" px")
        dim_row.addWidget(self._height_spin)
        dim_layout.addRow("Dimensions:", dim_row)

        self._resolution_spin = QDoubleSpinBox()
        self._resolution_spin.setRange(1.0, 9999.0)
        self._resolution_spin.setValue(150.0)
        self._resolution_spin.setSuffix(" DPI")
        self._resolution_spin.setDecimals(1)
        dim_layout.addRow("Resolution:", self._resolution_spin)

        layout.addWidget(dim_group)

        # --- Color group ---
        color_group = QWidget()
        color_layout = QFormLayout(color_group)
        color_layout.setContentsMargins(0, 0, 0, 0)

        self._color_model_combo = QComboBox()
        self._color_model_combo.addItems(self.COLOR_MODELS)
        self._color_model_combo.setCurrentText("RGBA")
        color_layout.addRow("Color model:", self._color_model_combo)

        self._color_depth_combo = QComboBox()
        self._color_depth_combo.addItems(self.COLOR_DEPTHS)
        self._color_depth_combo.setCurrentText("U8")
        color_layout.addRow("Color depth:", self._color_depth_combo)

        layout.addWidget(color_group)

        # --- Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_document_params(self):
        """Return (name, width, height, color_model, color_depth, resolution)."""
        return (
            self._name_edit.text().strip(),
            self._width_spin.value(),
            self._height_spin.value(),
            self._color_model_combo.currentText(),
            self._color_depth_combo.currentText(),
            self._resolution_spin.value(),
        )


def create_file(directory, parent=None):
    """Create a new .kra file in the given directory. Returns True on success."""
    dialog = NewFileDialog(directory, parent)
    if dialog.exec_() != QDialog.Accepted:
        return False

    name, width, height, color_model, color_depth, resolution = dialog.get_document_params()

    if not name:
        QMessageBox.warning(parent, "Invalid Name", "File name cannot be empty.")
        return False

    if not name.endswith(".kra"):
        name += ".kra"

    if re.search(r'[<>:"/\\|?*]', name) or name.rstrip('.') != name:
        QMessageBox.warning(
            parent,
            "Invalid Name",
            f"The filename '{name}' contains invalid characters.",
        )
        return False

    filepath = os.path.join(directory, name)

    if os.path.exists(filepath):
        QMessageBox.warning(
            parent,
            "File Exists",
            f"A file named '{name}' already exists in this directory.",
        )
        return False

    app = Krita.instance()
    doc = app.createDocument(width, height, name, color_model, color_depth, "", resolution)
    if doc is None:
        QMessageBox.critical(parent, "Error", "Failed to create document.")
        return False

    window = app.activeWindow()
    if window is not None:
        window.addView(doc)

    doc.saveAs(filepath)
    return True


def delete_file(filepath, parent=None):
    """Delete a file or directory after user confirmation. Returns True on success."""
    filename = os.path.basename(filepath)
    is_dir = os.path.isdir(filepath)

    if is_dir:
        msg = f"Are you sure you want to delete the folder '{filename}' and all its contents?\n\nThis action cannot be undone."
    else:
        msg = f"Are you sure you want to delete '{filename}'?\n\nThis action cannot be undone."

    reply = QMessageBox.question(
        parent,
        "Delete",
        msg,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
        return False

    try:
        if is_dir:
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)
        return True
    except OSError as e:
        QMessageBox.critical(
            parent,
            "Delete Error",
            f"Could not delete:\n{e}",
        )
        return False


def create_folder(directory, parent=None):
    """Create a new folder in the given directory. Returns True on success."""
    name, ok = QInputDialog.getText(
        parent,
        "New Folder",
        "Folder name:",
        text="New Folder",
    )
    if not ok or not name.strip():
        return False

    name = name.strip()

    if re.search(r'[<>:"/\\|?*]', name) or name.rstrip('.') != name:
        QMessageBox.warning(
            parent,
            "Invalid Name",
            f"The name '{name}' contains invalid characters.",
        )
        return False

    folder_path = os.path.join(directory, name)

    if os.path.exists(folder_path):
        QMessageBox.warning(
            parent,
            "Folder Exists",
            f"A folder named '{name}' already exists.",
        )
        return False

    try:
        os.makedirs(folder_path)
        return True
    except OSError as e:
        QMessageBox.critical(
            parent,
            "Error",
            f"Could not create folder:\n{e}",
        )
        return False


def duplicate_item(filepath, parent=None):
    """Duplicate a file or folder in place. Returns the new path on success, None on failure."""
    directory = os.path.dirname(filepath)
    basename = os.path.basename(filepath)

    # Generate a unique name: "name (1).ext", "name (2).ext", ...
    name, ext = os.path.splitext(basename)
    counter = 1
    while True:
        new_name = f"{name} ({counter}){ext}"
        new_path = os.path.join(directory, new_name)
        if not os.path.exists(new_path):
            break
        counter += 1

    try:
        if os.path.isdir(filepath):
            shutil.copytree(filepath, new_path)
        else:
            shutil.copy2(filepath, new_path)
        return new_path
    except OSError as e:
        QMessageBox.critical(
            parent,
            "Duplicate Error",
            f"Could not duplicate:\n{e}",
        )
        return None
