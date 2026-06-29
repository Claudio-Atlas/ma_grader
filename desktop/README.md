# MA Grader — Desktop App

A cross-platform (macOS + Windows) desktop wrapper around the existing
`ma_grader` Python grading engine. Drag in a submissions ZIP, pick the
assignment, and grade the whole class — no Python install required for end
users once it's packaged.

This folder is the Electron + React + Tailwind front end. The grading engine
itself lives one level up (`../`) and is reached through a thin command-line
bridge (`../cli.py`).

---

## How it fits together

```
ma_grader/                ← the Python engine (unchanged grading logic)
├── cli.py                ← NDJSON command bridge the app talks to
├── web_adapter.py        ← grade_zip(): the single entry point
├── graders/ writers/ …   ← existing grading code
└── desktop/              ← THIS app
    ├── electron/         ← main process, preload, sidecar spawn
    └── src/              ← React UI
```

The app spawns the engine once per grading job and reads newline-delimited
JSON (NDJSON) from its stdout to drive the live progress bar. See
`../DESIGN.md` for the full architecture and the NDJSON protocol.

---

## Prerequisites

- Node.js 18+ and npm
- Python 3.9+ on your PATH (dev only — end users won't need it)
- The engine's Python deps installed once, so dev runs work:
  ```bash
  cd ..
  python3 -m pip install -r requirements.txt
  ```

## Run it in development

```bash
cd desktop
npm install
npm run dev
```

`npm run dev` starts Vite (the UI dev server) and launches Electron pointed at
it, with hot reload on the React side.

## Build a local production bundle (no installer)

```bash
npm run start      # builds the UI, then runs Electron against the built files
```

## Package installers (.dmg / .exe)

Packaging needs the engine frozen into a standalone binary first (so users
don't need Python). From the repo root:

```bash
# 1) Freeze the engine (run on each target OS, or in CI)
python3 -m pip install pyinstaller
pyinstaller --onedir --name ma-grader-engine \
    --add-data "assets_templates:assets_templates" \
    --add-data "assets_feedback:assets_feedback" \
    cli.py
# → produces dist/ma-grader-engine/  (point package.json extraResources here:
#    we expect it copied to ../dist-engine/ma-grader-engine)

# 2) Build the app installer
cd desktop
npm run dist       # → release/  (.dmg on macOS, .exe on Windows)
```

> Build macOS installers on a Mac and Windows installers on Windows.
> electron-builder does not cross-compile the native shells.

## Signing (so coworkers don't see scary warnings)

- **macOS** — set your Apple Developer ID and notarization credentials; see
  `../DESIGN.md` → *Signing and distribution*.
- **Windows** — Azure Artifact Signing (formerly Trusted Signing), ~$10/mo,
  no hardware token. Optional; you can ship unsigned and click through the
  SmartScreen warning while testing.

---

## Project scripts

| Script           | What it does                                        |
| ---------------- | --------------------------------------------------- |
| `npm run dev`    | Vite dev server + Electron with hot reload          |
| `npm run start`  | Build UI, run Electron against the built files      |
| `npm run build:ui` | Build just the renderer to `dist/`                |
| `npm run dist`   | Build signed/packaged installers to `release/`      |
