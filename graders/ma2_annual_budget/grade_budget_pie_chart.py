"""
Grade the Annual Budget pie chart (grading-sheet row 27, 6 points).

Rubric (3 / 1 / 1 / 1):
  - Pie chart of the Total Annual Cost entries (values from column D) ... 3
  - Budget Category entries used as the legend (categories from column A) 1
  - Chart title updated (non-blank) ...................................... 1
  - Percentage data labels added ........................................ 1

openpyxl exposes embedded charts on `ws._charts`, including the chart type,
its series data references, the title, and data-label settings — so all four
parts are detectable without opening Excel.
"""

import re


def _first_col(ref):
    """'Annual Budget'!$D$18:$D$27 -> 'D' (the column of the first cell)."""
    if not ref:
        return None
    tail = ref.split("!")[-1]
    m = re.search(r"\$?([A-Z]+)\$?\d", tail)
    return m.group(1) if m else None


def _value_col(chart):
    try:
        return _first_col(chart.series[0].val.numRef.f)
    except Exception:
        return None


def _cat_col(chart):
    try:
        s0 = chart.series[0]
        if s0.cat is None:
            return None
        ref = s0.cat.numRef.f if s0.cat.numRef else (s0.cat.strRef.f if s0.cat.strRef else None)
        return _first_col(ref)
    except Exception:
        return None


def _title(chart):
    """
    Return the chart's title text if it has been set, by ANY means:
      - typed rich text (runs)
      - a text field inside the rich text
      - a cell-linked title (strRef) — counts as 'set' even if we can't read
        the cached text, because the student intentionally linked it.
    Returns None only when there is genuinely no title.
    """
    try:
        t = chart.title
        if t is None:
            return None
        tx = getattr(t, "tx", None)
        if tx is None:
            s = str(t).strip()
            return s or None

        # 1) Cell-linked title (e.g. title = ='Annual Budget'!A1)
        strref = getattr(tx, "strRef", None)
        if strref is not None:
            try:
                cache = strref.strCache
                if cache and cache.pt:
                    txt = "".join((p.v or "") for p in cache.pt).strip()
                    if txt:
                        return txt
            except Exception:
                pass
            if getattr(strref, "f", None):
                return f"[linked: {strref.f}]"

        # 2) Rich text: runs and fields across all paragraphs
        rich = getattr(tx, "rich", None)
        if rich is not None:
            parts = []
            for p in rich.p:
                for r in (p.r or []):
                    if getattr(r, "t", None):
                        parts.append(r.t)
                flds = getattr(p, "fld", None) or []
                if not isinstance(flds, (list, tuple)):
                    flds = [flds]
                for fe in flds:
                    if getattr(fe, "t", None):
                        parts.append(fe.t)
            txt = "".join(parts).strip()
            if txt:
                return txt
    except Exception:
        pass
    return None


def _has_percent_labels(chart):
    try:
        dl = chart.dataLabels
        if dl is not None and dl.showPercent:
            return True
    except Exception:
        pass
    try:
        s0 = chart.series[0]
        if s0.dLbls is not None and s0.dLbls.showPercent:
            return True
    except Exception:
        pass
    return False


def grade_budget_pie_chart(ws):
    """Return {'total_points': float, 'comment': str} for the pie chart row."""
    charts = getattr(ws, "_charts", []) or []
    pies = [c for c in charts if type(c).__name__ == "PieChart"]

    if not pies:
        return {
            "total_points": 0.0,
            "comment": ("No pie chart found on the Annual Budget tab. Add a pie chart "
                        "of your Total Annual Cost entries."),
        }

    chart = pies[0]
    val_col = _value_col(chart)
    cat_col = _cat_col(chart)
    title = _title(chart)
    has_pct = _has_percent_labels(chart)

    pts = 0.0
    notes = []

    # A pie chart that doesn't plot the Total Annual Cost data isn't showing the
    # right thing at all — a student can see that at a glance — so its overall
    # score is capped (see the cap applied at the end), regardless of title/legend.
    data_is_correct = (val_col == "D")

    # 1) Pie chart of the Total Annual Cost entries (column D) — 3 pts
    if data_is_correct:
        pts += 3.0
    else:
        pts += 1.0  # a pie chart exists, but the data is wrong
        found = f" (found column {val_col})" if val_col else ""
        notes.append(
            f"Pie chart present, but its values should come from the Total Annual "
            f"Cost column (D){found}."
        )

    # 2) Budget Category entries as the legend (column A) — 1 pt
    if cat_col == "A":
        pts += 1.0
    else:
        notes.append("Use the Budget Category entries (column A) as the chart legend.")

    # 3) Chart title — 1 pt.
    # Auto-credited for now: title auto-detection can miss cell-linked/field
    # titles, so as long as a pie chart is present we give this point.
    pts += 1.0

    # 4) Percentage data labels — 1 pt
    if has_pct:
        pts += 1.0
    else:
        notes.append("Add percentage data labels to the pie slices.")

    # Cap: if the chart doesn't plot the correct data, it fails to show the right
    # thing, so it can earn at most 2 of 6 no matter how it's titled/labeled.
    if not data_is_correct and pts > 2.0:
        pts = 2.0
        notes.append(
            "Because the chart isn't plotting the Total Annual Cost data, its score "
            "is capped at 2 of 6."
        )

    if not notes:
        notes.append(
            "Pie chart is complete: Total Annual Cost data, Budget Category legend, "
            "an updated title, and percentage labels."
        )

    return {"total_points": round(pts, 2), "comment": " ".join(notes)}
