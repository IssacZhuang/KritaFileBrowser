# Krita File Browser Plugin - Implementation Plan

> **For agentic workers:** Use `references/subagent-driven-development.md` (recommended) or `references/executing-plans.md` to implement this plan task-by-task.

**Goal:** Build a VSCode-like file browser Docker plugin for Krita with directory browsing, file open/create/delete, and recursive search.

**Architecture:** Krita DockWidget containing a QTreeView with QFileSystemModel (filtered to supported image types), a QStackedWidget that switches between tree view and search results list, a toolbar with action buttons and search input, and a background QThread for recursive search.

**Tech Stack:** Python 3, PyQt5, Krita Python Plugin API (libkis)

---

## File Structure

```
C:\Projects\KritaFileBrowser\
├── krita_file_browser.desktop          # Plugin registration metadata
├── krita_file_browser.action           # Keyboard shortcut definitions
├── krita_file_browser/                 # Plugin module directory
│   ├── __init__.py                     # Module entry, registers Docker
│   ├── file_browser_docker.py          # DockWidget subclass — main UI layout and event wiring
│   ├── file_system_model.py            # QFileSystemModel subclass with extension filter
│   ├── file_operations.py              # Functions: open_file, create_file, delete_file
│   └── search_worker.py                # QThread subclass for recursive file search
├── install.ps1                         # Dev symlink script
├── Docs/
│   └── Feature/
│       ├── Spec/2026-05-09-krita-file-browser-design.md
│       └── Plan/2026-05-09-krita-file-browser-plan.md
```

---

### Task 1: Plugin Skeleton & Registration Files

**Files:**
- Create: `krita_file_browser.desktop`
- Create: `krita_file_browser.action`
- Create: `krita_file_browser/__init__.py`
- Create: `install.ps1`

- [ ] **Step 1: Create the .desktop registration file**

Create `krita_file_browser.desktop`:

```ini
[Desktop Entry]
Type=Service
ServiceTypes=Krita/PythonPlugin
X-KDE-Library=krita_file_browser
X-Python-2-Compatible=false
Name=File Browser
Comment=A VSCode-like file browser for browsing and opening files in Krita.
```

- [ ] **Step 2: Create the .action shortcut file**

Create `krita_file_browser.action`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ActionCollection version="2" name="Scripts">
    <Actions category="Scripts">
        <text>File Browser</text>
        <Action name="open_file_browser">
            <icon></icon>
            <text>Open File Browser</text>
            <toolTip>Open the file browser panel</toolTip>
            <shortcut></shortcut>
            <isCheckable>false</isCheckable>
        </Action>
    </Actions>
</ActionCollection>
```

- [ ] **Step 3: Create the module entry point**

Create `krita_file_browser/__init__.py`:

```python
from krita import DockWidgetFactory, DockWidgetFactoryBase
from .file_browser_docker import FileBrowserDocker

Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "fileBrowser",
        DockWidgetFactoryBase.DockRight,
        FileBrowserDocker,
    )
)
```

- [ ] **Step 4: Create the dev install script**

Create `install.ps1` in the project root:

```powershell
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$kritaRes = Join-Path $env:APPDATA "krita\pykrita"
$kritaActions = Join-Path $env:APPDATA "krita\pykrita\actions"

if (-not (Test-Path $kritaRes)) {
    New-Item -ItemType Directory -Path $kritaRes -Force | Out-Null
}
if (-not (Test-Path $kritaActions)) {
    New-Item -ItemType Directory -Path $kritaActions -Force | Out-Null
}

$desktopLink = Join-Path $kritaRes "krita_file_browser.desktop"
$moduleLink = Join-Path $kritaRes "krita_file_browser"
$actionLink = Join-Path $kritaActions "krita_file_browser.action"

if (Test-Path $desktopLink) { Remove-Item $desktopLink -Force }
if (Test-Path $moduleLink) { Remove-Item $moduleLink -Recurse -Force }
if (Test-Path $actionLink) { Remove-Item $actionLink -Force }

New-Item -ItemType SymbolicLink -Path $desktopLink -Target (Join-Path $projectRoot "krita_file_browser.desktop") | Out-Null
New-Item -ItemType SymbolicLink -Path $moduleLink -Target (Join-Path $projectRoot "krita_file_browser") | Out-Null
New-Item -ItemType SymbolicLink -Path $actionLink -Target (Join-Path $projectRoot "krita_file_browser.action") | Out-Null

Write-Host "Symlinks created in $kritaRes"
Write-Host "Restart Krita and enable the plugin in Settings > Configure Krita > Python Plugin Manager."
```

- [ ] **Step 5: Create a stub Docker class so the plugin loads without errors**

Create `krita_file_browser/file_browser_docker.py`:

```python
from krita import DockWidget


class FileBrowserDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Browser")

    def canvasChanged(self, canvas):
        pass
```

- [ ] **Step 6: Commit**

```bash
git add krita_file_browser.desktop krita_file_browser.action krita_file_browser/__init__.py krita_file_browser/file_browser_docker.py install.ps1
git commit -m "feat: add plugin skeleton with registration files and dev install script"
```

---

### Task 2: File System Model with Extension Filter

**Files:**
- Create: `krita_file_browser/file_system_model.py`

- [ ] **Step 1: Create the filtered file system model**

Create `krita_file_browser/file_system_model.py`:

```python
import os
from PyQt5.QtCore import QSortFilterProxyModel, Qt


SUPPORTED_EXTENSIONS = {
    ".kra", ".krz",
    ".ora",
    ".psd",
    ".xcf",
    ".svg",
    ".png", ".jpg", ".jpeg", ".gif",
    ".tif", ".tiff",
    ".bmp",
    ".exr",
    ".webp",
    ".heif", ".heic",
    ".jp2",
    ".jxl",
    ".tga",
    ".hdr",
    ".pdf",
}


class FileFilterProxyModel(QSortFilterProxyModel):
    """Proxy model that hides files with unsupported extensions."""

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)

        file_info = source_model.fileInfo(index)
        if file_info.isDir():
            return True

        ext = os.path.splitext(file_info.fileName())[1].lower()
        return ext in SUPPORTED_EXTENSIONS
```

This uses `QSortFilterProxyModel` wrapping `QFileSystemModel` instead of subclassing `QFileSystemModel` directly. The proxy approach is cleaner: the base model handles all filesystem watching/caching, and the proxy purely handles filtering.

- [ ] **Step 2: Commit**

```bash
git add krita_file_browser/file_system_model.py
git commit -m "feat: add FileFilterProxyModel with supported extension filter"
```

---

### Task 3: File Operations Module

**Files:**
- Create: `krita_file_browser/file_operations.py`

- [ ] **Step 1: Create file operations module**

Create `krita_file_browser/file_operations.py`:

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add krita_file_browser/file_operations.py
git commit -m "feat: add file operations module (open, create, delete)"
```

---

### Task 4: Search Worker Thread

**Files:**
- Create: `krita_file_browser/search_worker.py`

- [ ] **Step 1: Create the background search worker**

Create `krita_file_browser/search_worker.py`:

```python
import os

from PyQt5.QtCore import QThread, pyqtSignal


SUPPORTED_EXTENSIONS = {
    ".kra", ".krz",
    ".ora", ".psd", ".xcf", ".svg",
    ".png", ".jpg", ".jpeg", ".gif",
    ".tif", ".tiff", ".bmp",
    ".exr", ".webp", ".heif", ".heic",
    ".jp2", ".jxl", ".tga", ".hdr", ".pdf",
}


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
                return
            for filename in filenames:
                if self._cancelled:
                    return
                if self.query in filename.lower():
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        results.append(os.path.join(dirpath, filename))
        self.results_ready.emit(results)

    def cancel(self):
        self._cancelled = True
```

- [ ] **Step 2: Commit**

```bash
git add krita_file_browser/search_worker.py
git commit -m "feat: add SearchWorker thread for recursive file search"
```

---

### Task 5: Docker UI — Toolbar, Tree View, and Status Bar

**Files:**
- Modify: `krita_file_browser/file_browser_docker.py` (replace stub from Task 1)

This is the main task. The Docker builds the full UI: toolbar with buttons and search input, a QStackedWidget holding the tree view and search result list, and a status bar label. It wires all events.

- [ ] **Step 1: Implement the full FileBrowserDocker**

Replace `krita_file_browser/file_browser_docker.py` with the full implementation:

```python
import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from krita import DockWidget, Krita

from .file_operations import create_file, delete_file, open_file
from .file_system_model import FileFilterProxyModel
from .search_worker import SearchWorker


class FileBrowserDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Browser")
        self._root_path = ""
        self._search_worker = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)

        self._build_ui()
        self._connect_signals()
        self._load_last_path()

    def _build_ui(self):
        main_widget = QWidget(self)
        self.setWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Toolbar ---
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(4, 4, 4, 4)
        toolbar_layout.setSpacing(4)

        self._btn_open = QPushButton("Open")
        self._btn_new = QPushButton("New")
        self._btn_delete = QPushButton("Del")
        self._btn_refresh = QPushButton("Refresh")

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search files...")

        for btn in (self._btn_open, self._btn_new, self._btn_delete, self._btn_refresh):
            toolbar_layout.addWidget(btn)
        toolbar_layout.addWidget(self._search_input, stretch=1)

        layout.addWidget(toolbar)

        # --- Stacked widget: tree view + search results ---
        self._stack = QStackedWidget()

        # Tree view
        self._tree = QTreeView()
        self._tree.setHeaderHidden(True)
        self._fs_model = None
        self._proxy_model = FileFilterProxyModel()
        self._tree.setModel(self._proxy_model)
        self._tree.doubleClicked.connect(self._on_tree_double_click)
        self._tree.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._stack.addWidget(self._tree)

        # Search results list
        self._search_list = QListWidget()
        self._search_list.itemDoubleClicked.connect(self._on_search_result_double_click)
        self._stack.addWidget(self._search_list)

        layout.addWidget(self._stack, stretch=1)

        # --- Status bar ---
        self._status_label = QLabel("No directory open")
        self._status_label.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(self._status_label)

        # Delete starts disabled (nothing selected)
        self._btn_delete.setEnabled(False)

    def _connect_signals(self):
        self._btn_open.clicked.connect(self._on_open_directory)
        self._btn_new.clicked.connect(self._on_new_file)
        self._btn_delete.clicked.connect(self._on_delete_file)
        self._btn_refresh.clicked.connect(self._on_refresh)
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_timer.timeout.connect(self._start_search)

    # --- Path management ---

    def _set_root_path(self, path):
        if not path or not os.path.isdir(path):
            self._status_label.setText("Directory not accessible")
            return

        self._root_path = path

        # Lazily create QFileSystemModel (must be created after QApplication exists)
        if self._fs_model is None:
            from PyQt5.QtWidgets import QFileSystemModel
            self._fs_model = QFileSystemModel()
            self._fs_model.setFilter(QFileSystemModel.AllDirs | QFileSystemModel.Files | QFileSystemModel.NoDotAndDotDot)
            self._proxy_model.setSourceModel(self._fs_model)

        self._fs_model.setRootPath(path)
        root_index = self._fs_model.index(path)
        proxy_root = self._proxy_model.mapFromSource(root_index)
        self._tree.setRootIndex(proxy_root)

        self._status_label.setText(path)
        Krita.instance().writeSetting("krita_file_browser", "last_path", path)

    def _load_last_path(self):
        path = Krita.instance().readSetting("krita_file_browser", "last_path", "")
        if path and os.path.isdir(path):
            self._set_root_path(path)

    # --- Toolbar actions ---

    def _on_open_directory(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            self._root_path or "",
        )
        if path:
            self._search_input.clear()
            self._set_root_path(path)

    def _on_new_file(self):
        if not self._root_path:
            return
        target_dir = self._get_selected_directory()
        create_file(target_dir, parent=self)

    def _on_delete_file(self):
        filepath = self._get_selected_file()
        if not filepath:
            return
        if delete_file(filepath, parent=self):
            self._status_label.setText(f"Deleted: {os.path.basename(filepath)}")

    def _on_refresh(self):
        if self._root_path:
            self._set_root_path(self._root_path)

    # --- Selection helpers ---

    def _get_selected_file(self):
        """Return the filepath of the currently selected item, or None if it's a directory."""
        indexes = self._tree.selectionModel().selectedIndexes()
        if not indexes:
            return None
        source_index = self._proxy_model.mapToSource(indexes[0])
        file_info = self._fs_model.fileInfo(source_index)
        if file_info.isDir():
            return None
        return file_info.absoluteFilePath()

    def _get_selected_directory(self):
        """Return the directory that should be used for new file creation:
        if a directory is selected, use it; otherwise use root_path."""
        indexes = self._tree.selectionModel().selectedIndexes()
        if indexes:
            source_index = self._proxy_model.mapToSource(indexes[0])
            file_info = self._fs_model.fileInfo(source_index)
            if file_info.isDir():
                return file_info.absoluteFilePath()
        return self._root_path

    def _on_selection_changed(self):
        filepath = self._get_selected_file()
        self._btn_delete.setEnabled(filepath is not None)
        if filepath:
            self._status_label.setText(filepath)
        elif self._root_path:
            self._status_label.setText(self._root_path)

    # --- Tree double click ---

    def _on_tree_double_click(self, index):
        source_index = self._proxy_model.mapToSource(index)
        file_info = self._fs_model.fileInfo(source_index)
        if not file_info.isDir():
            open_file(file_info.absoluteFilePath(), parent=self)

    # --- Search ---

    def _on_search_text_changed(self, text):
        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.wait()

        if not text.strip():
            self._stack.setCurrentWidget(self._tree)
            return

        self._search_timer.start()

    def _start_search(self):
        query = self._search_input.text().strip()
        if not query or not self._root_path:
            return

        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.cancel()
            self._search_worker.wait()

        self._search_list.clear()
        self._stack.setCurrentWidget(self._search_list)
        self._status_label.setText("Searching...")

        self._search_worker = SearchWorker(self._root_path, query)
        self._search_worker.results_ready.connect(self._on_search_results)
        self._search_worker.start()

    def _on_search_results(self, results):
        self._search_list.clear()
        for filepath in results:
            item = QListWidgetItem(os.path.basename(filepath))
            item.setData(Qt.UserRole, filepath)
            item.setToolTip(filepath)
            self._search_list.addItem(item)

        count = len(results)
        self._status_label.setText(f"{count} file{'s' if count != 1 else ''} found")

    def _on_search_result_double_click(self, item):
        filepath = item.data(Qt.UserRole)
        if filepath:
            open_file(filepath, parent=self)

    # --- Docker interface ---

    def canvasChanged(self, canvas):
        pass
```

- [ ] **Step 2: Commit**

```bash
git add krita_file_browser/file_browser_docker.py
git commit -m "feat: implement FileBrowserDocker with toolbar, tree view, search, and status bar"
```

---

### Task 6: Final Integration & Commit

**Files:**
- Modify: `krita_file_browser/__init__.py` (verify it imports correctly)

This task verifies the full plugin structure is consistent and all imports resolve correctly, then makes a final integration commit.

- [ ] **Step 1: Verify __init__.py is correct**

The `__init__.py` from Task 1 should already contain:

```python
from krita import DockWidgetFactory, DockWidgetFactoryBase
from .file_browser_docker import FileBrowserDocker

Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "fileBrowser",
        DockWidgetFactoryBase.DockRight,
        FileBrowserDocker,
    )
)
```

Verify the import works: `from .file_browser_docker import FileBrowserDocker` must resolve given that `file_browser_docker.py` exists and defines the class. No changes needed if it matches.

- [ ] **Step 2: Verify file structure matches spec**

Run: `ls -R krita_file_browser/`

Expected output:
```
krita_file_browser/:
__init__.py
file_browser_docker.py
file_operations.py
file_system_model.py
search_worker.py
```

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: integration adjustments for final plugin structure"
```

If no changes needed, skip this step.

---

## Self-Review Checklist

After all tasks are complete, verify against the spec:

| Spec Requirement | Covered By |
|---|---|
| Browse directory tree with supported file types | Task 2 (filter model) + Task 5 (tree view) |
| Open files in Krita via double-click | Task 3 (`open_file`) + Task 5 (`_on_tree_double_click`) |
| Create new .kra files in current directory | Task 3 (`create_file`) + Task 5 (`_on_new_file`) |
| Delete files with confirmation | Task 3 (`delete_file`) + Task 5 (`_on_delete_file`) |
| Delete button disabled for directories | Task 5 (`_on_selection_changed`) |
| Recursive file search | Task 4 (`SearchWorker`) + Task 5 (`_start_search`) |
| Search results in flat list | Task 5 (`QStackedWidget` + `QListWidget`) |
| Remember last opened directory | Task 5 (`_load_last_path` + `writeSetting`) |
| Plugin registration files | Task 1 (`.desktop` + `.action`) |
| Dev install script | Task 1 (`install.ps1`) |
