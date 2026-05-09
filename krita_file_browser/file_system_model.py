import os
from PyQt5.QtCore import QSortFilterProxyModel, Qt

from .constants import SUPPORTED_EXTENSIONS


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
