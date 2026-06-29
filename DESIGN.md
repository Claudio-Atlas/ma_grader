# MA Grader — Design Document

_Last updated: June 2026_

This document describes the MA Grader desktop application: what it is, how it
is built, what we validated, the known issues we should fix, and the plan for
signing and distributing it to coworkers.

---

## 1. Goal

Turn the existing `ma_grader` Python engine — which already grades MAT-144
Major Assignment spreadsheets (MA1, MA2, MA3) in batch — into a polished,
cross-platform desktop app. An instructor drops a ZIP of student submissions,
picks the assignment, and gets graded workbooks plus an instructor master
sheet, with no command line and no Python installation.

---

## 2. What we validated

Before designing the wrapper, the engine was run end-to-end against three real
Canvas submission ZIPs:

| Assignment | Students graded | Time   | Notes                                              |
| ---------- | --------------- | ------ | -------------------------------------------------- |
| MA1        | 19 / 19         | ~1.6 s | Currency tab calls a live exchange-rate API        |
| MA2        | 13 / 13         | ~20 s  | 4 students submitted no .xlsx (silently skipped)   |
| MA3        | 17 / 17         | ~12 s  | Reads charts; essay flagged for manual grading     |

The grading logic is sound: score distributions are realistic, weak
submissions correctly scored low, and Excel-Online formulas read cleanly
through `openpyxl`. The engine depends only on `openpyxl`, `requests`, and
`urllib3` — all pure Python, which makes it easy to freeze into a standalone
binary.

---

## 3. Architecture

Three layers, shipped as one signed app:

```
┌─────────────────────────────────────────────────────────┐
│ 1 · Renderer (React + Tailwind, Chromium)                │
│     drop zip · course + assignment · live progress       │
│     results table · (future) manual-grading panel        │
│     No Node, no filesystem, no shell access.             │
├─────────────────────────────────────────────────────────┤
│ 2 · Main process (Electron / Node)                       │
│     windows · native dialogs · spawns the engine         │
│     secure IPC bridge via preload (contextIsolation)     │
├─────────────────────────────────────────────────────────┤
│ 3 · Sidecar (the Python engine, frozen by PyInstaller)   │
│     cli.py → web_adapter.grade_zip → graders/writers     │
│     emits NDJSON progress + result on stdout             │
└─────────────────────────────────────────────────────────┘
                         │ writes
                         ▼
        Workspace on disk: graded_output/*.xlsx,
        INSTRUCTOR_MASTER.xlsx
```

### Process model: one-shot subprocess

Each grading run, the main process spawns the engine like a command and reads
its stdout. This avoids a long-lived local server, ports, and lifecycle bugs,
and maps directly onto the engine's existing `grade_zip` entry point. If we
later want interactive re-grading we can move to a persistent local server,
but it is not needed now.

### The NDJSON protocol

`cli.py` writes one JSON object per line to stdout. The reserved stdout is used
**only** for these events; any stray `print()` inside the engine is redirected
to stderr so it cannot corrupt the stream.

```
{"type": "start",    "total": null}
{"type": "progress", "current": 3, "total": 17, "student": "Jane_Doe"}
{"type": "result",   "data": { ...full grade_zip dict... }}
{"type": "error",    "message": "..."}
```

Per-student progress is produced by an optional `progress_callback` threaded
through `web_adapter.grade_zip` into the three phase-1 orchestrators. These
are additive hooks — no grading logic was changed.

### Security posture

The renderer runs with `contextIsolation: true`, `nodeIntegration: false`, and
`sandbox: true`. It can only call the small, explicit API exposed in
`preload.js` (`pickZip`, `pickFolder`, `openPath`, `runGrading`,
`onGradeEvent`). It never touches the filesystem or spawns processes directly.

---

## 4. Must-fix list (engine)

These are correctness and robustness issues found during review and live
testing. None block a first build, but they affect real student grades.

1. **Cache currency exchange rates (highest priority).** The MA1 currency tab
   fetches live rates from `open.er-api.com`. When the network is blocked
   (e.g. a locked-down campus network), every student silently loses the
   exchange-rate-accuracy points and a raw Python stack-trace string is
   written into their feedback. Grading also becomes non-reproducible — the
   same file can score differently on different days. Fix: fetch once, cache a
   dated snapshot per assignment, fall back to the cached snapshot offline,
   and never write an exception string into student feedback.

2. **Surface "no submission" students.** Students who submit only a .docx/.pdf
   and no .xlsx are currently skipped with only a log line and never appear in
   results. They should appear as an explicit "not submitted / needs manual
   review" row so nobody is missed.

3. **Drop the `sys.path` hijack.** `web_adapter._setup_ma_imports()` works
   around a package-name collision from the old web app. It is unnecessary in
   the standalone sidecar and should be removed once the app is the only
   caller.

4. **Remove the security-risk SSL bypass.** The currency fetch retries with
   `verify=False` when SSL fails. Once rates are cached this fallback can go.

5. **Reduce per-assignment duplication.** The `row26/27/28/29_checker_v2.py`
   files are near-identical; the MA2 graders use free-form comment strings
   while MA1/MA3 use the structured feedback-code system. Unifying these makes
   the engine easier to maintain but is not urgent.

6. **Add a golden-file test suite.** A handful of known submissions with
   expected scores would let us refactor the above safely. There are currently
   no automated tests.

---

## 5. Signing and distribution

Distribution and trust are two independent decisions.

**Hosting:** GitHub Releases, free. Installers (`.dmg`, `.exe`) are uploaded
there and coworkers download directly. This also supports auto-update later
via `electron-updater`.

**Trust (removing OS warnings):**

- **macOS** — sign and notarize with the existing Apple Developer ID. No extra
  cost beyond the membership already held. Result: no Gatekeeper warning.
- **Windows** — Azure Artifact Signing (formerly Trusted Signing): about
  **$9.99/month**, open to individual US developers, no hardware token, and it
  gives instant SmartScreen reputation (no warning period). It integrates with
  electron-builder. Requires a **paid** Azure subscription. The charge is
  pay-when-you-sign: a signed build is timestamped and stays trusted forever
  even after the subscription lapses, so for a tool released a few times a year
  you only need the subscription active in release months.
- **Unsigned Windows fallback** — perfectly usable for a handful of trusted
  coworkers: they click "More info → Run anyway" once per machine. Costs $0;
  the only downside is the one-time scary-looking prompt.

Recommended: host on GitHub Releases, sign+notarize macOS now (free), and
decide Windows signing by audience size — ship unsigned to start, add Azure
signing when it goes wider.

---

## 6. Build and run

See `desktop/README.md` for exact commands. In short:

- **Dev:** `cd desktop && npm install && npm run dev`
- **Freeze engine:** `pyinstaller --onedir --name ma-grader-engine … cli.py`
- **Package:** `cd desktop && npm run dist` → `release/`

Build macOS installers on a Mac and Windows installers on Windows;
electron-builder does not cross-compile the native shells.

---

## 7. Roadmap

**Now (this build):** drag-drop ZIP → grade → results, with live progress and
buttons to open the graded files and instructor master workbook.

**Next:**

1. Manual-grading panel for the MA3 written-analysis essay (lists flagged
   students, shows their response, takes a score, writes it back to the
   grading sheet).
2. Currency-rate caching (must-fix #1).
3. "Not submitted" rows (must-fix #2).
4. Per-run history and the ability to re-open a past batch.
5. Auto-update via GitHub Releases.
