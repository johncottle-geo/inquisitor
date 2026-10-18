#!/bin/bash
# Builds the auto-updating Inquisitor.app shell on a Mac.
# Needs a fine-grained read-only GitHub token for this repo (Contents: read).
# Give it as INQUISITOR_TOKEN, or save it in a file named token.txt next to this script
# (token.txt is git-ignored), or paste it when asked.
set -e
cd "$(dirname "$0")"
TOKEN="${INQUISITOR_TOKEN:-}"
[ -z "$TOKEN" ] && [ -f token.txt ] && TOKEN=$(tr -d '[:space:]' < token.txt)
if [ -z "$TOKEN" ]; then
  read -rsp "Paste the read-only GitHub token for the inquisitor repo: " TOKEN; echo
fi
[ -z "$TOKEN" ] && { echo "No token given."; exit 1; }

python3 -m venv .venv_build
source .venv_build/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
rm -rf build dist main_build.py
python3 - "$TOKEN" <<'PY'
import sys
s = open("main.py", encoding="utf-8").read()
open("main_build.py", "w", encoding="utf-8").write(s.replace("@@TOKEN_PLACEHOLDER@@", sys.argv[1]))
PY
pyinstaller --noconfirm --windowed --name Inquisitor \
  --icon inquisitor.icns \
  --add-data "inquisitor_icon_1024.png:." \
  --exclude-module vit_processor \
  --hidden-import PyQt6.sip \
  --collect-all pyqtgraph --collect-all scipy --collect-all sklearn --collect-all pandas \
  --collect-data certifi \
  main_build.py
rm -f main_build.py
echo; echo "Built: $(pwd)/dist/Inquisitor.app  (first launch: right-click, Open)"
