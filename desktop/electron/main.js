// main.js — Electron main process.
// Owns the window, native dialogs, and the bridge to the Python sidecar.
// The renderer never touches Node, the filesystem, or child processes directly;
// everything goes through the typed IPC channels below.

import { app, BrowserWindow, ipcMain, dialog, shell, safeStorage } from "electron";
import path from "node:path";
import os from "node:os";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import {
  runGrading,
  runGradingOne,
  inspectWorkbook,
  inspectGrade,
  updateGrade,
  inspectPaper,
  paperText,
  aiTestKey,
  aiGradePaper,
} from "./sidecar.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const isDev = process.env.NODE_ENV === "development";

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1040,
    height: 760,
    minWidth: 880,
    minHeight: 620,
    backgroundColor: "#f6f7f9",
    titleBarStyle: process.platform === "darwin" ? "hiddenInset" : "default",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.once("ready-to-show", () => mainWindow.show());

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// ---------------------------------------------------------------------------
// IPC handlers
// ---------------------------------------------------------------------------

// Pick a .zip of student submissions.
ipcMain.handle("dialog:pickZip", async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: "Select a submissions ZIP",
    properties: ["openFile"],
    filters: [{ name: "ZIP archive", extensions: ["zip"] }],
  });
  if (res.canceled || res.filePaths.length === 0) return null;
  return res.filePaths[0];
});

// Pick a single student's Excel workbook.
ipcMain.handle("dialog:pickWorkbook", async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: "Select a student's Excel workbook",
    properties: ["openFile"],
    filters: [{ name: "Excel workbook", extensions: ["xlsx"] }],
  });
  if (res.canceled || res.filePaths.length === 0) return null;
  return res.filePaths[0];
});

// Pick a write-up paper (MA2).
ipcMain.handle("dialog:pickPaper", async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: "Select the write-up paper",
    properties: ["openFile"],
    filters: [{ name: "Document", extensions: ["docx", "pdf"] }],
  });
  if (res.canceled || res.filePaths.length === 0) return null;
  return res.filePaths[0];
});

// Pick the output folder where graded files are written.
ipcMain.handle("dialog:pickFolder", async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: "Choose an output folder",
    properties: ["openDirectory", "createDirectory"],
  });
  if (res.canceled || res.filePaths.length === 0) return null;
  return res.filePaths[0];
});

// Open a file or folder with the OS default application.
ipcMain.handle("shell:openPath", async (_evt, target) => {
  if (!target) return "no path";
  return shell.openPath(target);
});

ipcMain.handle("shell:showItem", async (_evt, target) => {
  if (target) shell.showItemInFolder(target);
});

// Run a grading job. Streams progress back to the renderer over the
// "grade:event" channel, then resolves with the final result.
ipcMain.handle("grade:run", async (evt, payload) => {
  const { zipPath, course, assignment } = payload || {};
  if (!zipPath || !course || !assignment) {
    throw new Error("Missing zipPath, course, or assignment.");
  }

  // Default workspace: the single Library folder (Settings), so everything
  // lands in one predictable place. A per-run override still wins if provided.
  let workspace = payload.workspace || libraryFolder();
  fs.mkdirSync(workspace, { recursive: true });

  const sender = evt.sender;
  const result = await runGrading(
    {
      zipPath,
      course,
      assignment,
      workspace,
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
    },
    (event) => {
      if (!sender.isDestroyed()) sender.send("grade:event", event);
    }
  );
  recordRun({ course, assignment, mode: "class" }, result);
  return result;
});

// ---- App settings (library folder) ----------------------------------------
const settingsFile = () => path.join(app.getPath("userData"), "settings.json");

function readSettings() {
  try {
    const f = settingsFile();
    if (!fs.existsSync(f)) return {};
    return JSON.parse(fs.readFileSync(f, "utf8")) || {};
  } catch {
    return {};
  }
}
function writeSettings(obj) {
  try {
    fs.mkdirSync(path.dirname(settingsFile()), { recursive: true });
    fs.writeFileSync(settingsFile(), JSON.stringify(obj, null, 2));
  } catch {}
}

// The single Library folder where all grading output lives by default.
// Defaults to ~/Documents/MA Grader (the conventional home for user files).
function libraryFolder() {
  const s = readSettings();
  let folder = s.libraryFolder;
  if (!folder) {
    let docs;
    try {
      docs = app.getPath("documents");
    } catch {
      docs = path.join(os.homedir(), "Documents");
    }
    folder = path.join(docs, "MA Grader");
  }
  try {
    fs.mkdirSync(folder, { recursive: true });
  } catch {}
  return folder;
}

ipcMain.handle("settings:getLibrary", async () => ({ folder: libraryFolder() }));

ipcMain.handle("settings:setLibrary", async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: "Choose your MA Grader library folder",
    properties: ["openDirectory", "createDirectory"],
  });
  if (res.canceled || res.filePaths.length === 0) return { folder: libraryFolder() };
  const s = readSettings();
  s.libraryFolder = res.filePaths[0];
  writeSettings(s);
  return { folder: res.filePaths[0] };
});

// ---- Library browser (drill-down: course -> assignment -> students) --------
function safeReaddir(dir) {
  try {
    return fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
}

ipcMain.handle("library:courses", async () => {
  const root = path.join(libraryFolder(), "graded_output");
  return safeReaddir(root)
    .filter((d) => d.isDirectory())
    .map((d) => ({ course: d.name, label: d.name.replace(/_/g, " ") }))
    .sort((a, b) => a.label.localeCompare(b.label));
});

ipcMain.handle("library:assignments", async (_evt, course) => {
  const dir = path.join(libraryFolder(), "graded_output", course);
  return safeReaddir(dir)
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
});

ipcMain.handle("library:students", async (_evt, course, assignment) => {
  const root = libraryFolder();
  const gradedDir = path.join(root, "graded_output", course, assignment);
  const subDir = path.join(root, "student_submissions", course, assignment);
  const paperDir = path.join(root, "student_papers", course, assignment);
  const suffix = `_${assignment}_Grade.xlsx`;

  const exists = (p) => {
    try {
      return fs.existsSync(p) ? p : null;
    } catch {
      return null;
    }
  };

  const students = safeReaddir(gradedDir)
    .filter((d) => d.isFile() && d.name.endsWith(suffix))
    .map((d) => {
      const name = d.name.slice(0, -suffix.length);
      let paper = null;
      for (const ext of [".docx", ".pdf"]) {
        const p = path.join(paperDir, `${name}_${assignment}${ext}`);
        if (exists(p)) {
          paper = p;
          break;
        }
      }
      return {
        name,
        grade_file: path.join(gradedDir, d.name),
        workbook_file: exists(path.join(subDir, `${name}_${assignment}.xlsx`)),
        paper_file: paper,
        status: "graded",
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  const master = exists(path.join(gradedDir, "INSTRUCTOR_MASTER.xlsx"));
  return { students, master_workbook: master };
});

// ---- Secure API key storage (Anthropic) -----------------------------------
// The key is encrypted at rest with the OS keychain (safeStorage) and never
// stored in plaintext, never in the project, never synced. It is only handed
// to the Python engine as an environment variable at grade time.
const keyFile = () => path.join(app.getPath("userData"), "anthropic.key.enc");

function readStoredKey() {
  try {
    const f = keyFile();
    if (!fs.existsSync(f)) return null;
    const buf = fs.readFileSync(f);
    if (safeStorage.isEncryptionAvailable()) return safeStorage.decryptString(buf);
    return buf.toString("utf8"); // fallback if OS encryption unavailable
  } catch {
    return null;
  }
}

ipcMain.handle("key:save", async (_evt, key) => {
  const trimmed = (key || "").trim();
  if (!trimmed) return { ok: false, error: "Empty key." };
  const enc = safeStorage.isEncryptionAvailable()
    ? safeStorage.encryptString(trimmed)
    : Buffer.from(trimmed, "utf8");
  fs.mkdirSync(path.dirname(keyFile()), { recursive: true });
  fs.writeFileSync(keyFile(), enc);
  return { ok: true, last4: trimmed.slice(-4) };
});

ipcMain.handle("key:status", async () => {
  const k = readStoredKey();
  return {
    hasKey: !!k,
    last4: k ? k.slice(-4) : null,
    encrypted: safeStorage.isEncryptionAvailable(),
  };
});

ipcMain.handle("key:clear", async () => {
  try {
    if (fs.existsSync(keyFile())) fs.unlinkSync(keyFile());
  } catch {}
  return { ok: true };
});

ipcMain.handle("key:test", async () => {
  const k = readStoredKey();
  if (!k) return { ok: false, error: "No API key saved yet." };
  return aiTestKey({ ...engineOpts(), env: { ANTHROPIC_API_KEY: k } });
});

// ---- Run history ----------------------------------------------------------
// Each completed run is appended to a small JSON file in userData so past
// batches can be re-opened (and their students reviewed / papers graded) later.
const historyFile = () => path.join(app.getPath("userData"), "history.json");

function readHistory() {
  try {
    const f = historyFile();
    if (!fs.existsSync(f)) return [];
    const arr = JSON.parse(fs.readFileSync(f, "utf8"));
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function writeHistory(arr) {
  try {
    fs.mkdirSync(path.dirname(historyFile()), { recursive: true });
    fs.writeFileSync(historyFile(), JSON.stringify(arr.slice(0, 200), null, 2));
  } catch {}
}

function recordRun(meta, result) {
  if (!result || result.error) return;
  const record = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    date: new Date().toISOString(),
    course: meta.course,
    assignment: meta.assignment,
    mode: meta.mode, // "class" | "single"
    success_count: result.success_count ?? (result.students || []).length,
    issue_count: result.issue_count ?? (result.issues || []).length,
    graded_path: result.graded_path || null,
    master_workbook: result.master_workbook || null,
    students: result.students || [],
    issues: result.issues || [],
  };
  const all = readHistory();
  all.unshift(record); // most recent first
  writeHistory(all);
}

ipcMain.handle("history:list", async () => readHistory());
ipcMain.handle("history:clear", async () => {
  writeHistory([]);
  return { ok: true };
});

// ---- Review mode ----------------------------------------------------------
const engineOpts = () => ({
  isPackaged: app.isPackaged,
  resourcesPath: process.resourcesPath,
});

ipcMain.handle("review:inspectWorkbook", async (_evt, filePath) =>
  inspectWorkbook(filePath, engineOpts())
);
ipcMain.handle("review:inspectGrade", async (_evt, filePath, assignment) =>
  inspectGrade(filePath, assignment || "MA2", engineOpts())
);
ipcMain.handle("review:updateGrade", async (_evt, filePath, edits) =>
  updateGrade(filePath, edits, engineOpts())
);

// ---- MA2 paper grading ----------------------------------------------------
ipcMain.handle("paper:inspect", async (_evt, gradeFile) =>
  inspectPaper(gradeFile, engineOpts())
);
ipcMain.handle("paper:text", async (_evt, paperPath) =>
  paperText(paperPath, engineOpts())
);
// ---- Student feedback PDF (rendered by Chromium, printed to PDF) ----------
function _esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function buildFeedbackHtml(p) {
  const pct = p.possible ? Math.round((p.total / p.possible) * 100) : 0;
  const rows = (p.criteria || []).map((c) => `
    <div class="crit">
      <div class="crit-head">
        <span class="crit-name">${_esc(c.name)}</span>
        <span class="crit-score">${_esc(c.levelName)} · ${c.points} / ${c.possible}</span>
      </div>
      ${c.description ? `<div class="crit-desc">${_esc(c.description)}</div>` : ""}
      ${c.comment ? `<div class="crit-comment">${_esc(c.comment)}</div>` : ""}
    </div>`).join("");
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, "Segoe UI", system-ui, sans-serif; color: #1d2433;
           margin: 0; padding: 40px 44px; font-size: 13px; line-height: 1.5; }
    .head { border-bottom: 3px solid #2f59c4; padding-bottom: 14px; margin-bottom: 18px; }
    .title { font-size: 20px; font-weight: 600; }
    .sub { color: #5b6478; font-size: 13px; margin-top: 2px; }
    .summary { display: flex; align-items: baseline; gap: 10px; margin: 0 0 22px;
               background: #f3f6f9; border-radius: 10px; padding: 14px 18px; }
    .summary .big { font-size: 26px; font-weight: 700; color: #2f59c4; }
    .summary .lbl { color: #5b6478; }
    .crit { padding: 12px 0; border-bottom: 1px solid #e6eaf0; page-break-inside: avoid; }
    .crit-head { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; }
    .crit-name { font-weight: 600; }
    .crit-score { color: #2f59c4; font-weight: 600; white-space: nowrap; }
    .crit-desc { color: #5b6478; font-size: 12px; margin-top: 3px; }
    .crit-comment { margin-top: 6px; background: #f7f9fb; border-left: 3px solid #cdd6e2;
                    padding: 7px 10px; border-radius: 0 6px 6px 0; font-size: 12.5px; }
    .foot { margin-top: 24px; color: #8a93a3; font-size: 11px; }
  </style></head><body>
    <div class="head">
      <div class="title">${_esc(p.studentName)}</div>
      <div class="sub">${_esc(p.assignment || "MA2")} — Written Paper Feedback</div>
    </div>
    <div class="summary">
      <span class="big">${p.total} / ${p.possible}</span>
      <span class="lbl">(${pct}%)</span>
    </div>
    ${rows}
    <div class="foot">Generated by MA Grader on ${new Date().toLocaleDateString()}.</div>
  </body></html>`;
}

async function htmlToPdf(html) {
  const win = new BrowserWindow({ show: false, webPreferences: { sandbox: true } });
  try {
    await win.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
    return await win.webContents.printToPDF({ printBackground: true, pageSize: "Letter" });
  } finally {
    win.close();
  }
}

ipcMain.handle("pdf:paperFeedback", async (_evt, payload) => {
  const safe = (payload.studentName || "student").replace(/[^a-z0-9]+/gi, "_");
  const res = await dialog.showSaveDialog(mainWindow, {
    title: "Save feedback PDF",
    defaultPath: path.join(
      app.getPath("documents"),
      `${safe}_${payload.assignment || "MA2"}_Paper_Feedback.pdf`
    ),
    filters: [{ name: "PDF", extensions: ["pdf"] }],
  });
  if (res.canceled || !res.filePath) return { canceled: true };
  try {
    const pdf = await htmlToPdf(buildFeedbackHtml(payload));
    fs.writeFileSync(res.filePath, pdf);
    return { ok: true, path: res.filePath };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
});

// Generate feedback PDFs for many students into one chosen folder.
ipcMain.handle("pdf:paperFeedbackBatch", async (_evt, items) => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: "Choose a folder for the feedback PDFs",
    properties: ["openDirectory", "createDirectory"],
  });
  if (res.canceled || res.filePaths.length === 0) return { canceled: true };
  const folder = res.filePaths[0];
  let count = 0;
  const errors = [];
  for (const it of items || []) {
    try {
      const pdf = await htmlToPdf(buildFeedbackHtml(it.payload));
      fs.writeFileSync(path.join(folder, it.filename), pdf);
      count += 1;
    } catch {
      errors.push(it.filename);
    }
  }
  return { ok: true, count, folder, errors };
});

ipcMain.handle("paper:aiGrade", async (_evt, paperPath, strictness, model, gradeFile) => {
  const k = readStoredKey();
  if (!k) return { error: "No API key set. Add your Anthropic key in Settings." };
  return aiGradePaper(paperPath, strictness, model, gradeFile || null, {
    ...engineOpts(),
    env: { ANTHROPIC_API_KEY: k },
  });
});

// Grade a single student's workbook (late / resubmission), merging into the
// existing course folder.
ipcMain.handle("grade:runOne", async (evt, payload) => {
  const { workbookPath, course, student, assignment, paperPath } = payload || {};
  if (!workbookPath || !course || !student || !assignment) {
    throw new Error("Missing workbook, course, student, or assignment.");
  }

  let workspace = payload.workspace || libraryFolder();
  fs.mkdirSync(workspace, { recursive: true });

  const sender = evt.sender;
  const result = await runGradingOne(
    {
      workbookPath,
      course,
      student,
      assignment,
      paperPath: paperPath || null,
      workspace,
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
    },
    (event) => {
      if (!sender.isDestroyed()) sender.send("grade:event", event);
    }
  );
  recordRun({ course, assignment, mode: "single" }, result);
  return result;
});
