from krita import DockWidgetFactory, DockWidgetFactoryBase
from .file_browser_docker import FileBrowserDocker

Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "fileBrowser",
        DockWidgetFactoryBase.DockRight,
        FileBrowserDocker,
    )
)
