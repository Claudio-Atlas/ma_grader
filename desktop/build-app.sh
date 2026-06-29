#!/bin/bash
# build-app.sh — build the MA Grader macOS app locally (for your own Mac).
# Produces an installable .dmg and a .app under desktop/release/.
#
# Requires: Node deps installed (npm install) and PyInstaller available on PATH
# (pip install -r ../requirements.txt pyinstaller==6.11.1 — ideally in ../.venv).
#
# NOTE: Official releases for BOTH Windows and macOS are built automatically by
# GitHub Actions (.github/workflows/build.yml). This script is just for quick
# local Mac builds.
set -e
cd "$(dirname "$0")"

echo "==> 1/3  Building the UI"
npm run build:ui

echo "==> 2/3  Freezing the Python engine (PyInstaller, self-contained)"
npm run freeze:engine

echo "==> 3/3  Packaging the macOS app (unsigned)"
npx electron-builder --mac

echo ""
echo "Done. Look in:  desktop/release/"
echo "  • MA Grader-<version>.dmg   (installer)"
echo "  • mac/MA Grader.app         (the app itself)"
echo ""
echo "First launch: right-click the app -> Open -> Open (to bypass the"
echo "unsigned-app warning, just once)."
