import React, { useCallback, useEffect, useState } from "react";
import { Button, Card, Segmented, Stat, Badge, Dot } from "./ui.jsx";
import { Icon } from "./icons.jsx";
import Review from "./Review.jsx";
import PaperGrade from "./PaperGrade.jsx";

// Fallback so the UI renders outside Electron (plain browser preview).
const api =
  typeof window !== "undefined" && window.api
    ? window.api
    : {
        getPathForFile: () => null,
        pickZip: async () => null,
        pickWorkbook: async () => null,
        pickPaper: async () => null,
        pickFolder: async () => null,
        openPath: async () => {},
        showItem: async () => {},
        runGrading: async () => ({ students: [], issues: [] }),
        runGradingOne: async () => ({ students: [], issues: [] }),
        onGradeEvent: () => () => {},
        keySave: async () => ({ ok: true }),
        keyStatus: async () => ({ hasKey: false }),
        keyClear: async () => ({ ok: true }),
        keyTest: async () => ({ ok: false, error: "unavailable" }),
        historyList: async () => [],
        historyClear: async () => ({ ok: true }),
        getLibrary: async () => ({ folder: "~/MA_Grader_Output" }),
        setLibrary: async () => ({ folder: "~/MA_Grader_Output" }),
        libraryCourses: async () => [],
        libraryAssignments: async () => [],
        libraryStudents: async () => ({ students: [], master_workbook: null }),
      };

const ASSIGNMENTS = [
  { value: "MA1", label: "MA1" },
  { value: "MA2", label: "MA2" },
  { value: "MA3", label: "MA3" },
];

const basename = (p) => (p ? p.split(/[\\/]/).pop() : "");

// ---- theme handling -------------------------------------------------------
function applyTheme(mode) {
  const root = document.documentElement;
  if (mode === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", mode);
}
function loadTheme() {
  try {
    return localStorage.getItem("ma-theme") || "system";
  } catch {
    return "system";
  }
}

export default function App() {
  const [theme, setTheme] = useState(loadTheme());
  const [nav, setNav] = useState("run"); // run | manual | history | settings

  // Grade-run state
  const [phase, setPhase] = useState("setup"); // setup | running | done | error
  const [mode, setMode] = useState("class"); // class (zip) | single
  const [zipPath, setZipPath] = useState(null);
  const [workbookPath, setWorkbookPath] = useState(null);
  const [studentName, setStudentName] = useState("");
  const [paperPath, setPaperPath] = useState(null);
  const [course, setCourse] = useState("MAT 144 Online");
  const [assignment, setAssignment] = useState("MA2");
  const [outputFolder, setOutputFolder] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, student: "" });
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [reviewStudent, setReviewStudent] = useState(null);
  const [paperStudent, setPaperStudent] = useState(null);
  // Paper scores held in-app (PDF-only flow): { [studentName]: { [critKey]: {level,points,comment} } }
  const [paperScores, setPaperScores] = useState({});
  const updatePaperScores = useCallback(
    (name, scores) => setPaperScores((p) => ({ ...p, [name]: scores })),
    []
  );

  const canRun =
    course.trim().length > 0 &&
    (mode === "class"
      ? !!zipPath
      : !!workbookPath && studentName.trim().length > 0);

  useEffect(() => applyTheme(theme), [theme]);

  useEffect(() => {
    const off = api.onGradeEvent((evt) => {
      if (evt.type === "progress")
        setProgress({ current: evt.current, total: evt.total, student: evt.student });
    });
    return off;
  }, []);

  const cycleTheme = useCallback(() => {
    setTheme((t) => {
      const next = t === "system" ? "dark" : t === "dark" ? "light" : "system";
      try {
        localStorage.setItem("ma-theme", next);
      } catch {}
      return next;
    });
  }, []);

  const pickZip = useCallback(async () => {
    const p = await api.pickZip();
    if (p) setZipPath(p);
  }, []);
  const pickWorkbook = useCallback(async () => {
    const p = await api.pickWorkbook();
    if (p) setWorkbookPath(p);
  }, []);
  const pickPaper = useCallback(async () => {
    const p = await api.pickPaper();
    if (p) setPaperPath(p);
  }, []);
  const pickFolder = useCallback(async () => {
    const p = await api.pickFolder();
    if (p) setOutputFolder(p);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.name.toLowerCase().endsWith(".zip")) {
      const full = (api.getPathForFile && api.getPathForFile(f)) || f.path || null;
      // Only accept a real absolute path; otherwise prompt to browse.
      if (full && full.startsWith("/")) setZipPath(full);
      else pickZip();
    }
  }, []);

  const run = useCallback(async () => {
    setNav("run");
    setPhase("running");
    setProgress({ current: 0, total: 0, student: "" });
    setErrorMsg("");
    setResult(null);
    try {
      const res =
        mode === "single"
          ? await api.runGradingOne({
              workbookPath,
              student: studentName.trim(),
              course: course.trim(),
              assignment,
              paperPath: assignment === "MA2" ? paperPath || undefined : undefined,
              workspace: outputFolder || undefined,
            })
          : await api.runGrading({
              zipPath,
              course: course.trim(),
              assignment,
              workspace: outputFolder || undefined,
            });
      setResult(res);
      setPhase(res?.error ? "error" : "done");
      if (res?.error) setErrorMsg(res.error);
    } catch (err) {
      setErrorMsg(err?.message || String(err));
      setPhase("error");
    }
  }, [mode, zipPath, workbookPath, studentName, paperPath, course, assignment, outputFolder]);

  const reset = useCallback(() => {
    setPhase("setup");
    setResult(null);
    setErrorMsg("");
    setProgress({ current: 0, total: 0, student: "" });
  }, []);

  // Re-open a past run: load it as the current result and show its results,
  // from which Review and paper grading work just like a fresh run.
  const openHistory = useCallback((rec) => {
    setResult(rec);
    setAssignment(rec.assignment || "MA2");
    setReviewStudent(null);
    setPaperStudent(null);
    setNav("run");
    setPhase("done");
  }, []);

  const stepLabel =
    phase === "running" ? "Running" : phase === "done" ? "Results" : phase === "error" ? "Error" : "New run";

  return (
    <div className="h-full flex text-ink font-sans bg-bg">
      <Sidebar nav={nav} setNav={setNav} theme={theme} cycleTheme={cycleTheme} />

      <div className="flex-1 flex flex-col min-w-0">
        <TopBar crumb={navCrumb(nav, stepLabel)} course={course} />

        <main className="flex-1 flex flex-col min-h-0">
          {reviewStudent ? (
            <div className="flex-1 min-h-0 px-6 py-5">
              <Review
                student={reviewStudent}
                assignment={reviewStudent.assignment || assignment}
                onBack={() => setReviewStudent(null)}
              />
            </div>
          ) : paperStudent ? (
            <div className="flex-1 min-h-0 px-6 py-5">
              <PaperGrade
                student={paperStudent}
                scores={paperScores[paperStudent.name]}
                onScores={updatePaperScores}
                onBack={() => setPaperStudent(null)}
              />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-3xl mx-auto px-8 py-8">
                {nav === "run" && phase === "setup" && (
                  <SetupScreen
                    {...{
                      mode, setMode, zipPath, workbookPath, studentName, setStudentName,
                      paperPath, setPaperPath, course, setCourse, assignment, setAssignment,
                      outputFolder, dragging, setDragging, onDrop, pickZip, pickWorkbook,
                      pickPaper, pickFolder, canRun, run,
                    }}
                  />
                )}
                {nav === "run" && phase === "running" && <RunningScreen progress={progress} />}
                {nav === "run" && phase === "done" && (
                  <ResultsScreen
                    result={result}
                    assignment={assignment}
                    onReset={reset}
                    onReview={setReviewStudent}
                  />
                )}
                {nav === "run" && phase === "error" && (
                  <ErrorScreen message={errorMsg} onReset={reset} />
                )}
                {nav === "library" && (
                  <LibraryScreen
                    onReview={(s) => setReviewStudent(s)}
                    onPaper={(s) => setPaperStudent(s)}
                  />
                )}
                {nav === "manual" && (
                  <ManualScreen
                    result={result}
                    onPick={setPaperStudent}
                    paperScores={paperScores}
                    setStudentScores={updatePaperScores}
                  />
                )}
                {nav === "history" && <HistoryScreen onOpen={openHistory} />}
                {nav === "settings" && <SettingsScreen theme={theme} setTheme={setTheme} />}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function navCrumb(nav, stepLabel) {
  if (nav === "run") return ["New run", stepLabel === "New run" ? null : stepLabel];
  if (nav === "library") return ["Library", null];
  if (nav === "manual") return ["Manual grading", null];
  if (nav === "history") return ["History", null];
  return ["Settings", null];
}

// ---------------------------------------------------------------------------
// Shell
// ---------------------------------------------------------------------------
function Sidebar({ nav, setNav, theme, cycleTheme }) {
  const items = [
    { id: "run", label: "New run", icon: Icon.Play },
    { id: "library", label: "Library", icon: Icon.Folder },
    { id: "manual", label: "Manual grade", icon: Icon.Pencil, badge: "MA2" },
    { id: "history", label: "History", icon: Icon.Clock },
    { id: "settings", label: "Settings", icon: Icon.Sliders },
  ];
  const themeIcon =
    theme === "dark" ? Icon.Moon : theme === "light" ? Icon.Sun : Icon.Monitor;
  const ThemeIcon = themeIcon;
  return (
    <aside className="w-60 shrink-0 bg-bg-elev border-r border-hair flex flex-col titlebar-drag">
      <div className="h-14 flex items-center gap-2.5 px-5">
        <div className="w-7 h-7 rounded-lg bg-accent text-ink-inv flex items-center justify-center shadow-glow-sm">
          <Icon.Bolt width={15} height={15} />
        </div>
        <div className="leading-tight">
          <div className="text-[13px] font-medium tracking-tight">MA Grader</div>
          <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-ink-3">
            Autograder
          </div>
        </div>
      </div>

      <nav className="px-3 mt-3 space-y-0.5 titlebar-no-drag">
        {items.map((it) => {
          const ItIcon = it.icon;
          const active = nav === it.id;
          return (
            <button
              key={it.id}
              onClick={() => setNav(it.id)}
              className={
                "w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150 " +
                (active
                  ? "bg-accent-soft text-accent shadow-inset-accent"
                  : "text-ink-2 hover:text-ink hover:bg-surface-3")
              }
            >
              <ItIcon width={17} height={17} />
              <span className="flex-1 text-left">{it.label}</span>
              {it.badge && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-manual-soft text-manual">
                  {it.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto p-3 titlebar-no-drag">
        <button
          onClick={cycleTheme}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-ink-2 hover:text-ink bg-surface-3 hover:bg-surface-2 border border-hair transition-all"
        >
          <ThemeIcon width={16} height={16} />
          <span className="flex-1 text-left capitalize">{theme}</span>
          <Dot tone="accent" glow />
        </button>
      </div>
    </aside>
  );
}

function TopBar({ crumb, course }) {
  const [main, sub] = crumb;
  return (
    <header className="titlebar-drag h-14 shrink-0 flex items-center justify-between px-7 border-b border-hair bg-bg-elev/60 backdrop-blur">
      <div className="flex items-center gap-2 text-sm">
        <span className="font-medium">{main}</span>
        {sub && (
          <>
            <span className="text-ink-3">/</span>
            <span className="font-mono text-ink-3 text-[13px]">{sub}</span>
          </>
        )}
      </div>
      <div className="font-mono text-[12px] text-ink-3">{course}</div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Screens
// ---------------------------------------------------------------------------
function SetupScreen(props) {
  const {
    mode, setMode, zipPath, workbookPath, studentName, setStudentName, paperPath,
    setPaperPath, course, setCourse, assignment, setAssignment, outputFolder,
    dragging, setDragging, onDrop, pickZip, pickWorkbook, pickPaper, pickFolder,
    canRun, run,
  } = props;

  const single = mode === "single";

  return (
    <div className="fade-up space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">
          {single ? "Grade one late submission" : "Grade a class in one drop"}
        </h1>
        <p className="text-ink-2 text-sm mt-1.5">
          {single
            ? "Drop in a single student's workbook — it merges into the existing class."
            : "Drop a submissions zip, pick the assignment, and the grader handles the rest."}
        </p>
      </div>

      <Segmented
        options={[
          { value: "class", label: "Whole class" },
          { value: "single", label: "Single student" },
        ]}
        value={mode}
        onChange={setMode}
      />

      {!single ? (
        <DropArea
          onDrop={onDrop}
          onClick={pickZip}
          setDragging={setDragging}
          dragging={dragging}
          selected={zipPath}
          idleTitle="Drop submissions zip here"
          selectedHint="Click to choose a different zip"
        />
      ) : (
        <FilePick
          icon={Icon.File}
          label="Student workbook"
          value={workbookPath}
          onPick={pickWorkbook}
          placeholder="Choose the student's .xlsx"
        />
      )}

      <Card className="p-6 space-y-6">
        {single && (
          <Field label="Student name" hint="First and last — names the graded file">
            <input
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="Jane Doe"
              className="titlebar-no-drag w-full rounded-xl bg-surface-2 border border-hair px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:shadow-focus focus:border-accent transition-all"
            />
          </Field>
        )}

        <Field label="Course label" hint={single ? "Must match the class to merge in" : "Used to name the output folder"}>
          <input
            value={course}
            onChange={(e) => setCourse(e.target.value)}
            placeholder="MAT 144 Online"
            className="titlebar-no-drag w-full rounded-xl bg-surface-2 border border-hair px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:shadow-focus focus:border-accent transition-all"
          />
        </Field>

        <Field label="Assignment">
          <Segmented options={ASSIGNMENTS} value={assignment} onChange={setAssignment} />
        </Field>

        {single && assignment === "MA2" && (
          <Field label="Write-up paper" hint="Stored for manual grading (optional)">
            <FilePick
              inline
              icon={Icon.File}
              value={paperPath}
              onPick={pickPaper}
              placeholder="Choose .docx or .pdf"
              onClear={() => setPaperPath(null)}
            />
          </Field>
        )}

        <Field label="Output folder" hint="Optional — overrides your Library folder for this run">
          <div className="flex items-center gap-3">
            <Button variant="subtle" onClick={pickFolder}>
              <Icon.Folder width={16} height={16} />
              Choose folder…
            </Button>
            <span className="text-xs text-ink-3 truncate">
              {outputFolder || "Defaults to your Library folder (Settings)"}
            </span>
          </div>
        </Field>
      </Card>

      <div className="flex justify-end">
        <Button onClick={run} disabled={!canRun} className="px-6 py-3">
          {single ? "Grade student" : "Grade submissions"}
          <Icon.ArrowRight width={17} height={17} />
        </Button>
      </div>
    </div>
  );
}

function DropArea({ onDrop, onClick, setDragging, dragging, selected, idleTitle, selectedHint }) {
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={onClick}
      className={
        "cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-200 px-6 py-12 text-center titlebar-no-drag " +
        (dragging
          ? "border-accent bg-accent-soft shadow-glow"
          : selected
          ? "border-accent/50 bg-accent-soft shadow-glow-soft"
          : "border-hair-strong bg-surface hover:border-accent/60 hover:bg-accent-soft")
      }
    >
      <div className="flex flex-col items-center gap-2">
        <div
          className={
            "w-12 h-12 rounded-xl flex items-center justify-center " +
            (selected ? "bg-accent text-ink-inv shadow-glow-sm" : "bg-surface-3 text-accent")
          }
        >
          {selected ? <Icon.File width={22} height={22} /> : <Icon.Upload width={22} height={22} />}
        </div>
        {selected ? (
          <>
            <div className="font-medium text-sm">{basename(selected)}</div>
            <div className="text-xs text-ink-3">{selectedHint}</div>
          </>
        ) : (
          <>
            <div className="font-medium text-sm">{idleTitle}</div>
            <div className="text-xs text-ink-3">or click to browse</div>
          </>
        )}
      </div>
    </div>
  );
}

function FilePick({ icon, label, value, onPick, placeholder, inline, onClear }) {
  const PIcon = icon;
  const body = (
    <div className="flex items-center gap-3">
      <Button variant="subtle" onClick={onPick}>
        <PIcon width={16} height={16} />
        {value ? "Change…" : "Choose…"}
      </Button>
      <span className="text-xs text-ink-3 truncate flex-1">{value ? basename(value) : placeholder}</span>
      {value && onClear && (
        <button onClick={onClear} className="text-xs text-ink-3 hover:text-danger titlebar-no-drag">
          Clear
        </button>
      )}
    </div>
  );
  if (inline) return body;
  return (
    <Card className="p-5">
      <div className="text-sm font-medium mb-3">{label}</div>
      {body}
    </Card>
  );
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <label className="text-sm font-medium">{label}</label>
        {hint && <span className="text-xs text-ink-3">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

function RunningScreen({ progress }) {
  const pct = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;
  return (
    <div className="fade-up flex flex-col items-center justify-center py-24 text-center">
      <div className="w-full max-w-md">
        <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent mb-3">
          Grading in progress
        </div>
        <div className="text-lg font-medium mb-4">
          {progress.total > 0 ? (
            <span className="tabular-nums">
              {progress.current} <span className="text-ink-3">/</span> {progress.total}
            </span>
          ) : (
            "Preparing submissions…"
          )}
        </div>
        <div className="h-2 rounded-full bg-surface-3 overflow-hidden border border-hair">
          <div
            className="h-full rounded-full bg-accent shadow-glow-soft transition-all duration-300 ease-out"
            style={{ width: `${Math.max(pct, progress.total > 0 ? 4 : 14)}%` }}
          />
        </div>
        <div className="mt-4 text-xs text-ink-3 h-4 font-mono">
          {progress.student ? progress.student.replace(/_/g, " ") : ""}
        </div>
      </div>
    </div>
  );
}

function ResultsScreen({ result, assignment, onReset, onReview }) {
  const students = result?.students || [];
  const issues = result?.issues || [];
  const graded = result?.success_count ?? students.length;

  return (
    <div className="fade-up space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Grading complete</h1>
          <p className="text-ink-2 text-sm mt-1.5">{assignment} batch finished.</p>
        </div>
        <Button variant="subtle" onClick={onReset}>
          Grade another
        </Button>
      </div>

      <Card className="p-6">
        <div className="grid grid-cols-3 gap-4">
          <Stat label="Graded" value={graded} tone="accent" />
          <Stat label="Issues" value={issues.length} tone={issues.length ? "warn" : "default"} />
          <Stat label="Assignment" value={assignment} />
        </div>
      </Card>

      <div className="flex flex-wrap gap-3">
        {result?.master_workbook && (
          <Button onClick={() => api.openPath(result.master_workbook)}>
            Open instructor master
            <Icon.ArrowRight width={16} height={16} />
          </Button>
        )}
        {result?.graded_path && (
          <Button variant="soft" onClick={() => api.openPath(result.graded_path)}>
            <Icon.Folder width={16} height={16} />
            Open graded folder
          </Button>
        )}
      </div>

      {issues.length > 0 && (
        <Card className="p-6">
          <h2 className="text-sm font-medium mb-3 flex items-center gap-2">
            <span className="text-warning">
              <Icon.Alert width={16} height={16} />
            </span>
            Needs a look
          </h2>
          <ul className="space-y-3">
            {issues.map((it, i) => (
              <li key={i} className="text-sm">
                <span className="font-medium">{(it.student || "Unknown").replace(/_/g, " ")}</span>
                <span className="text-ink-2"> — {it.problem}</span>
                {it.action && <div className="text-xs text-ink-3 mt-0.5">→ {it.action}</div>}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="overflow-hidden">
        <div className="px-6 py-3.5 border-b border-hair text-sm font-medium flex items-center justify-between">
          <span>Students</span>
          <span className="font-mono text-xs text-ink-3">{students.length}</span>
        </div>
        <ul className="divide-y divide-hair">
          {students.map((s, i) => (
            <li key={i}>
              <button
                onClick={() => onReview && s.grade_file && onReview(s)}
                disabled={!s.grade_file}
                className="w-full px-6 py-3 flex items-center justify-between text-sm hover:bg-surface-3 transition-colors disabled:cursor-default text-left group"
              >
                <span className="flex items-center gap-2.5">
                  <Dot tone="ok" />
                  <span className="font-medium">{s.name.replace(/_/g, " ")}</span>
                </span>
                <span className="flex items-center gap-2.5">
                  {s.grade_file && (
                    <span className="text-xs text-ink-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      Review →
                    </span>
                  )}
                  <Badge tone="ok">{s.status || "graded"}</Badge>
                </span>
              </button>
            </li>
          ))}
          {students.length === 0 && (
            <li className="px-6 py-8 text-sm text-ink-3 text-center">
              No graded files were produced.
            </li>
          )}
        </ul>
      </Card>
    </div>
  );
}

function ErrorScreen({ message, onReset }) {
  return (
    <div className="fade-up flex flex-col items-center justify-center py-24 text-center">
      <div className="w-12 h-12 rounded-2xl bg-danger-soft text-danger flex items-center justify-center mb-4">
        <Icon.Alert width={24} height={24} />
      </div>
      <h1 className="text-xl font-medium">Something went wrong</h1>
      <p className="text-ink-2 text-sm mt-2 max-w-md whitespace-pre-wrap">
        {message || "The grading run did not finish."}
      </p>
      <Button variant="subtle" onClick={onReset} className="mt-6">
        Back to start
      </Button>
    </div>
  );
}

function SettingsScreen({ theme, setTheme }) {
  const opts = [
    { value: "system", label: "System", icon: Icon.Monitor },
    { value: "light", label: "Light", icon: Icon.Sun },
    { value: "dark", label: "Dark", icon: Icon.Moon },
  ];
  const set = (v) => {
    try {
      localStorage.setItem("ma-theme", v);
    } catch {}
    setTheme(v);
  };
  return (
    <div className="fade-up space-y-6">
      <h1 className="text-2xl font-medium tracking-tight">Settings</h1>
      <Card className="p-6 space-y-3">
        <div className="text-sm font-medium">Appearance</div>
        <div className="flex gap-2">
          {opts.map((o) => {
            const OIcon = o.icon;
            const active = theme === o.value;
            return (
              <button
                key={o.value}
                onClick={() => set(o.value)}
                className={
                  "flex-1 flex flex-col items-center gap-2 py-4 rounded-xl border transition-all " +
                  (active
                    ? "border-accent bg-accent-soft text-accent shadow-glow-sm"
                    : "border-hair bg-surface-2 text-ink-2 hover:text-ink")
                }
              >
                <OIcon width={20} height={20} />
                <span className="text-xs font-medium">{o.label}</span>
              </button>
            );
          })}
        </div>
      </Card>

      <LibraryFolderCard />
      <ApiKeyCard />
    </div>
  );
}

function LibraryFolderCard() {
  const [folder, setFolder] = useState("");
  useEffect(() => {
    api.getLibrary().then((r) => setFolder(r?.folder || ""));
  }, []);
  const change = useCallback(async () => {
    const r = await api.setLibrary();
    if (r?.folder) setFolder(r.folder);
  }, []);
  return (
    <Card className="p-6 space-y-3">
      <div className="text-sm font-medium">Library folder</div>
      <p className="text-xs text-ink-3">
        Where all graded files are saved and browsed from. Everything lands here
        unless you override the output folder for a single run.
      </p>
      <div className="flex items-center gap-3">
        <Button variant="subtle" onClick={change}>
          <Icon.Folder width={16} height={16} />
          Change…
        </Button>
        <span className="text-xs text-ink-3 truncate flex-1 font-mono">{folder}</span>
      </div>
    </Card>
  );
}

function ApiKeyCard() {
  const [status, setStatus] = useState({ hasKey: false });
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null); // {ok, text}

  const refresh = useCallback(async () => {
    const s = await api.keyStatus();
    setStatus(s || { hasKey: false });
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);

  const save = useCallback(async () => {
    if (!value.trim()) return;
    setBusy(true);
    setMsg(null);
    const res = await api.keySave(value.trim());
    setBusy(false);
    if (res?.ok) {
      setValue("");
      setMsg({ ok: true, text: "Key saved." });
      refresh();
    } else {
      setMsg({ ok: false, text: res?.error || "Could not save key." });
    }
  }, [value, refresh]);

  const test = useCallback(async () => {
    setBusy(true);
    setMsg(null);
    const res = await api.keyTest();
    setBusy(false);
    setMsg(
      res?.ok
        ? { ok: true, text: "Key works." }
        : { ok: false, text: res?.error || "Key test failed." }
    );
  }, []);

  const clear = useCallback(async () => {
    setBusy(true);
    await api.keyClear();
    setBusy(false);
    setMsg({ ok: true, text: "Key removed." });
    refresh();
  }, [refresh]);

  return (
    <Card className="p-6 space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium">AI grading</div>
        {status.hasKey ? (
          <Badge tone="ok">Key saved ····{status.last4}</Badge>
        ) : (
          <Badge tone="default">No key</Badge>
        )}
      </div>
      <p className="text-xs text-ink-3">
        Your own Anthropic API key, used to AI-grade MA2 papers. It's encrypted on
        this Mac and never leaves it. Each person uses their own key.
      </p>
      <div className="flex items-center gap-2">
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={status.hasKey ? "Enter a new key to replace" : "sk-ant-…"}
          className="flex-1 rounded-xl bg-surface-2 border border-hair px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:shadow-focus focus:border-accent transition-all"
        />
        <Button onClick={save} disabled={busy || !value.trim()}>
          Save
        </Button>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="subtle" onClick={test} disabled={busy || !status.hasKey}>
          Test key
        </Button>
        {status.hasKey && (
          <Button variant="ghost" onClick={clear} disabled={busy}>
            Remove
          </Button>
        )}
        {msg && (
          <span className={"text-xs " + (msg.ok ? "text-success" : "text-danger")}>{msg.text}</span>
        )}
      </div>
      {!status.encrypted && status.hasKey && (
        <div className="text-[11px] text-warning">
          OS encryption unavailable — key stored unencrypted on this machine.
        </div>
      )}

      <ModelPicker />
      <StrictnessPicker />
    </Card>
  );
}

function ModelPicker() {
  const opts = [
    { v: "claude-haiku-4-5-20251001", label: "Haiku", hint: "Fastest, cheapest (~<1¢/paper)" },
    { v: "claude-sonnet-4-6", label: "Sonnet", hint: "Best balance (~2¢/paper)" },
    { v: "claude-opus-4-8", label: "Opus", hint: "Strongest (~3–4¢/paper)" },
  ];
  const [val, setVal] = useState("claude-sonnet-4-6");
  useEffect(() => {
    try {
      setVal(localStorage.getItem("ma-ai-model") || "claude-sonnet-4-6");
    } catch {}
  }, []);
  const set = (v) => {
    try {
      localStorage.setItem("ma-ai-model", v);
    } catch {}
    setVal(v);
  };
  return (
    <div className="pt-3 border-t border-hair space-y-2">
      <div className="text-sm font-medium">AI model</div>
      <p className="text-xs text-ink-3">
        Which Claude model grades the papers. Sonnet is recommended for judging writing.
      </p>
      <div className="flex gap-2">
        {opts.map((o) => {
          const active = val === o.v;
          return (
            <button
              key={o.v}
              onClick={() => set(o.v)}
              title={o.hint}
              className={
                "flex-1 py-2.5 rounded-xl border text-xs font-medium transition-all " +
                (active
                  ? "border-accent bg-accent-soft text-accent shadow-glow-sm"
                  : "border-hair bg-surface-2 text-ink-2 hover:text-ink")
              }
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function StrictnessPicker() {
  const opts = [
    { v: "lenient", label: "Lenient", hint: "Generous — rounds borderline up" },
    { v: "standard", label: "Standard", hint: "Rubric as written" },
    { v: "elite", label: "Elite", hint: "Strict — high bar for top marks" },
  ];
  const [val, setVal] = useState("standard");
  useEffect(() => {
    try {
      setVal(localStorage.getItem("ma-ai-strictness") || "standard");
    } catch {}
  }, []);
  const set = (v) => {
    try {
      localStorage.setItem("ma-ai-strictness", v);
    } catch {}
    setVal(v);
  };
  return (
    <div className="pt-3 border-t border-hair space-y-2">
      <div className="text-sm font-medium">AI grading strictness</div>
      <p className="text-xs text-ink-3">
        How demanding Claude is when suggesting paper levels. Point values never change.
      </p>
      <div className="flex gap-2">
        {opts.map((o) => {
          const active = val === o.v;
          return (
            <button
              key={o.v}
              onClick={() => set(o.v)}
              title={o.hint}
              className={
                "flex-1 py-2.5 rounded-xl border text-xs font-medium transition-all " +
                (active
                  ? "border-accent bg-accent-soft text-accent shadow-glow-sm"
                  : "border-hair bg-surface-2 text-ink-2 hover:text-ink")
              }
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ManualScreen({ result, onPick, paperScores = {}, setStudentScores }) {
  const all = result?.students || [];
  const papers = all.filter((s) => s.paper_file);

  const [batch, setBatch] = useState(null); // {current,total,student} | null
  const [batchDone, setBatchDone] = useState(null); // {graded, failed:[]}
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfDone, setPdfDone] = useState(null); // {count, folder}

  const gradedCount = papers.filter((s) => paperScores[s.name]).length;

  const runBatch = useCallback(async () => {
    let strictness = "standard";
    let model = "claude-sonnet-4-6";
    try {
      strictness = localStorage.getItem("ma-ai-strictness") || "standard";
      model = localStorage.getItem("ma-ai-model") || "claude-sonnet-4-6";
    } catch {}
    setBatchDone(null);
    const failed = [];
    let ok = 0;
    for (let i = 0; i < papers.length; i++) {
      const s = papers[i];
      setBatch({ current: i + 1, total: papers.length, student: s.name });
      try {
        // No grade_file => AI suggests only; scores are held in the app, not Excel.
        const res = await api.paperAiGrade(s.paper_file, strictness, model);
        if (res?.error) failed.push({ name: s.name, error: res.error });
        else {
          const scores = {};
          (res.suggestions || []).forEach((sg) => {
            scores[sg.key] = { level: sg.level, points: sg.points, comment: sg.comment || "" };
          });
          setStudentScores(s.name, scores);
          ok += 1;
        }
      } catch (e) {
        failed.push({ name: s.name, error: e?.message || String(e) });
      }
    }
    setBatch(null);
    setBatchDone({ graded: ok, failed });
  }, [papers, setStudentScores]);

  const downloadAll = useCallback(async () => {
    const graded = papers.filter((s) => paperScores[s.name]);
    if (!graded.length) return;
    setPdfBusy(true);
    setPdfDone(null);
    try {
      const ins = await api.inspectPaper(graded[0].grade_file); // rubric structure (same for all)
      const crit = ins.criteria || [];
      const items = graded.map((s) => {
        const sc = paperScores[s.name] || {};
        let sum = 0;
        const criteria = crit.map((c) => {
          const x = sc[c.key] || {};
          const lvl = (c.levels || []).find((l) => l.level === x.level);
          const points = typeof x.points === "number" ? x.points : 0;
          sum += points;
          return {
            name: c.name,
            possible: c.possible,
            levelName: lvl ? lvl.name : "Not scored",
            points,
            description: lvl ? lvl.description : "",
            comment: x.comment || "",
          };
        });
        return {
          filename: `${s.name.replace(/[^a-z0-9]+/gi, "_")}_MA2_Paper_Feedback.pdf`,
          payload: {
            studentName: s.name.replace(/_/g, " "),
            assignment: "MA2",
            total: Math.round(sum * 100) / 100,
            possible: ins.total_possible || 42,
            criteria,
          },
        };
      });
      const res = await api.paperFeedbackPdfBatch(items);
      if (res?.ok) setPdfDone({ count: res.count, folder: res.folder });
    } finally {
      setPdfBusy(false);
    }
  }, [papers, paperScores]);

  if (papers.length === 0) {
    return (
      <Placeholder
        title="Manual paper grading"
        icon={Icon.Pencil}
        body={
          all.length === 0
            ? "Grade an MA2 batch (or a single MA2 student with a paper) first — the write-ups to grade will appear here."
            : "No write-up papers were found in the last run. MA2 single submissions and zips that include .docx/.pdf papers will show up here."
        }
      />
    );
  }

  const running = !!batch;
  const pct = batch ? Math.round((batch.current / batch.total) * 100) : 0;

  return (
    <div className="fade-up space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Manual paper grading</h1>
          <p className="text-ink-2 text-sm mt-1.5">
            {papers.length} write-up{papers.length === 1 ? "" : "s"}
            {gradedCount > 0 ? ` · ${gradedCount} scored` : ""}. Grade all with AI, review, then export PDFs.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button variant="soft" onClick={runBatch} disabled={running || pdfBusy}>
            <Icon.Bolt width={15} height={15} />
            {running ? "Grading…" : "Grade all papers (AI)"}
          </Button>
          <Button onClick={downloadAll} disabled={pdfBusy || running || gradedCount === 0}>
            {pdfBusy ? "Exporting…" : `Download all PDFs${gradedCount ? ` (${gradedCount})` : ""}`}
          </Button>
        </div>
      </div>

      {running && (
        <Card className="p-4">
          <div className="text-xs font-mono text-accent mb-2">
            Grading {batch.current} / {batch.total} — {batch.student.replace(/_/g, " ")}
          </div>
          <div className="h-2 rounded-full bg-surface-3 overflow-hidden border border-hair">
            <div
              className="h-full bg-accent rounded-full shadow-glow-soft transition-all duration-300"
              style={{ width: `${Math.max(pct, 4)}%` }}
            />
          </div>
        </Card>
      )}

      {pdfDone && !pdfBusy && (
        <Card className="p-4">
          <div className="text-sm">
            <span className="text-success font-medium">{pdfDone.count} PDF{pdfDone.count === 1 ? "" : "s"} saved</span>
            <span className="text-ink-3"> to {pdfDone.folder}</span>
          </div>
        </Card>
      )}

      {batchDone && !running && (
        <Card className="p-4">
          <div className="text-sm">
            <span className="text-success font-medium">{batchDone.graded} scored</span>
            {batchDone.failed.length > 0 && (
              <span className="text-ink-2">
                {" "}· <span className="text-warning">{batchDone.failed.length} need a look</span>
              </span>
            )}
            <span className="text-ink-3"> — open any student to review or adjust, then Download all PDFs.</span>
          </div>
          {batchDone.failed.length > 0 && (
            <ul className="mt-2 space-y-1">
              {batchDone.failed.map((f, i) => (
                <li key={i} className="text-xs text-ink-3">
                  {f.name.replace(/_/g, " ")}: {f.error}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Card className="overflow-hidden">
        <ul className="divide-y divide-hair">
          {papers.map((s, i) => (
            <li key={i}>
              <button
                onClick={() => onPick(s)}
                className="w-full px-6 py-3 flex items-center justify-between text-sm hover:bg-surface-3 transition-colors text-left group"
              >
                <span className="flex items-center gap-2.5">
                  <Dot tone={paperScores[s.name] ? "ok" : "manual"} />
                  <span className="font-medium">{s.name.replace(/_/g, " ")}</span>
                </span>
                <span className="flex items-center gap-2.5">
                  <span className="text-xs text-ink-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    {paperScores[s.name] ? "Review →" : "Grade paper →"}
                  </span>
                  <Badge tone={paperScores[s.name] ? "ok" : "manual"}>
                    {paperScores[s.name] ? "scored" : "paper"}
                  </Badge>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function HistoryScreen({ onOpen }) {
  const [runs, setRuns] = useState(null);
  const load = useCallback(async () => {
    setRuns((await api.historyList()) || []);
  }, []);
  useEffect(() => {
    load();
  }, [load]);
  const clear = useCallback(async () => {
    await api.historyClear();
    load();
  }, [load]);

  if (runs && runs.length === 0) {
    return (
      <Placeholder
        title="History"
        icon={Icon.Clock}
        body="No grading runs yet. Grade a class or a single student and it'll be saved here so you can re-open it later — even after restarting."
      />
    );
  }

  const when = (iso) => {
    try {
      return new Date(iso).toLocaleString(undefined, {
        month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="fade-up space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">History</h1>
          <p className="text-ink-2 text-sm mt-1.5">
            Past grading runs. Open one to review students or grade papers again.
          </p>
        </div>
        {runs?.length > 0 && (
          <Button variant="ghost" onClick={clear}>
            Clear history
          </Button>
        )}
      </div>
      <Card className="overflow-hidden">
        <ul className="divide-y divide-hair">
          {(runs || []).map((r) => (
            <li key={r.id}>
              <button
                onClick={() => onOpen(r)}
                className="w-full px-6 py-3.5 flex items-center justify-between text-sm hover:bg-surface-3 transition-colors text-left group"
              >
                <span className="flex items-center gap-3">
                  <Badge tone="accent">{r.assignment}</Badge>
                  <span>
                    <span className="font-medium">{r.course}</span>
                    <span className="text-ink-3 text-xs ml-2">{when(r.date)}</span>
                    {r.mode === "single" && (
                      <span className="text-ink-3 text-xs ml-2">· single</span>
                    )}
                  </span>
                </span>
                <span className="flex items-center gap-3">
                  <span className="text-xs text-ink-3 tabular-nums">
                    {r.success_count} graded
                    {r.issue_count ? ` · ${r.issue_count} issues` : ""}
                  </span>
                  <span className="text-xs text-ink-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    Open →
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function LibraryScreen({ onReview, onPaper }) {
  const [courses, setCourses] = useState(null);
  const [course, setCourse] = useState(null); // {course, label}
  const [assignments, setAssignments] = useState(null);
  const [assignment, setAssignment] = useState(null);
  const [data, setData] = useState(null); // {students, master_workbook}

  useEffect(() => {
    api.libraryCourses().then(setCourses);
  }, []);

  const openCourse = useCallback(async (c) => {
    setCourse(c);
    setAssignment(null);
    setData(null);
    setAssignments(await api.libraryAssignments(c.course));
  }, []);

  const openAssignment = useCallback(
    async (a) => {
      setAssignment(a);
      setData(await api.libraryStudents(course.course, a));
    },
    [course]
  );

  const back = useCallback(() => {
    if (assignment) {
      setAssignment(null);
      setData(null);
    } else if (course) {
      setCourse(null);
      setAssignments(null);
    }
  }, [assignment, course]);

  // ----- breadcrumb -----
  const crumb = (
    <div className="flex items-center gap-2 text-sm">
      <button
        onClick={() => {
          setCourse(null);
          setAssignment(null);
          setAssignments(null);
          setData(null);
        }}
        className={course ? "text-ink-3 hover:text-ink" : "font-medium"}
      >
        Library
      </button>
      {course && (
        <>
          <span className="text-ink-3">/</span>
          <button
            onClick={() => {
              setAssignment(null);
              setData(null);
            }}
            className={assignment ? "text-ink-3 hover:text-ink" : "font-medium"}
          >
            {course.label}
          </button>
        </>
      )}
      {assignment && (
        <>
          <span className="text-ink-3">/</span>
          <span className="font-medium font-mono">{assignment}</span>
        </>
      )}
    </div>
  );

  if (courses && courses.length === 0) {
    return (
      <Placeholder
        title="Library"
        icon={Icon.Folder}
        body="Nothing here yet. Grade a class or a student and it'll show up, organized by course and assignment."
      />
    );
  }

  return (
    <div className="fade-up space-y-5">
      <div className="flex items-center justify-between">
        {crumb}
        {course && (
          <Button variant="ghost" onClick={back} className="px-2.5">
            ← Back
          </Button>
        )}
      </div>

      {/* Level 1: courses */}
      {!course && (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-hair">
            {(courses || []).map((c) => (
              <li key={c.course}>
                <button
                  onClick={() => openCourse(c)}
                  className="w-full px-6 py-3.5 flex items-center justify-between text-sm hover:bg-surface-3 transition-colors text-left"
                >
                  <span className="flex items-center gap-2.5">
                    <span className="text-accent"><Icon.Folder width={17} height={17} /></span>
                    <span className="font-medium">{c.label}</span>
                  </span>
                  <span className="text-ink-3">→</span>
                </button>
              </li>
            ))}
            {!courses && <li className="px-6 py-6 text-sm text-ink-3">Loading…</li>}
          </ul>
        </Card>
      )}

      {/* Level 2: assignments */}
      {course && !assignment && (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-hair">
            {(assignments || []).map((a) => (
              <li key={a}>
                <button
                  onClick={() => openAssignment(a)}
                  className="w-full px-6 py-3.5 flex items-center justify-between text-sm hover:bg-surface-3 transition-colors text-left"
                >
                  <Badge tone="accent">{a}</Badge>
                  <span className="text-ink-3">→</span>
                </button>
              </li>
            ))}
            {assignments && assignments.length === 0 && (
              <li className="px-6 py-6 text-sm text-ink-3">No assignments graded for this course yet.</li>
            )}
          </ul>
        </Card>
      )}

      {/* Level 3: students */}
      {assignment && data && (
        <>
          {data.master_workbook && (
            <Button onClick={() => api.openPath(data.master_workbook)}>
              Open instructor master
            </Button>
          )}
          <Card className="overflow-hidden">
            <div className="px-6 py-3 border-b border-hair text-sm font-medium flex items-center justify-between">
              <span>Students</span>
              <span className="font-mono text-xs text-ink-3">{data.students.length}</span>
            </div>
            <ul className="divide-y divide-hair">
              {data.students.map((s) => (
                <li
                  key={s.name}
                  className="px-6 py-3 flex items-center justify-between text-sm group"
                >
                  <span className="flex items-center gap-2.5">
                    <Dot tone="ok" />
                    <span className="font-medium">{s.name.replace(/_/g, " ")}</span>
                  </span>
                  <span className="flex items-center gap-2">
                    <RowAction onClick={() => onReview({ ...s, assignment })}>Review</RowAction>
                    {assignment === "MA2" && s.paper_file && (
                      <RowAction onClick={() => onPaper({ ...s, assignment })}>Paper</RowAction>
                    )}
                    <RowAction onClick={() => api.openPath(s.grade_file)}>Open</RowAction>
                    <RowAction subtle onClick={() => api.showItem(s.grade_file)}>Reveal</RowAction>
                  </span>
                </li>
              ))}
              {data.students.length === 0 && (
                <li className="px-6 py-6 text-sm text-ink-3">No graded students in this assignment.</li>
              )}
            </ul>
          </Card>
        </>
      )}
    </div>
  );
}

function RowAction({ children, onClick, subtle }) {
  return (
    <button
      onClick={onClick}
      className={
        "px-2.5 py-1 rounded-lg text-xs font-medium transition-all " +
        (subtle
          ? "text-ink-3 hover:text-ink hover:bg-surface-3"
          : "bg-surface-3 text-ink-2 hover:text-accent hover:bg-accent-soft")
      }
    >
      {children}
    </button>
  );
}

function Placeholder({ title, body, icon }) {
  const PIcon = icon;
  return (
    <div className="fade-up flex flex-col items-center justify-center py-24 text-center">
      <div className="w-12 h-12 rounded-2xl bg-surface-3 text-accent flex items-center justify-center mb-4">
        <PIcon width={22} height={22} />
      </div>
      <h1 className="text-xl font-medium">{title}</h1>
      <p className="text-ink-2 text-sm mt-2 max-w-md">{body}</p>
    </div>
  );
}
