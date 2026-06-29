# Building the MA Grader macOS app

This produces a real, double-clickable **MA Grader.app** (and a `.dmg` installer)
that runs on your Mac. It bundles the grading engine's source and a Python
environment with all dependencies, so you don't touch the `.venv` to run it.

> Scope: this build runs on **your Mac** (and Macs that have Python 3 installed).
> A fully standalone build that needs *no* Python on the target machine is a
> later step (PyInstaller) — see "Going fully portable" below.

## One-time prerequisites

- Node + npm (already used for `npm run dev`)
- Python 3 (already installed — it's what your `.venv` uses)
- Dependencies installed once: from the `desktop/` folder, `npm install`

## Build it

```bash
cd ~/Desktop/ma_grader/desktop
npm run app
```

That runs three steps automatically:
1. Builds the UI.
2. Stages the engine — copies the Python source into `engine-src/` and builds a
   self-contained venv into `pyengine/` (installs `requirements.txt`).
3. Packages the macOS app with electron-builder.

When it finishes, look in **`desktop/release/`**:
- `MA Grader-0.1.0.dmg` — the installer (drag to Applications)
- `mac/MA Grader.app` — the app itself

## First launch (unsigned app)

Because this build isn't code-signed yet, macOS will warn the first time:
**right-click the app → Open → Open**. After that it launches normally.

## Going fully portable (later)

To share with coworkers who may not have Python, we freeze the engine with
PyInstaller so nothing external is required, then sign + notarize with your
Apple Developer ID so it opens with no warning. That's a follow-up once this
local build is confirmed working.

## Troubleshooting

- If `npm run app` stops during step 3, copy the error — it's usually an
  electron-builder or signing setting, quick to fix.
- To re-run just the engine staging: `npm run stage:engine`.
- The staged `engine-src/` and `pyengine/` are rebuilt each time and are
  git-ignored.
