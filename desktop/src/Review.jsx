import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Badge } from "./ui.jsx";
import { Icon } from "./icons.jsx";

// Reach the same preload bridge App.jsx uses.
const api =
  typeof window !== "undefined" && window.api
    ? window.api
    : {
        inspectWorkbook: async () => ({ sheets: [] }),
        inspectGrade: async () => ({ rows: [], total_possible: 0, total_awarded: 0 }),
        updateGrade: async () => ({ ok: true }),
        openPath: async () => {},
      };

const colLetter = (n) => {
  let s = "";
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
};

// Pull cell references (B30, $E$19, E19:E35) out of a feedback comment.
const CELL_RE = /\$?[A-Z]{1,3}\$?\d{1,4}(?::\$?[A-Z]{1,3}\$?\d{1,4})?/g;
const extractRefs = (text) => {
  if (!text || typeof text !== "string") return [];
  const found = text.match(CELL_RE) || [];
  return [...new Set(found)];
};
const firstCellOfRef = (ref) => ref.split(":")[0].replace(/\$/g, "");

export default function Review({ student, assignment, onBack }) {
  const [grade, setGrade] = useState(null);
  const [wb, setWb] = useState(null);
  const [activeSheet, setActiveSheet] = useState(0);
  const [edits, setEdits] = useState({}); // cell -> value
  const [highlight, setHighlight] = useState(null); // cell ref
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const [g, w] = await Promise.all([
          api.inspectGrade(student.grade_file, assignment),
          student.workbook_file
            ? api.inspectWorkbook(student.workbook_file)
            : Promise.resolve({ sheets: [] }),
        ]);
        if (!alive) return;
        if (g?.error) setLoadError(g.error);
        setGrade(g);
        setWb(w);
      } catch (e) {
        if (alive) setLoadError(e?.message || String(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [student, assignment]);

  const valueFor = useCallback(
    (cell, fallback) => (cell in edits ? edits[cell] : fallback),
    [edits]
  );

  const setCell = useCallback((cell, value) => {
    setEdits((e) => ({ ...e, [cell]: value }));
  }, []);

  const liveAwarded = useMemo(() => {
    if (!grade) return 0;
    let sum = 0;
    for (const r of grade.rows) {
      const v = valueFor(r.awarded_cell, r.awarded);
      const n = typeof v === "number" ? v : parseFloat(v);
      if (!Number.isNaN(n)) sum += n;
    }
    return Math.round(sum * 100) / 100;
  }, [grade, valueFor]);

  const dirty = Object.keys(edits).length > 0;

  const save = useCallback(async () => {
    if (!dirty) return;
    setSaving(true);
    try {
      const editList = Object.entries(edits).map(([cell, value]) => ({
        cell,
        value:
          /^F\d+$/.test(cell) && value !== "" && !Number.isNaN(parseFloat(value))
            ? parseFloat(value)
            : value,
      }));
      const res = await api.updateGrade(student.grade_file, editList);
      if (res?.ok) {
        // Re-pull fresh grade rows so awarded values reflect the save.
        const g = await api.inspectGrade(student.grade_file, assignment);
        setGrade(g);
        setEdits({});
        setSavedAt(Date.now());
      }
    } finally {
      setSaving(false);
    }
  }, [dirty, edits, student, assignment]);

  const jumpToCell = useCallback(
    (ref) => {
      const cell = firstCellOfRef(ref);
      setHighlight(cell);
      // Best-effort scroll to the highlighted cell.
      requestAnimationFrame(() => {
        const el = document.getElementById(`cell-${cell}`);
        if (el) el.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
      });
    },
    []
  );

  const sheets = wb?.sheets || [];
  const sheet = sheets[activeSheet];

  return (
    <div className="fade-up h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={onBack} className="px-2.5">
            <Icon.ArrowRight width={16} height={16} className="rotate-180" />
            Back
          </Button>
          <div>
            <div className="text-lg font-medium">{student.name.replace(/_/g, " ")}</div>
            <div className="text-xs text-ink-3 font-mono">{assignment} · review</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xl font-medium tabular-nums">
              {liveAwarded}
              <span className="text-ink-3"> / {grade?.total_possible ?? "—"}</span>
            </div>
            <div className="text-[10px] uppercase tracking-wide text-ink-3">points</div>
          </div>
          {student.workbook_file && (
            <Button variant="subtle" onClick={() => api.openPath(student.workbook_file)}>
              Open in Excel
            </Button>
          )}
          <Button onClick={save} disabled={!dirty || saving}>
            {saving ? "Saving…" : dirty ? "Save changes" : savedAt ? "Saved" : "Saved"}
          </Button>
        </div>
      </div>

      {loadError && (
        <Card className="p-4 mb-4 border-danger/30">
          <span className="text-sm text-danger">{loadError}</span>
        </Card>
      )}

      {/* Split panes */}
      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        {/* Left: editable rubric */}
        <Card className="flex flex-col min-h-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-hair text-sm font-medium shrink-0">
            Grade sheet
          </div>
          <div className="overflow-y-auto p-3 space-y-2.5">
            {loading && <div className="text-sm text-ink-3 p-3">Loading…</div>}
            {grade?.rows?.map((r) => {
              const awardedVal = valueFor(r.awarded_cell, r.awarded ?? "");
              const commentVal = valueFor(r.comment_cell, r.comment ?? "");
              const refs = extractRefs(r.comment);
              return (
                <div
                  key={r.row}
                  className="rounded-xl border border-hair bg-surface-2 p-3 space-y-2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="text-xs text-ink-2 leading-snug flex-1">
                      {r.section && (
                        <span className="font-medium text-ink">{r.section} · </span>
                      )}
                      {r.label}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max={r.possible}
                        value={awardedVal}
                        onChange={(e) => setCell(r.awarded_cell, e.target.value)}
                        className="w-14 text-right rounded-lg bg-surface border border-hair px-2 py-1 text-sm tabular-nums focus:outline-none focus:shadow-focus focus:border-accent"
                      />
                      <span className="text-xs text-ink-3 tabular-nums">/ {r.possible}</span>
                    </div>
                  </div>
                  <textarea
                    rows={2}
                    value={commentVal}
                    onChange={(e) => setCell(r.comment_cell, e.target.value)}
                    placeholder="Comment…"
                    className="w-full rounded-lg bg-surface border border-hair px-2.5 py-1.5 text-xs text-ink-2 resize-y focus:outline-none focus:shadow-focus focus:border-accent"
                  />
                  {refs.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {refs.map((ref) => (
                        <button
                          key={ref}
                          onClick={() => jumpToCell(ref)}
                          className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-accent-soft text-accent hover:shadow-glow-sm transition-all"
                          title="Highlight in workbook"
                        >
                          {ref}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        {/* Right: workbook grid */}
        <Card className="flex flex-col min-h-0 overflow-hidden">
          <div className="px-2 py-2 border-b border-hair shrink-0 flex gap-1 overflow-x-auto">
            {sheets.map((s, i) => (
              <button
                key={s.name}
                onClick={() => setActiveSheet(i)}
                className={
                  "px-2.5 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-all " +
                  (i === activeSheet
                    ? "bg-accent-soft text-accent"
                    : "text-ink-3 hover:text-ink hover:bg-surface-3")
                }
              >
                {s.name}
              </button>
            ))}
            {sheets.length === 0 && !loading && (
              <span className="text-xs text-ink-3 px-2 py-1">No workbook to show</span>
            )}
          </div>
          <div className="overflow-auto flex-1">
            {sheet ? <SheetGrid sheet={sheet} highlight={highlight} /> : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

function SheetGrid({ sheet, highlight }) {
  const { maxR, maxC, byRC } = useMemo(() => {
    let mr = 0;
    let mc = 0;
    const map = new Map();
    for (const c of sheet.cells) {
      mr = Math.max(mr, c.r);
      mc = Math.max(mc, c.c);
      map.set(`${c.r}:${c.c}`, c);
    }
    return { maxR: Math.min(mr, 120), maxC: Math.min(mc, 24), byRC: map };
  }, [sheet]);

  const rows = [];
  for (let r = 1; r <= maxR; r++) {
    const tds = [];
    for (let c = 1; c <= maxC; c++) {
      const cell = byRC.get(`${r}:${c}`);
      const ref = `${colLetter(c)}${r}`;
      const isHi = highlight === ref;
      const formula = cell?.f;
      const value = cell?.v;
      tds.push(
        <td
          key={c}
          id={`cell-${ref}`}
          title={formula ? `${ref}: ${formula}` : value != null ? `${ref}: ${value}` : ref}
          className={
            "border-r border-b border-hair px-1.5 py-0.5 text-[11px] whitespace-nowrap max-w-[160px] overflow-hidden text-ellipsis " +
            (isHi ? "bg-accent-soft text-accent ring-1 ring-accent" : "")
          }
        >
          {formula ? (
            <span className="font-mono text-ink-2">{formula}</span>
          ) : (
            <span className="text-ink">{value == null ? "" : String(value)}</span>
          )}
        </td>
      );
    }
    rows.push(
      <tr key={r}>
        <td className="sticky left-0 bg-surface-2 border-r border-b border-hair px-1.5 py-0.5 text-[10px] text-ink-3 text-right tabular-nums">
          {r}
        </td>
        {tds}
      </tr>
    );
  }

  return (
    <table className="border-collapse">
      <thead>
        <tr>
          <th className="sticky left-0 top-0 z-10 bg-surface-3 border-r border-b border-hair w-8" />
          {Array.from({ length: maxC }, (_, i) => (
            <th
              key={i}
              className="sticky top-0 bg-surface-3 border-r border-b border-hair px-1.5 py-0.5 text-[10px] text-ink-3 font-medium"
            >
              {colLetter(i + 1)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  );
}
