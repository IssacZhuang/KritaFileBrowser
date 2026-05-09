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
