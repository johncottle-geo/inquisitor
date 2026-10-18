"""
Run this after editing vit_processor.py and
before pushing to GitHub. It bumps manifest.json's version string to
today's date (plus a counter if you've already bumped it today), so every
running copy of Inquisitor picks up the change on its next launch.

Usage:  python bump_version.py
Then:   git add -A && git commit -m "..." && git push
"""
import json
import datetime
import os

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    today = datetime.date.today().strftime("%Y.%m.%d")
    old_version = manifest.get("version", "")
    if old_version.startswith(today):
        # Already bumped today -- increment the trailing counter.
        try:
            counter = int(old_version.rsplit(".", 1)[1]) + 1
        except (IndexError, ValueError):
            counter = 1
    else:
        counter = 1
    new_version = "{}.{}".format(today, counter)

    manifest["version"] = new_version
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print("manifest.json version: {} -> {}".format(old_version or "(none)", new_version))
    print("Now commit and push manifest.json plus whatever files you changed.")


if __name__ == "__main__":
    main()
