# Inquisitor

Vitesse ToF LA-ICP-MS imaging processor (PyQt6 and pyqtgraph).

- `vit_processor.py` is the whole program. Pushing a new version here is the release.
- `manifest.json` carries the version. Run `python bump_version.py` before each push.
- `shell/` builds the thin Mac app that fetches `vit_processor.py` from this repo on every launch. Rebuild it only when `shell/main.py` changes.
