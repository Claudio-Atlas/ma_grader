import React, { useCallback, useEffect, useRef, useState } from "react";
import { Button, Card, Segmented, Stat, Badge, Dot } from "./ui.jsx";
import { Icon } from "./icons.jsx";
import Review from "./Review.jsx";
import PaperGrade from "./PaperGrade.jsx";

// ---- Browser-preview stand-in for the engine (never used inside Electron) ----
const previewListeners = new Set();
const PREVIEW_NAMES = ["Avery_Chen", "Jordan_Patel", "Sam_Okafor", "Riley_Brooks", "Morgan_Diaz", "Taylor_Nguyen", "Casey_Moreau", "Quinn_Alvarez"];
async function previewRun() {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < PREVIEW_NAMES.length; i++) {
    previewListeners.forEach((fn) => fn({ type: "progress", current: i + 1, total: PREVIEW_NAMES.length, student: PREVIEW_NAMES[i] }));
    await wait(700);
  }
  return {
    success_count: PREVIEW_NAMES.length,
    students: PREVIEW_NAMES.map((name) => ({ name, status: "graded", grade_file: `/demo/${name}_Grade.xlsx` })),
    issues: [{ student: "Quinn_Alvarez", problem: "Missing the Annual Budget tab.", action: "Ask the student to resubmit with all tabs." }],
    master_workbook: "/demo/INSTRUCTOR_MASTER.xlsx",
    graded_path: "/demo",
  };
}

// Fallback so the UI renders outside Electron (plain browser preview).
const api =
  typeof window !== "undefined" && window.api
    ? window.api
    : {
        getPathForFile: () => null,
        // Preview-only sample data so every screen can be seen in a browser.
        pickZip: async () => "/Users/demo/Downloads/submissions.zip",
        pickWorkbook: async () => "/Users/demo/Downloads/Late_Student_MA2.xlsx",
        pickPaper: async () => null,
        pickFolder: async () => null,
        openPath: async () => {},
        showItem: async () => {},
        runGrading: (opts) => previewRun(opts),
        runGradingOne: (opts) => previewRun(opts),
        onGradeEvent: (fn) => {
          previewListeners.add(fn);
          return () => previewListeners.delete(fn);
        },
        keySave: async () => ({ ok: true }),
        keyStatus: async () => ({ hasKey: false }),
        keyClear: async () => ({ ok: true }),
        keyTest: async () => ({ ok: false, error: "unavailable" }),
        historyList: async () => [
          { id: "1", date: "2026-10-12T15:00:00Z", course: "MAT 144 · Section 01", assignment: "MA2", mode: "class", success_count: 31, issue_count: 3, students: [], issues: [] },
          { id: "2", date: "2026-09-21T15:00:00Z", course: "MAT 144 · Section 01", assignment: "MA1", mode: "class", success_count: 32, issue_count: 0, students: [], issues: [] },
        ],
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
  // Native window materials follow too (no-op outside Electron).
  try {
    window.api?.setTheme?.(mode);
  } catch {}
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
      // (macOS/Linux "/…", Windows "C:\\…" or "\\\\server\\…")
      if (full && /^(\/|[A-Za-z]:[\\/]|\\\\)/.test(full)) setZipPath(full);
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
              ...aiNotePrefs(),
            })
          : await api.runGrading({
              zipPath,
              course: course.trim(),
              assignment,
              workspace: outputFolder || undefined,
              ...aiNotePrefs(),
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

  // Each screen opens at the top (the scroll position used to carry over, so a
  // screen could open scrolled past its content and look blank).
  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [nav, phase, reviewStudent, paperStudent]);

  return (
    <div className="h-full flex text-ink font-sans">
      <Sidebar nav={nav} setNav={setNav} theme={theme} cycleTheme={cycleTheme} />

      <div className="app-main flex-1 flex flex-col min-w-0 bg-bg">
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
            <div ref={scrollRef} className="flex-1 overflow-y-auto">
              <div className="max-w-[720px] mx-auto px-10 pt-4 pb-12">
                {nav === "run" && phase === "setup" && (
                  <SetupScreen
                    {...{
                      mode, setMode, zipPath, workbookPath, studentName, setStudentName,
                      paperPath, setPaperPath, course, setCourse, assignment, setAssignment,
                      outputFolder, dragging, setDragging, onDrop, pickZip, pickWorkbook,
                      pickPaper, pickFolder, canRun, run, onOpenRun: openHistory,
                    }}
                  />
                )}
                {nav === "run" && phase === "running" && (
                  <RunningScreen progress={progress} assignment={assignment} course={course} />
                )}
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
  const groups = [
    [
      { id: "run", label: "New run", icon: Icon.Plus },
      { id: "library", label: "Library", icon: Icon.Folder },
      { id: "history", label: "History", icon: Icon.Clock },
    ],
    [{ id: "manual", label: "Manual grade", icon: Icon.Pencil, badge: "MA2" }],
  ];
  const ThemeIcon = theme === "dark" ? Icon.Moon : theme === "light" ? Icon.Sun : Icon.Monitor;

  const Item = ({ it }) => {
    const ItIcon = it.icon;
    const active = nav === it.id;
    return (
      <button
        onClick={() => setNav(it.id)}
        className={
          "w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg text-[13px] transition-colors duration-100 " +
          (active
            ? "bg-accent-soft text-ink font-medium"
            : "text-ink-2 hover:bg-ink/[0.04] hover:text-ink")
        }
      >
        <ItIcon width={16} height={16} className={active ? "text-accent" : "text-ink-3"} />
        <span className="flex-1 text-left">{it.label}</span>
        {it.badge && (
          <span className="text-[10.5px] font-medium px-1.5 py-px rounded-full bg-manual-soft text-manual">
            {it.badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside className="app-sidebar w-[232px] shrink-0 bg-side border-r border-hair flex flex-col titlebar-drag">
      {/* Room for the macOS window buttons, which sit inside the sidebar. */}
      <div className="h-[52px] shrink-0" />
      <div className="flex items-center gap-2.5 px-4 pb-4">
        <div className="w-[26px] h-[26px] rounded-[7px] bg-accent text-ink-inv flex items-center justify-center shadow-raise">
          <Icon.Mark width={14} height={14} />
        </div>
        <div className="text-[13.5px] font-semibold tracking-tight">MA Grader</div>
      </div>

      <nav className="px-2.5 titlebar-no-drag">
        <div className="space-y-px">
          {groups[0].map((it) => <Item key={it.id} it={it} />)}
        </div>
        <div className="text-[11px] font-medium text-ink-3 px-2.5 pt-4 pb-1.5">Review</div>
        <div className="space-y-px">
          {groups[1].map((it) => <Item key={it.id} it={it} />)}
        </div>
      </nav>

      <div className="mt-auto px-2.5 pb-3 titlebar-no-drag flex items-center gap-1">
        <div className="flex-1">
          <Item it={{ id: "settings", label: "Settings", icon: Icon.Sliders }} />
        </div>
        <button
          onClick={cycleTheme}
          title={`Appearance: ${theme} (click to change)`}
          aria-label={`Appearance: ${theme}`}
          className="w-8 h-8 shrink-0 flex items-center justify-center rounded-lg text-ink-3 hover:text-ink hover:bg-ink/[0.04] transition-colors"
        >
          <ThemeIcon width={15} height={15} />
        </button>
      </div>
    </aside>
  );
}

function TopBar({ crumb, course }) {
  const [main, sub] = crumb;
  return (
    <header className="titlebar-drag h-[52px] shrink-0 flex items-center justify-between px-6">
      <div className="flex items-center gap-1.5 text-[12.5px] text-ink-3">
        <span>{main}</span>
        {sub && (
          <>
            <span className="text-ink-3/60">/</span>
            <span className="text-ink-2">{sub}</span>
          </>
        )}
      </div>
      {course && (
        <div className="text-[12px] text-ink-2 px-2.5 py-1 rounded-full bg-surface-2 border border-hair">
          {course}
        </div>
      )}
    </header>
  );
}

// ---------------------------------------------------------------------------
// Screens
// ---------------------------------------------------------------------------
const ASSIGNMENT_INFO = {
  MA1: "Currency & unit conversion, income analysis",
  MA2: "Income projection, budget, credit cards, loans",
  MA3: "Descriptive statistics & histogram",
};

const inputCls =
  "titlebar-no-drag w-full rounded-[9px] bg-surface border border-hair px-3 py-2 text-[13.5px] text-ink placeholder:text-ink-3 focus:outline-none focus:shadow-focus focus:border-transparent transition-shadow";

function SetupScreen(props) {
  const {
    mode, setMode, zipPath, workbookPath, studentName, setStudentName, paperPath,
    setPaperPath, course, setCourse, assignment, setAssignment, outputFolder,
    dragging, setDragging, onDrop, pickZip, pickWorkbook, pickPaper, pickFolder,
    canRun, run, onOpenRun,
  } = props;

  const single = mode === "single";
  // Progressive: the details appear once there's something to grade.
  const ready = single ? !!workbookPath : !!zipPath;

  return (
    <div className="space-y-6 fade-up">
      <div>
        <h1 className="text-[30px] leading-tight font-semibold tracking-[-0.025em]">
          {ready ? "Ready to grade" : single ? "Grade one student" : "Grade a class"}
        </h1>
        <p className="text-ink-2 text-[14.5px] mt-2 leading-relaxed">
          {ready
            ? "Check the details, then start. Nothing is written until you press Grade."
            : single
            ? "Choose a late or resubmitted workbook. It merges into the existing class."
            : "Drop the submissions ZIP from Canvas. MA Grader grades every workbook and builds your master sheet."}
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
        />
      ) : (
        <FileCard
          icon={Icon.File}
          value={workbookPath}
          onPick={pickWorkbook}
          placeholder="Choose the student's .xlsx"
        />
      )}

      {ready && (
        <div className="space-y-7 fade-up">
          <Field label="Assignment">
            <div className="grid grid-cols-3 gap-2.5">
              {ASSIGNMENTS.map((a) => {
                const on = assignment === a.value;
                return (
                  <button
                    key={a.value}
                    onClick={() => setAssignment(a.value)}
                    aria-pressed={on}
                    className={
                      "titlebar-no-drag text-left rounded-xl px-3.5 py-3 border transition-colors " +
                      (on
                        ? "bg-accent-soft border-accent"
                        : "bg-surface border-hair hover:border-hair-strong")
                    }
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[14px] font-semibold">{a.label}</span>
                      <span
                        className={
                          "w-4 h-4 rounded-full flex items-center justify-center " +
                          (on ? "bg-accent text-ink-inv" : "border-[1.5px] border-hair-strong")
                        }
                      >
                        {on && <Icon.Mark width={9} height={9} />}
                      </span>
                    </div>
                    <div className="text-[12px] text-ink-2 mt-1.5 leading-snug">
                      {ASSIGNMENT_INFO[a.value]}
                    </div>
                  </button>
                );
              })}
            </div>
          </Field>

          <div className="grid grid-cols-2 gap-x-4 gap-y-5">
            {single && (
              <Field label="Student name" hint="Names the graded file">
                <input
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="First Last"
                  className={inputCls}
                />
              </Field>
            )}
            <Field label="Course" hint={single ? "Must match the class" : "Names the output folder"}>
              <input
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                placeholder="MAT 144 Online"
                className={inputCls}
              />
            </Field>
            <Field label="Save to" hint={outputFolder ? "This run only" : "Your Library folder"}>
              <div className="flex items-center gap-2">
                <button
                  onClick={pickFolder}
                  className={inputCls + " flex items-center gap-2 text-left hover:border-hair-strong"}
                  title={outputFolder || "Choose a different folder for this run"}
                >
                  <Icon.Folder width={15} height={15} className="text-ink-3 shrink-0" />
                  <span className="truncate font-mono text-[12.5px] text-ink-2">
                    {outputFolder || "Library folder"}
                  </span>
                </button>
              </div>
            </Field>
            {single && assignment === "MA2" && (
              <Field label="Write-up paper" hint="Optional, for manual grading">
                <FilePick
                  inline
                  icon={Icon.Doc}
                  value={paperPath}
                  onPick={pickPaper}
                  placeholder=".docx or .pdf"
                  onClear={() => setPaperPath(null)}
                />
              </Field>
            )}
          </div>

          <div className="flex items-center justify-between pt-5 border-t border-hair">
            <span className="text-[12.5px] text-ink-3">
              {course.trim() ? `${assignment} · ${course.trim()}` : "Add a course name to continue"}
            </span>
            <Button onClick={run} disabled={!canRun} className="px-5">
              {single ? "Grade student" : "Grade submissions"}
              <Icon.ArrowRight width={16} height={16} />
            </Button>
          </div>
        </div>
      )}

      {!ready && !single && <RecentRuns onOpen={onOpenRun} />}
    </div>
  );
}

function RecentRuns({ onOpen }) {
  const [runs, setRuns] = useState(null);
  useEffect(() => {
    let alive = true;
    api.historyList().then((r) => alive && setRuns((r || []).slice(0, 3)));
    return () => {
      alive = false;
    };
  }, []);
  if (!runs || runs.length === 0) return null;
  const when = (iso) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return "";
    }
  };
  return (
    <div className="pt-4">
      <div className="text-[13px] font-semibold mb-2">Recent runs</div>
      <ul className="border-t border-hair">
        {runs.map((r) => (
          <li key={r.id}>
            <button
              onClick={() => onOpen && onOpen(r)}
              className="titlebar-no-drag w-full flex items-center justify-between gap-4 py-3 px-1 border-b border-hair text-left hover:bg-ink/[0.025] transition-colors"
            >
              <span>
                <span className="block text-[13px] font-medium">
                  {r.assignment} · {r.course}
                </span>
                <span className="block text-[12px] text-ink-3 mt-0.5">
                  {when(r.date)} · {r.success_count} graded
                </span>
              </span>
              {r.issue_count ? (
                <Badge tone="warn">{r.issue_count} to check</Badge>
              ) : (
                <Badge tone="ok">Complete</Badge>
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DropArea({ onDrop, onClick, setDragging, dragging, selected }) {
  if (selected) {
    return (
      <FileCard icon={Icon.File} value={selected} onPick={onClick} placeholder="" onDrop={onDrop} setDragging={setDragging} />
    );
  }
  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onClick()}
      className={
        "drop-hero cursor-pointer rounded-2xl px-6 pt-14 pb-12 text-center titlebar-no-drag transition-[box-shadow,transform] duration-200 focus:outline-none focus-visible:shadow-focus " +
        (dragging ? "is-dragging scale-[1.005]" : "")
      }
    >
      <div className="relative w-16 h-16 mx-auto mb-5">
        <span className="absolute inset-0 rounded-xl bg-surface border border-hair-strong -rotate-[9deg] -translate-x-1.5 opacity-60" />
        <span className="absolute inset-0 rounded-xl bg-surface border border-hair-strong rotate-6 translate-x-1.5 opacity-80" />
        <span className="absolute inset-0 rounded-xl bg-surface border border-hair-strong shadow-raise flex items-center justify-center text-accent">
          <Icon.Upload width={24} height={24} />
        </span>
      </div>
      <div className="text-[17px] font-semibold tracking-[-0.015em]">Drop a submissions ZIP</div>
      <div className="text-[13px] text-ink-2 mt-1.5">
        or <span className="text-accent font-medium">choose a file</span> from your computer
      </div>
      <div className="text-[12px] text-ink-3 mt-5">
        The .zip from Canvas &ldquo;Download Submissions&rdquo;
      </div>
    </div>
  );
}

function FileCard({ icon, value, onPick, placeholder, onDrop, setDragging }) {
  const FIcon = icon;
  return (
    <div
      onDragOver={onDrop ? (e) => { e.preventDefault(); setDragging && setDragging(true); } : undefined}
      onDragLeave={onDrop ? () => setDragging && setDragging(false) : undefined}
      onDrop={onDrop}
      className="flex items-center gap-3.5 px-4 py-3.5 rounded-2xl bg-surface border border-hair shadow-card titlebar-no-drag"
    >
      <div className="w-10 h-10 rounded-[10px] bg-accent-soft text-accent flex items-center justify-center shrink-0">
        <FIcon width={20} height={20} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[14px] font-semibold tracking-[-0.01em] truncate">
          {value ? basename(value) : placeholder}
        </div>
        {value && <div className="text-[12px] text-ink-3 truncate mt-0.5 font-mono">{value}</div>}
      </div>
      <Button variant={value ? "ghost" : "subtle"} onClick={onPick}>
        {value ? "Replace" : "Choose…"}
      </Button>
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
    <div className="space-y-1.5 min-w-0">
      <div className="flex items-baseline justify-between gap-3">
        <label className="text-[12.5px] font-medium text-ink-2">{label}</label>
        {hint && <span className="text-[11.5px] text-ink-3 truncate">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

const prettyName = (n) => (n || "").replace(/_/g, " ");
const initials = (n) =>
  prettyName(n)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");

function Avatar({ name }) {
  return (
    <span className="w-[26px] h-[26px] shrink-0 rounded-full bg-surface-2 border border-hair text-[10.5px] font-semibold text-ink-2 flex items-center justify-center">
      {initials(name) || "?"}
    </span>
  );
}

function RunningScreen({ progress, assignment, course }) {
  // The engine reports "student N of M" as it starts each one; when the next
  // one starts, the previous one is done. Keep the finished names to show a
  // live list, and time per student for an estimate.
  const [done, setDone] = useState([]);
  const [startedAt] = useState(() => Date.now());
  const lastRef = useRef(null);
  useEffect(() => {
    const cur = progress.student;
    if (cur && cur !== lastRef.current) {
      if (lastRef.current) setDone((d) => [lastRef.current, ...d]);
      lastRef.current = cur;
    }
  }, [progress.student]);

  const { current, total } = progress;
  const finished = Math.max(0, current - 1);
  const pct = total > 0 ? (finished / total) * 100 : 0;
  const perStudent = finished > 0 ? (Date.now() - startedAt) / finished : null;
  const left = perStudent && total ? Math.round(((total - finished) * perStudent) / 1000) : null;
  const eta = left == null ? "" : left < 60 ? `About ${Math.max(1, left)} s left` : `About ${Math.round(left / 60)} min left`;

  return (
    <div className="space-y-6 fade-up">
      <div className="flex items-end justify-between gap-6">
        <div>
          <h1 className="text-[30px] leading-tight font-semibold tracking-[-0.025em]">Grading {assignment}</h1>
          <p className="text-ink-2 text-[14.5px] mt-1">{course}</p>
        </div>
        <div className="text-[44px] leading-none font-semibold tracking-[-0.035em] num">
          {finished}
          <span className="text-[18px] text-ink-3 font-medium tracking-normal"> / {total || "…"}</span>
        </div>
      </div>

      <div>
        <div className="h-1.5 rounded-full bg-surface-2 border border-hair overflow-hidden">
          <div
            className={"h-full rounded-full bg-accent transition-[width] duration-500 ease-out " + (total ? "" : "animate-pulse")}
            style={{ width: `${total ? Math.max(pct, 2) : 12}%` }}
          />
        </div>
        <div className="flex justify-between text-[12px] text-ink-3 mt-2">
          <span>{progress.student ? `Grading ${prettyName(progress.student)}` : "Preparing submissions…"}</span>
          <span>{eta}</span>
        </div>
      </div>

      <div>
        <div className="text-[13px] font-semibold mb-2">Students</div>
        <ul className="border-t border-hair">
          {progress.student && (
            <li className="flex items-center gap-3 py-2.5 px-1 border-b border-hair text-ink-3">
              <Avatar name={progress.student} />
              <span className="flex-1 text-[13px]">{prettyName(progress.student)}</span>
              <span className="w-3 h-3 rounded-full border-[1.5px] border-hair-strong border-t-accent animate-spin" />
            </li>
          )}
          {done.slice(0, 8).map((n) => (
            <li key={n} className="flex items-center gap-3 py-2.5 px-1 border-b border-hair fade-up">
              <Avatar name={n} />
              <span className="flex-1 text-[13px] font-medium">{prettyName(n)}</span>
              <Badge tone="ok">Graded</Badge>
            </li>
          ))}
        </ul>
        {done.length > 8 && (
          <div className="text-[12px] text-ink-3 mt-2">and {done.length - 8} more</div>
        )}
      </div>
    </div>
  );
}

function ResultsScreen({ result, assignment, onReset, onReview }) {
  const students = result?.students || [];
  const issues = result?.issues || [];
  const graded = result?.success_count ?? students.length;

  return (
    <div className="space-y-7 fade-up">
      <div className="flex items-end justify-between gap-6">
        <div>
          <h1 className="text-[30px] leading-tight font-semibold tracking-[-0.025em]">Grading complete</h1>
          <p className="text-ink-2 text-[14.5px] mt-1">
            {assignment} · {graded} {graded === 1 ? "student" : "students"} graded
            {issues.length ? `, ${issues.length} to check` : ""}
          </p>
        </div>
        <Button variant="subtle" onClick={onReset}>
          <Icon.Plus width={15} height={15} />
          Grade another
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-2.5">
        {[
          ["Graded", graded, "text-ink"],
          ["To check", issues.length, issues.length ? "text-warning" : "text-ink"],
          ["Assignment", assignment, "text-ink"],
        ].map(([l, v, tone]) => (
          <div key={l} className="rounded-xl bg-surface border border-hair px-4 py-3">
            <div className="text-[11.5px] text-ink-3">{l}</div>
            <div className={`text-[22px] font-semibold tracking-[-0.02em] mt-0.5 num ${tone}`}>{v}</div>
          </div>
        ))}
      </div>

      {(result?.master_workbook || result?.graded_path) && (
        <div className="flex flex-wrap gap-2.5">
          {result?.master_workbook && (
            <Button onClick={() => api.openPath(result.master_workbook)}>
              Open instructor master
              <Icon.ArrowRight width={16} height={16} />
            </Button>
          )}
          {result?.graded_path && (
            <Button variant="subtle" onClick={() => api.openPath(result.graded_path)}>
              <Icon.Folder width={15} height={15} />
              Open graded folder
            </Button>
          )}
        </div>
      )}

      {issues.length > 0 && (
        <div className="rounded-2xl bg-warning-soft px-5 py-4">
          <div className="text-[13px] font-semibold flex items-center gap-2 text-warning">
            <Icon.Alert width={15} height={15} />
            Needs a look
          </div>
          <ul className="mt-2.5 space-y-2.5">
            {issues.map((it, i) => (
              <li key={i} className="text-[13px]">
                <span className="font-medium">{prettyName(it.student || "Unknown")}</span>
                <span className="text-ink-2">: {it.problem}</span>
                {it.action && <div className="text-[12px] text-ink-3 mt-0.5">{it.action}</div>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <div className="flex items-baseline justify-between mb-2">
          <div className="text-[13px] font-semibold">Students</div>
          <div className="text-[12px] text-ink-3 num">{students.length}</div>
        </div>
        <ul className="border-t border-hair">
          {students.map((s, i) => (
            <li key={i}>
              <button
                onClick={() => onReview && s.grade_file && onReview(s)}
                disabled={!s.grade_file}
                className="titlebar-no-drag w-full flex items-center gap-3 py-2.5 px-1 border-b border-hair text-left hover:bg-ink/[0.025] transition-colors disabled:cursor-default group"
              >
                <Avatar name={s.name} />
                <span className="flex-1 text-[13px] font-medium">{prettyName(s.name)}</span>
                {s.grade_file && (
                  <span className="text-[12px] text-ink-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    Review
                  </span>
                )}
                <Badge tone="ok">{(s.status || "graded").replace(/^./, (c) => c.toUpperCase())}</Badge>
              </button>
            </li>
          ))}
          {students.length === 0 && (
            <li className="py-8 text-[13px] text-ink-3 text-center">No graded files were produced.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

function ErrorScreen({ message, onReset }) {
  return (
    <div className="fade-up flex flex-col items-center justify-center py-24 text-center">
      <div className="w-12 h-12 rounded-2xl bg-danger-soft text-danger flex items-center justify-center mb-4">
        <Icon.Alert width={24} height={24} />
      </div>
      <h1 className="text-[20px] font-semibold tracking-[-0.015em]">Something went wrong</h1>
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
      <h1 className="text-[30px] leading-tight font-semibold tracking-[-0.025em]">Settings</h1>
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
      <AiNotesToggle />
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

// Whether grading runs ask Claude to write each student's overall note (the
// rule-based note is used otherwise, or whenever the AI call fails).
function aiNotePrefs() {
  try {
    return {
      aiNotes: localStorage.getItem("ma-ai-notes") === "1",
      model: localStorage.getItem("ma-ai-model") || undefined,
    };
  } catch {
    return { aiNotes: false };
  }
}

function AiNotesToggle() {
  const [on, setOn] = useState(false);
  useEffect(() => {
    try {
      setOn(localStorage.getItem("ma-ai-notes") === "1");
    } catch {}
  }, []);
  const toggle = () => {
    const next = !on;
    try {
      localStorage.setItem("ma-ai-notes", next ? "1" : "0");
    } catch {}
    setOn(next);
  };
  return (
    <div className="pt-3 border-t border-hair flex items-start justify-between gap-4">
      <div>
        <div className="text-sm font-medium">Write overall notes with AI</div>
        <p className="text-xs text-ink-3 mt-1">
          Claude writes each student's overall note from their grading results. Student names
          are never sent. Off: a built-in note is used instead.
        </p>
      </div>
      <button
        role="switch"
        aria-checked={on}
        onClick={toggle}
        className={
          "titlebar-no-drag shrink-0 w-10 h-6 rounded-full p-0.5 transition-colors " +
          (on ? "bg-accent" : "bg-surface-3 border border-hair")
        }
      >
        <span
          className={
            "block w-5 h-5 rounded-full bg-white shadow transition-transform " +
            (on ? "translate-x-4" : "translate-x-0")
          }
        />
      </button>
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
          <h1 className="text-[30px] leading-tight font-semibold tracking-[-0.025em]">Manual paper grading</h1>
          <p className="text-ink-2 text-[14.5px] mt-2 leading-relaxed">
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
          <h1 className="text-[30px] leading-tight font-semibold tracking-[-0.025em]">History</h1>
          <p className="text-ink-2 text-[14.5px] mt-2 leading-relaxed">
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
