# engine.spec — PyInstaller build of the MA Grader engine (cli.py).
#
# Produces a self-contained "ma-grader-engine" folder (onedir) that runs the
# grading pipeline with NO Python installed on the target machine. The desktop
# app (Electron) launches the bundled binary as its sidecar.
#
# Build (run from the repo root, ma_grader/):
#     pyinstaller --noconfirm \
#         --distpath desktop/engine \
#         --workpath desktop/build/pyi \
#         engine.spec
#
# The same spec is used on every OS (Windows / macOS) — PyInstaller produces a
# native binary for whichever machine it runs on, which is why the GitHub
# Actions workflow builds it on both a windows-latest and a macos-latest runner.

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = os.path.abspath(os.getcwd())  # repo root — pyinstaller is invoked from here

# --- Code: pull in every submodule of the engine packages -------------------
# Most graders are reached via static imports, but collecting submodules makes
# the freeze robust against any import that the analyzer can't trace statically.
hiddenimports = []
for pkg in ("graders", "orchestrator", "writers", "utilities"):
    hiddenimports += collect_submodules(pkg)

# --- Data: non-.py files the engine reads at runtime ------------------------
# Grading-sheet templates, feedback JSON, and the data files some graders load
# relative to their own module (cpi_monthly.json, mortgage_rates.json).
datas = [
    ("assets_templates", "assets_templates"),
    ("assets_feedback", "assets_feedback"),
    ("graders/ma2_income_projection/cpi_monthly.json", "graders/ma2_income_projection"),
    ("graders/ma2_student_loans/mortgage_rates.json", "graders/ma2_student_loans"),
]
# python-docx ships default template XML it needs when opening documents.
datas += collect_data_files("docx")

a = Analysis(
    ["cli.py"],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Trim things the engine never uses to keep the bundle small.
    excludes=["tkinter", "matplotlib", "pytest", "PIL.ImageTk"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ma-grader-engine",
    console=True,           # headless CLI sidecar — no GUI window
    disable_windowed_traceback=False,
    strip=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ma-grader-engine",
)
