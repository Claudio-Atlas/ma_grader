import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Badge } from "./ui.jsx";
import { Icon } from "./icons.jsx";

const api =
  typeof window !== "undefined" && window.api
    ? window.api
    : {
        inspectPaper: async () => ({ criteria: [], total_possible: 42 }),
        paperText: async () => ({ ok: true, text: "" }),
        paperAiGrade: async () => ({ error: "unavailable" }),
        updateGrade: async () => ({ ok: true }),
        paperFeedbackPdf: async () => ({ canceled: true }),
        openPath: async () => {},
      };

export default function PaperGrade({ student, scores, onScores, onBack }) {
  const [paper, setPaper] = useState(null); // {criteria, total_possible}
  const [docText, setDocText] = useState("");
  const [docErr, setDocErr] = useState("");
  const [sel, setSel] = useState({}); // key -> {level, points, comment}
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiModel, setAiModel] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      const [p, d] = await Promise.all([
        api.inspectPaper(student.grade_file),
        student.paper_file ? api.paperText(student.paper_file) : Promise.resolve({ ok: false }),
      ]);
      if (!alive) return;
      setPaper(p);
      // Prefer scores already held in the app (from a batch AI run or earlier
      // edits this session); otherwise seed from the grade sheet.
      if (scores && Object.keys(scores).length) {
        setSel(scores);
      } else {
        const seed = {};
        (p?.criteria || []).forEach((c) => {
          if (c.selected_level) {
            const lvl = c.levels.find((l) => l.level === c.selected_level);
            seed[c.key] = { level: c.selected_level, points: lvl?.points ?? c.awarded, comment: c.comment || "" };
          } else if (c.comment) {
            seed[c.key] = { level: null, points: null, comment: c.comment };
          }
        });
        setSel(seed);
      }
      if (d?.ok) setDocText(d.text || "");
      else setDocErr(d?.error || "No paper attached to this student.");
      setLoading(false);
    })();
    return () => {
      alive = false;
    };
  }, [student]);

  const setLevel = useCallback((crit, level) => {
    const lvl = crit.levels.find((l) => l.level === level);
    setSel((s) => ({
      ...s,
      [crit.key]: { level, points: lvl?.points ?? 0, comment: s[crit.key]?.comment || "" },
    }));
  }, []);

  const setComment = useCallback((key, comment) => {
    setSel((s) => ({ ...s, [key]: { ...(s[key] || { level: null, points: null }), comment } }));
  }, []);

  // Keep the app-level score store in sync so the batch "Download all PDFs"
  // and re-opening a student reflect the latest edits.
  useEffect(() => {
    if (onScores && Object.keys(sel).length) onScores(student.name, sel);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  const total = useMemo(() => {
    let t = 0;
    for (const k in sel) {
      const p = sel[k]?.points;
      if (typeof p === "number") t += p;
    }
    return Math.round(t * 100) / 100;
  }, [sel]);

  const dirty = Object.keys(sel).length > 0;

  const runAi = useCallback(async () => {
    setAiBusy(true);
    setAiError("");
    try {
      let strictness = "standard";
      let model = "claude-sonnet-4-6";
      try {
        strictness = localStorage.getItem("ma-ai-strictness") || "standard";
        model = localStorage.getItem("ma-ai-model") || "claude-sonnet-4-6";
      } catch {}
      const res = await api.paperAiGrade(student.paper_file, strictness, model);
      if (res?.error) {
        setAiError(res.error);
        return;
      }
      setAiModel(res.model || "");
      const byKey = {};
      (paper?.criteria || []).forEach((c) => (byKey[c.key] = c));
      const next = {};
      (res.suggestions || []).forEach((s) => {
        next[s.key] = { level: s.level, points: s.points, comment: s.comment || "" };
      });
      setSel((prev) => ({ ...prev, ...next }));
    } finally {
      setAiBusy(false);
    }
  }, [student, paper]);

  const [pdfBusy, setPdfBusy] = useState(false);

  const downloadPdf = useCallback(async () => {
    if (!paper) return;
    setPdfBusy(true);
    try {
      let sum = 0;
      const criteria = (paper.criteria || []).map((c) => {
        const s = sel[c.key] || {};
        const lvl = (c.levels || []).find((l) => l.level === s.level);
        const points = typeof s.points === "number" ? s.points : 0;
        sum += points;
        return {
          name: c.name,
          possible: c.possible,
          levelName: lvl ? lvl.name : "Not scored",
          points,
          description: lvl ? lvl.description : "",
          comment: s.comment || "",
        };
      });
      await api.paperFeedbackPdf({
        studentName: student.name.replace(/_/g, " "),
        assignment: "MA2",
        total: Math.round(sum * 100) / 100,
        possible: paper.total_possible || 42,
        criteria,
      });
    } finally {
      setPdfBusy(false);
    }
  }, [paper, sel, student]);

  return (
    <div className="fade-up h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={onBack} className="px-2.5">
            <Icon.ArrowRight width={16} height={16} className="rotate-180" />
            Back
          </Button>
          <div>
            <div className="text-lg font-medium">{student.name.replace(/_/g, " ")}</div>
            <div className="text-xs text-ink-3 font-mono">MA2 · written paper</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xl font-medium tabular-nums">
              {total}
              <span className="text-ink-3"> / {paper?.total_possible ?? 42}</span>
            </div>
            <div className="text-[10px] uppercase tracking-wide text-ink-3">paper points</div>
          </div>
          <Button variant="soft" onClick={runAi} disabled={aiBusy || !student.paper_file}>
            <Icon.Bolt width={15} height={15} />
            {aiBusy ? "Grading…" : "AI suggest"}
          </Button>
          <Button onClick={downloadPdf} disabled={pdfBusy || !dirty}>
            {pdfBusy ? "Preparing…" : "Download feedback PDF"}
          </Button>
        </div>
      </div>

      {aiError && (
        <Card className="p-3 mb-3 border-danger/30">
          <span className="text-sm text-danger">{aiError}</span>
        </Card>
      )}
      {aiModel && !aiError && (
        <div className="mb-3 text-xs text-ink-3">
          AI suggestions from {aiModel} — review and adjust before saving.
        </div>
      )}

      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        {/* Paper text */}
        <Card className="flex flex-col min-h-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-hair text-sm font-medium shrink-0 flex items-center justify-between">
            <span>Write-up</span>
            {student.paper_file && (
              <button
                onClick={() => api.openPath(student.paper_file)}
                className="text-xs text-ink-3 hover:text-accent"
              >
                Open original
              </button>
            )}
          </div>
          <div className="overflow-y-auto p-4 text-sm text-ink-2 whitespace-pre-wrap leading-relaxed">
            {loading ? "Loading…" : docErr ? <span className="text-ink-3">{docErr}</span> : docText}
          </div>
        </Card>

        {/* Criteria */}
        <Card className="flex flex-col min-h-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-hair text-sm font-medium shrink-0">
            Rubric · {paper?.criteria?.length || 0} criteria
          </div>
          <div className="overflow-y-auto p-3 space-y-3">
            {paper?.criteria?.map((c) => {
              const chosen = sel[c.key];
              return (
                <div key={c.key} className="rounded-xl border border-hair bg-surface-2 p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium">{c.name}</div>
                    <div className="text-xs text-ink-3 tabular-nums">
                      {typeof chosen?.points === "number" ? chosen.points : "—"} / {c.possible}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {c.levels.map((l) => {
                      const active = chosen?.level === l.level;
                      return (
                        <button
                          key={l.level}
                          title={`${l.name} · ${l.points} pts — ${l.description}`}
                          onClick={() => setLevel(c, l.level)}
                          className={
                            "flex-1 py-1.5 rounded-lg text-xs font-medium transition-all " +
                            (active
                              ? "bg-accent text-ink-inv shadow-glow-sm"
                              : "bg-surface border border-hair text-ink-2 hover:text-ink hover:border-accent/50")
                          }
                        >
                          {l.level}
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[10px] text-ink-3 px-0.5">
                    <span>Unsatisfactory</span>
                    <span>Target</span>
                  </div>
                  <textarea
                    rows={2}
                    value={chosen?.comment || ""}
                    onChange={(e) => setComment(c.key, e.target.value)}
                    placeholder="Comment…"
                    className="w-full rounded-lg bg-surface border border-hair px-2.5 py-1.5 text-xs text-ink-2 resize-y focus:outline-none focus:shadow-focus focus:border-accent"
                  />
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
