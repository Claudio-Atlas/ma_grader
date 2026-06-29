// preload.js — the only bridge between the sandboxed renderer and Node.
// Exposes a small, explicit API on window.api. Nothing else leaks through.

const { contextBridge, ipcRenderer, webUtils } = require("electron");

contextBridge.exposeInMainWorld("api", {
  // Resolve the absolute path of a drag-and-dropped File (replaces the
  // removed File.path property in modern Electron).
  getPathForFile: (file) => {
    try {
      return webUtils.getPathForFile(file);
    } catch {
      return null;
    }
  },
  pickZip: () => ipcRenderer.invoke("dialog:pickZip"),
  pickWorkbook: () => ipcRenderer.invoke("dialog:pickWorkbook"),
  pickPaper: () => ipcRenderer.invoke("dialog:pickPaper"),
  pickFolder: () => ipcRenderer.invoke("dialog:pickFolder"),
  openPath: (p) => ipcRenderer.invoke("shell:openPath", p),
  showItem: (p) => ipcRenderer.invoke("shell:showItem", p),

  // Kick off a whole-class grading run.
  runGrading: (payload) => ipcRenderer.invoke("grade:run", payload),
  // Grade a single student's workbook (late / resubmission).
  runGradingOne: (payload) => ipcRenderer.invoke("grade:runOne", payload),

  // Review mode.
  inspectWorkbook: (filePath) => ipcRenderer.invoke("review:inspectWorkbook", filePath),
  inspectGrade: (filePath, assignment) =>
    ipcRenderer.invoke("review:inspectGrade", filePath, assignment),
  updateGrade: (filePath, edits) =>
    ipcRenderer.invoke("review:updateGrade", filePath, edits),

  // API key (Anthropic) — stored encrypted by the main process.
  keySave: (key) => ipcRenderer.invoke("key:save", key),
  keyStatus: () => ipcRenderer.invoke("key:status"),
  keyClear: () => ipcRenderer.invoke("key:clear"),
  keyTest: () => ipcRenderer.invoke("key:test"),

  // Library folder + browser.
  getLibrary: () => ipcRenderer.invoke("settings:getLibrary"),
  setLibrary: () => ipcRenderer.invoke("settings:setLibrary"),
  libraryCourses: () => ipcRenderer.invoke("library:courses"),
  libraryAssignments: (course) => ipcRenderer.invoke("library:assignments", course),
  libraryStudents: (course, assignment) =>
    ipcRenderer.invoke("library:students", course, assignment),

  // Run history.
  historyList: () => ipcRenderer.invoke("history:list"),
  historyClear: () => ipcRenderer.invoke("history:clear"),

  // MA2 paper grading.
  inspectPaper: (gradeFile) => ipcRenderer.invoke("paper:inspect", gradeFile),
  paperText: (paperPath) => ipcRenderer.invoke("paper:text", paperPath),
  paperAiGrade: (paperPath, strictness, model, gradeFile) =>
    ipcRenderer.invoke("paper:aiGrade", paperPath, strictness, model, gradeFile),
  paperFeedbackPdf: (payload) => ipcRenderer.invoke("pdf:paperFeedback", payload),
  paperFeedbackPdfBatch: (items) => ipcRenderer.invoke("pdf:paperFeedbackBatch", items),

  // Subscribe to streamed progress events. Returns an unsubscribe function.
  onGradeEvent: (handler) => {
    const listener = (_evt, data) => handler(data);
    ipcRenderer.on("grade:event", listener);
    return () => ipcRenderer.removeListener("grade:event", listener);
  },
});
