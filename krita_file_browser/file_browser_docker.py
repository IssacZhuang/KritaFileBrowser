import os

from PyQt5.QtCore import Qt, QTimer, QDir
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStackedWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from krita import DockWidget, Krita

from .file_operations import create_file, create_folder, delete_file, open_file
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

        self._btn_open = QPushButton("Open Folder")
        self._btn_refresh = QPushButton("Refresh")

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search files...")

        for btn in (self._btn_open, self._btn_refresh):
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

    def _connect_signals(self):
        self._btn_open.clicked.connect(self._on_open_directory)
        self._btn_refresh.clicked.connect(self._on_refresh)
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_timer.timeout.connect(self._start_search)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)

    # --- Path management ---

    def _set_root_path(self, path):
        if not path or not os.path.isdir(path):
            self._status_label.setText("Directory not accessible")
            return

        self._root_path = path

        # QFileSystemModel must be created after QApplication is running,
        # so we defer it to first use rather than __init__
        if self._fs_model is None:
            from PyQt5.QtWidgets import QFileSystemModel
            self._fs_model = QFileSystemModel()
            self._fs_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
            self._proxy_model.setSourceModel(self._fs_model)

            # Hide columns after source model is attached
            for col in range(1, 4):
                self._tree.hideColumn(col)

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

    def _on_refresh(self):
        if self._root_path:
            self._set_root_path(self._root_path)

    # --- Context menu ---

    def _on_context_menu(self, pos):
        if self._fs_model is None or not self._root_path:
            return

        index = self._tree.indexAt(pos)
        menu = QMenu(self)

        source_index = None
        is_dir = False
        is_root = False

        if index.isValid():
            source_index = self._proxy_model.mapToSource(index)
            file_info = self._fs_model.fileInfo(source_index)
            is_dir = file_info.isDir()
            is_root = (file_info.absoluteFilePath() == self._root_path)

        if is_dir:
            menu.addAction("New .kra File", self._on_new_file)
            menu.addAction("New Folder", self._on_new_folder)

        if index.isValid():
            if is_dir:
                menu.addSeparator()
            rename_action = menu.addAction("Rename", lambda checked=False, idx=index: self._tree.edit(idx))
            rename_action.setEnabled(not is_root)
            menu.addAction("Delete", lambda checked=False, si=source_index: self._on_delete_item(si))
        elif not index.isValid():
            menu.addAction("New .kra File", self._on_new_file)
            menu.addAction("New Folder", self._on_new_folder)

        if menu.actions():
            menu.exec_(self._tree.viewport().mapToGlobal(pos))

    def _on_new_folder(self):
        if not self._root_path:
            return
        target_dir = self._get_selected_directory()
        if create_folder(target_dir, parent=self):
            self._status_label.setText(f"Folder created in: {target_dir}")

    def _on_delete_item(self, source_index):
        if source_index is None or not source_index.isValid():
            return
        filepath = self._fs_model.filePath(source_index)
        if delete_file(filepath, parent=self):
            self._status_label.setText(f"Deleted: {os.path.basename(filepath)}")

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
        """Return the directory for new file creation: selected dir or root_path."""
        indexes = self._tree.selectionModel().selectedIndexes()
        if indexes:
            source_index = self._proxy_model.mapToSource(indexes[0])
            file_info = self._fs_model.fileInfo(source_index)
            if file_info.isDir():
                return file_info.absoluteFilePath()
        return self._root_path

    def _on_selection_changed(self):
        filepath = self._get_selected_file()
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
            self._search_worker.wait(100)

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
            self._search_worker.wait(100)

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
