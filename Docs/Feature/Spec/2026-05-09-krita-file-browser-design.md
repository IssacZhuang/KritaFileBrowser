# Krita File Browser Plugin - Design Spec

**Date:** 2026-05-09
**Status:** Approved
**Approach:** QTreeView + QFileSystemModel (Approach A)

## Overview

A Krita Python plugin that provides a VSCode-like file browser as a Docker panel. Users can browse directories, open supported files in Krita, create new .kra files, delete files, and search files recursively.

## Architecture

### Plugin Structure

```
krita_file_browser.desktop    # Plugin registration
krita_file_browser.action     # Keyboard shortcut definitions
krita_file_browser/           # Plugin module directory
├── __init__.py               # Module entry: from .file_browser_docker import *
├── file_browser_docker.py    # DockWidget subclass, main UI
├── file_system_model.py      # Custom QFileSystemModel with file type filter
├── file_operations.py        # File operations (new, delete, open)
└── search_worker.py          # Background search thread (QThread)
```

### Component Diagram

```
┌─────────────────────────────────────┐
│  FileBrowserDocker (DockWidget)     │
│  ┌───────────────────────────────┐  │
│  │ QToolBar                      │  │
│  │ [Open] [New] [Del] [Refresh]  │  │
│  │ [Search: ________________ ]   │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ QTreeView / QListWidget       │  │
│  │ (tree for browsing, list for  │  │
│  │  search results, stacked)     │  │
│  │                               │  │
│  │ 📁 subfolder/                 │  │
│  │   📄 image.png                │  │
│  │   📄 drawing.kra              │  │
│  │ 📄 photo.jpg                  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ QLabel (status bar)           │  │
│  │ "C:\Art | 42 files"          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Supported File Formats

The plugin filters the directory view to show only these extensions:

```python
SUPPORTED_EXTENSIONS = {
    '.kra', '.krz',       # Krita native
    '.ora',                # OpenRaster
    '.psd',                # Photoshop
    '.xcf',                # GIMP
    '.svg',                # SVG vector
    '.png', '.jpg', '.jpeg', '.gif',
    '.tif', '.tiff',       # TIFF
    '.bmp',                # Bitmap
    '.exr',                # OpenEXR
    '.webp',               # WebP
    '.heif', '.heic',      # HEIF
    '.jp2',                # JPEG 2000
    '.jxl',                # JPEG XL
    '.tga',                # Targa
    '.hdr',                # RGBE/HDR
    '.pdf',                # PDF
}
```

Subdirectories are always shown (needed for tree navigation) even if they contain no supported files.

## User Interaction Flows

### Opening a Directory

1. User clicks "Open Directory" button in toolbar
2. `QFileDialog.getExistingDirectory()` (PyQt5) opens a directory picker
3. Selected path becomes the tree root via `QFileSystemModel.setRootPath()`
4. Path is persisted via `Application.writeSetting("krita_file_browser", "last_path", path)`
5. On next launch, the plugin auto-loads the last opened directory

### Browsing Files

1. Tree shows directory structure with supported files only
2. Directories can be expanded/collapsed
3. Single click selects a file (shows filename in status bar)
4. Double click opens the file in Krita via `Application.openDocument(path)`

### Creating a New File

1. User clicks "New" button
2. A `QInputDialog` prompts for filename (default: "Untitled.kra")
3. Plugin creates a new document with fixed defaults (no customization dialog — YAGNI): `Application.createDocument(1920, 1080, name, "RGBA", "U8", "", 150.0)`
4. Displays the document: `Application.activeWindow().addView(doc)`
5. Saves to current directory: `doc.saveAs(os.path.join(current_dir, filename))`
6. File tree refreshes automatically (QFileSystemModel watches the filesystem)

### Deleting a File

1. User selects a file in the tree and clicks "Delete" button. The Delete button is disabled when a directory is selected — only files can be deleted, not directories.
2. Confirmation dialog: `QMessageBox.question("Delete file?", filename)`
3. If confirmed: `os.remove(filepath)`
4. File tree refreshes automatically

### Searching Files

1. User types in the search box
2. Search triggers after a 300ms debounce (QTimer singleShot)
3. A `SearchWorker` (QThread) recursively walks the current root directory
4. Matching file paths are emitted via `pyqtSignal(list)` back to the main thread
5. Results are displayed in a flat `QListWidget` that replaces the tree view during active search
6. User can click a search result to open the file in Krita
7. Clearing the search box restores the normal tree view

## Key Technical Decisions

### QFileSystemModel vs Manual Tree

Using `QFileSystemModel` because:
- Built-in lazy loading (only loads visible nodes)
- Built-in filesystem watching (auto-refreshes when files change)
- Built-in sorting and filtering
- Much less code to maintain

### Background Search

Search uses a `QThread` worker to avoid blocking the UI. The worker:
- Walks the directory tree using `os.walk()`
- Filters files by supported extensions and name match
- Emits results as a list via signal
- Supports cancellation (checked each directory iteration)

### Settings Persistence

Using Krita's built-in settings API:
- `Application.writeSetting("krita_file_browser", key, value)` to save
- `Application.readSetting("krita_file_browser", key, default)` to load

Settings stored:
- `last_path`: Last opened directory path
- `window_geometry`: Docker panel size (optional, future)

## Error Handling

| Scenario | Handling |
|----------|----------|
| File open fails | `QMessageBox.critical()` with error message |
| Directory not accessible | Status bar shows "Cannot access directory" |
| New file name conflict | `QMessageBox.warning()` - file already exists |
| Delete fails (in use) | `QMessageBox.critical()` with OS error |
| Search on empty directory | Show "No files found" in status bar |

## Krita API Usage

| Operation | API Call |
|-----------|----------|
| Open file | `Application.openDocument(path)` |
| Create document | `Application.createDocument(1920, 1080, name, "RGBA", "U8", "", 150.0)` |
| Display document | `Application.activeWindow().addView(doc)` |
| Save document | `doc.saveAs(path)` |
| Save setting | `Application.writeSetting("krita_file_browser", key, value)` |
| Read setting | `Application.readSetting("krita_file_browser", key, default)` |
| Pick directory | `QFileDialog.getExistingDirectory()` |

## Plugin Registration

### krita_file_browser.desktop

```ini
[Desktop Entry]
Type=Service
ServiceTypes=Krita/PythonPlugin
X-KDE-Library=krita_file_browser
X-Python-2-Compatible=false
Name=File Browser
Comment=A VSCode-like file browser for browsing and opening files in Krita.
```

### krita_file_browser.action

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

## Scope and Non-Goals

### In Scope
- Browse directory tree with supported file types
- Open files in Krita via double-click
- Create new .kra files in current directory
- Delete files with confirmation
- Recursive file search
- Remember last opened directory

### Out of Scope (YAGNI)
- File rename
- Drag and drop
- File thumbnails/previews
- Copy/move files
- Customizable file type filters
- Multi-directory bookmarks
- Template-based new file creation
- Recent files list

## Related Skills & Docs

- Krita Python Plugin Howto: https://docs.krita.org/en/user_manual/python_scripting/krita_python_plugin_howto.html
- Krita API Reference: https://api.kde.org/krita/html/namespaceKrita.html
- PyQt5 QTreeView: https://doc.qt.io/qt-5/qtreeview.html
- PyQt5 QFileSystemModel: https://doc.qt.io/qt-5/qfilesystemmodel.html
