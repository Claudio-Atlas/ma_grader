// sidecar.js — spawns the Python grading engine and parses its NDJSON stream.
//
// In development we run the engine from source with the system Python:
//     python3 ../cli.py grade --zip ... --course ... --assignment ... --workspace ...
// In a packaged build we run the PyInstaller binary bundled under resources/engine.
//
// The engine prints one JSON object per line to stdout:
//   {type:"start"} | {type:"progress",current,total,student} |
//   {type:"result",data} | {type:"error",message}
// stderr is diagnostic logging only.

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Engine source root = the ma_grader/ folder (one level above desktop/).
const ENGINE_SRC_DIR = path.resolve(__dirname, "..", "..");
const ENGINE_CLI = path.join(ENGINE_SRC_DIR, "cli.py");

const winPy = (dir) => path.join(dir, "Scripts", "python.exe");
const nixPy = (dir) => path.join(dir, "bin", "python3");

/**
 * Resolve how to invoke the engine.
 * @returns {{cmd: string, baseArgs: string[], cwd: string}}
 */
function resolveEngine(isPackaged, resourcesPath) {
  if (isPackaged) {
    // Packaged build ships a self-contained engine binary frozen by
    // PyInstaller (no Python required on the target machine). It lives under
    // resources/engine/ma-grader-engine/ — see engine.spec + package.json.
    const engineDir = path.join(resourcesPath, "engine", "ma-grader-engine");
    const binName =
      process.platform === "win32" ? "ma-grader-engine.exe" : "ma-grader-engine";
    const exe = path.join(engineDir, binName);
    return { cmd: exe, baseArgs: [], cwd: engineDir };
  }
  // Dev: run from the source tree, preferring the project venv (../.venv).
  const venvPy =
    process.platform === "win32"
      ? winPy(path.join(ENGINE_SRC_DIR, ".venv"))
      : nixPy(path.join(ENGINE_SRC_DIR, ".venv"));
  const py = existsSync(venvPy)
    ? venvPy
    : process.platform === "win32"
    ? "python"
    : "python3";
  return { cmd: py, baseArgs: [ENGINE_CLI], cwd: ENGINE_SRC_DIR };
}

// Shared spawn + NDJSON parsing for any engine subcommand.
function spawnEngine(args, opts, onEvent) {
  const { isPackaged, resourcesPath } = opts;
  const { cmd, baseArgs, cwd } = resolveEngine(isPackaged, resourcesPath);
  const fullArgs = [...baseArgs, ...args];

  return new Promise((resolve, reject) => {
    if (!isPackaged && !existsSync(ENGINE_CLI)) {
      reject(new Error(`Engine CLI not found at ${ENGINE_CLI}`));
      return;
    }

    const child = spawn(cmd, fullArgs, {
      cwd,
      env: { ...process.env, ...(opts.env || {}) },
    });

    let stdoutBuf = "";
    let stderrTail = "";
    let finalResult = null;
    let sawError = null;

    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdoutBuf += chunk;
      let nl;
      while ((nl = stdoutBuf.indexOf("\n")) >= 0) {
        const line = stdoutBuf.slice(0, nl).trim();
        stdoutBuf = stdoutBuf.slice(nl + 1);
        if (!line) continue;
        let evt;
        try {
          evt = JSON.parse(line);
        } catch {
          // Non-JSON on stdout shouldn't happen, but never crash on it.
          continue;
        }
        if (evt.type === "result") finalResult = evt.data;
        if (evt.type === "error") sawError = evt.message;
        try {
          onEvent(evt);
        } catch {
          /* UI callback errors are non-fatal */
        }
      }
    });

    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk) => {
      stderrTail = (stderrTail + chunk).slice(-4000);
    });

    child.on("error", (err) => reject(err));

    child.on("close", (code) => {
      if (sawError) {
        reject(new Error(sawError));
      } else if (finalResult) {
        resolve(finalResult);
      } else if (code !== 0) {
        reject(new Error(`Engine exited with code ${code}.\n${stderrTail}`));
      } else {
        reject(new Error("Engine finished without returning a result."));
      }
    });
  });
}

/**
 * Grade a whole-class ZIP.
 * @param {object} opts {zipPath, course, assignment, workspace, isPackaged, resourcesPath}
 */
export function runGrading(opts, onEvent) {
  const args = [
    "grade",
    "--zip", opts.zipPath,
    "--course", opts.course,
    "--assignment", opts.assignment,
    "--workspace", opts.workspace,
  ];
  return spawnEngine(args, opts, onEvent);
}

/**
 * Grade a single student's workbook, merging into the course folder.
 * @param {object} opts {workbookPath, course, student, assignment, workspace,
 *                        paperPath?, isPackaged, resourcesPath}
 */
export function runGradingOne(opts, onEvent) {
  const args = [
    "grade-one",
    "--workbook", opts.workbookPath,
    "--course", opts.course,
    "--student", opts.student,
    "--assignment", opts.assignment,
    "--workspace", opts.workspace,
  ];
  if (opts.paperPath) args.push("--paper", opts.paperPath);
  return spawnEngine(args, opts, onEvent);
}

// ---- Review-mode (one-shot JSON, no progress) -----------------------------
export function inspectWorkbook(filePath, opts) {
  return spawnEngine(["inspect-workbook", "--file", filePath], opts, () => {});
}
export function inspectGrade(filePath, assignment, opts) {
  return spawnEngine(
    ["inspect-grade", "--file", filePath, "--assignment", assignment],
    opts,
    () => {}
  );
}
export function updateGrade(filePath, edits, opts) {
  return spawnEngine(
    ["update-grade", "--file", filePath, "--edits", JSON.stringify(edits || [])],
    opts,
    () => {}
  );
}

// ---- MA2 paper grading ----------------------------------------------------
export function inspectPaper(gradeFile, opts) {
  return spawnEngine(["inspect-paper", "--file", gradeFile], opts, () => {});
}
export function paperText(paperPath, opts) {
  return spawnEngine(["paper-text", "--paper", paperPath], opts, () => {});
}
export function aiTestKey(opts) {
  // opts.env must carry ANTHROPIC_API_KEY
  return spawnEngine(["ai-test-key"], opts, () => {});
}
export function aiGradePaper(paperPath, strictness, model, gradeFile, opts) {
  const args = ["ai-grade-paper", "--paper", paperPath, "--strictness", strictness || "standard"];
  if (model) args.push("--model", model);
  if (gradeFile) args.push("--grade-file", gradeFile);
  return spawnEngine(args, opts, () => {});
}
