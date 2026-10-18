"""
Inquisitor -- entry point.

This is the thin shell that gets built into the Mac app. The real program,
vit_processor.py, lives in the private GitHub repo (inquisitor/ folder) and
is fetched on every launch, then cached. Pushing a new version to GitHub is
the whole update process, same as LAXative.

Dependencies bundled by build_mac.sh: PyQt6, pyqtgraph, numpy, scipy,
pandas, scikit-learn, certifi.
"""
from __future__ import annotations

import importlib
import json
import os
import ssl
import sys
import urllib.request
import urllib.error

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon

GITHUB_OWNER = "johncottle-geo"
GITHUB_REPO = "inquisitor"
GITHUB_BRANCH = "main"
# build_mac.sh fills this in at build time (never commit a real token).
GITHUB_TOKEN = "@@TOKEN_PLACEHOLDER@@"

# The program sits at the root of this repo.
REPO_SUBDIR = ""
MODULE_FILES = ["vit_processor.py"]

API_ROOT = "https://api.github.com/repos/{}/{}/contents".format(GITHUB_OWNER, GITHUB_REPO)
REQUEST_TIMEOUT = 30

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CONTEXT = ssl.create_default_context()


def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def cache_dir():
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.local/share")
    path = os.path.join(base, "Inquisitor")
    os.makedirs(path, exist_ok=True)
    return path


def _fetch_file_bytes(path):
    # The raw media type matters: the normal JSON response cuts off at 1 MB,
    # and vit_processor.py is bigger than that.
    url = "{}/{}?ref={}".format(API_ROOT, path, GITHUB_BRANCH)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + GITHUB_TOKEN,
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=_SSL_CONTEXT) as resp:
        return resp.read()


def _local_version(manifest_path):
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f).get("version")
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def check_and_update(status_callback=None):
    directory = cache_dir()
    manifest_path = os.path.join(directory, "manifest.json")
    local_version = _local_version(manifest_path)

    def note(msg):
        if status_callback:
            status_callback(msg)

    try:
        remote_manifest = json.loads(_fetch_file_bytes("manifest.json").decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError) as exc:
        note("Could not check for updates ({}); using the cached copy.".format(exc))
        if local_version is None:
            raise RuntimeError(
                "Inquisitor needs one successful internet connection to finish "
                "its first-time setup. Connect to the internet and try again.\n\n"
                "Details: {}".format(exc))
        return directory

    remote_version = remote_manifest.get("version")
    if remote_version == local_version:
        note("Up to date (version {}).".format(local_version))
        return directory

    note("Updating to version {}...".format(remote_version))
    try:
        for filename in remote_manifest.get("files", MODULE_FILES):
            content = _fetch_file_bytes(filename)
            tmp = os.path.join(directory, filename + ".part")
            with open(tmp, "wb") as f:
                f.write(content)
            os.replace(tmp, os.path.join(directory, filename))
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(remote_manifest, f)
        note("Updated to version {}.".format(remote_version))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            OSError) as exc:
        note("Update to {} failed ({}); using the cached copy.".format(
            remote_version, exc))
        if local_version is None:
            raise RuntimeError(
                "Could not download Inquisitor and no cached copy exists "
                "yet. Check your internet connection and try again.\n\n"
                "Details: {}".format(exc))
    return directory


_BG = "#141413"
_INK = "#F5F1E8"
_ACCENT = "#D9714E"


class _UpdateSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(380, 120)
        self.setStyleSheet("background: {};".format(_BG))
        row = QHBoxLayout(self)
        pm = QPixmap(resource_path("inquisitor_icon_1024.png"))
        if not pm.isNull():
            logo = QLabel()
            logo.setPixmap(pm.scaled(88, 88, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
            row.addWidget(logo)
        col = QVBoxLayout()
        title = QLabel("Inquisitor")
        title.setStyleSheet(
            "color: {}; font-size: 22px; font-weight: 800;".format(_INK))
        col.addWidget(title)
        self.status_label = QLabel("Checking for updates...")
        self.status_label.setStyleSheet(
            "color: {}; font-size: 12px;".format(_ACCENT))
        self.status_label.setWordWrap(True)
        col.addWidget(self.status_label)
        row.addLayout(col, 1)

    def set_status(self, text):
        self.status_label.setText(text)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon_file = resource_path("inquisitor_icon_1024.png")
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    splash = _UpdateSplash()
    splash.show()
    app.processEvents()

    try:
        directory = check_and_update(status_callback=splash.set_status)
        app.processEvents()
    except RuntimeError as exc:
        splash.close()
        QMessageBox.critical(None, "Inquisitor", str(exc))
        sys.exit(1)

    splash.close()

    # importlib on purpose, so PyInstaller does not try to bundle the module.
    # vit_processor.main() reuses the QApplication made above.
    sys.path.insert(0, directory)
    mod = importlib.import_module("vit_processor")
    mod.main()


if __name__ == "__main__":
    main()
