# Krita 文件浏览器

一个类似 VSCode 文件浏览器的 Krita 插件。在 Krita 中直接浏览目录、打开/新建/删除文件、搜索文件。

![预览](Preview.png)

## 功能

- **目录浏览** — 打开任意目录，以树形结构浏览受支持的图片文件
- **快捷操作** — 新建 `.kra` 文件（可自定义宽高/分辨率/色彩设置）、删除文件、双击打开文件
- **递归搜索** — 按文件名在所有子目录中搜索
- **自动恢复** — 记住上次打开的目录，下次启动自动加载

## 支持的格式

`.kra` `.krz` `.ora` `.psd` `.xcf` `.svg` `.png` `.jpg` `.jpeg` `.gif` `.tif` `.tiff` `.bmp` `.exr` `.webp` `.heif` `.heic` `.jp2` `.jxl` `.tga` `.hdr` `.pdf`

## 安装

1. 下载或克隆本仓库
2. 找到 Krita 资源文件夹：Krita → 设置 → 管理资源 → 打开资源文件夹
3. 在其中找到 `pykrita` 子目录
4. 将 `krita_file_browser.desktop` 和 `krita_file_browser/` 文件夹复制到 `pykrita/` 中
5. 在 `pykrita/` 下创建 `actions/` 文件夹（如不存在），将 `krita_file_browser.action` 复制进去
6. 重启 Krita
7. 进入 **设置 → 配置 Krita → Python 插件管理器**，找到 "File Browser" 并启用
8. 再次重启 Krita
9. 进入 **Settings → Dockers**（中文版：**设置 → 面板列表**），勾选 **File Browser** 显示面板

### 快速安装（Windows PowerShell）

```powershell
$src = "C:\path\to\KritaFileBrowser"       # 改为你的克隆路径
$dst = Join-Path $env:APPDATA "krita\pykrita"

Copy-Item "$src\krita_file_browser.desktop" $dst
Copy-Item -Recurse "$src\krita_file_browser" $dst
$actionsDir = Join-Path $dst "actions"
New-Item -ItemType Directory -Path $actionsDir -Force | Out-Null
Copy-Item "$src\krita_file_browser.action" $actionsDir
```

## 使用方法

- **打开目录** — 点击 "Open" 按钮选择文件夹
- **打开文件** — 双击树中的文件
- **新建文件** — 点击 "New"，设置文件名/宽高/分辨率/色彩参数，点击 OK
- **删除文件** — 选中文件，点击 "Del"，确认删除
- **搜索** — 在搜索框输入关键词，显示所有子目录的匹配结果
- **清除搜索** — 清空搜索框回到树形视图

## 许可证

[MIT](LICENSE)
