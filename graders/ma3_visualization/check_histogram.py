"""
check_histogram.py — Validates histogram/bar chart on Visualization tab

Grading: 6 points total
    - 1 pt: Chart exists and is bar chart type
    - 2 pts: Chart uses correct data (Frequency column G)
    - 1 pt: Chart uses correct labels (Title of Bin column F)
    - 1 pt: Chart has title
    - 1 pt: Chart has X and Y axis titles (0.5 each)
"""

import re
from typing import Tuple, List, Optional
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.chart import BarChart


_TITLE_PLACEHOLDERS = (
    "title", "chart title", "axis title", "axis title 1",
    "title of bin", "title of the bin", "title of bins",
)


def _is_placeholder_title(text: Optional[str]) -> bool:
    """True if the title is empty or one of Excel's default placeholder strings
    (or the assignment's 'Title of Bin' label), which shouldn't earn credit."""
    if not text or not text.strip():
        return True
    s = text.strip().lower()
    if s in _TITLE_PLACEHOLDERS:
        return True
    if "title of" in s:  # "Title of the bin", "Title of Bins", etc.
        return True
    return False


def _extract_title_text(title_obj, sheet: Optional[Worksheet] = None) -> Optional[str]:
    """Readable text of a chart/axis title, or None.

    Titles are either typed (rich text) or LINKED to a cell (=Visualization!$F$27).
    A linked title's text comes from the chart's cached copy, or from the cell
    itself. (Previously a linked title fell through to the object's debug string,
    which never looked like a placeholder, so "Title of the Bin" got credit.)
    """
    if title_obj is None:
        return None
    tx = getattr(title_obj, "tx", None)
    try:
        # Linked to a cell? (Checked first: openpyxl also attaches an empty
        # rich-text block to linked titles.)
        ref = getattr(tx, "strRef", None) if tx is not None else None
        if ref is not None:
            cache = getattr(ref, "strCache", None)
            pts = getattr(cache, "pt", None) if cache is not None else None
            if pts:
                text = "".join(str(pt.v) for pt in pts if getattr(pt, "v", None) is not None)
                if text:
                    return text
            if sheet is not None and getattr(ref, "f", None):
                cell = str(ref.f).split("!")[-1].replace("$", "")
                value = sheet[cell].value
                return str(value) if value not in (None, "") else None

        if tx is not None and getattr(tx, "rich", None):
            texts = []
            for p in tx.rich.p:
                for r in (getattr(p, "r", None) or []):
                    if getattr(r, "t", None):
                        texts.append(r.t)
                for fld in (getattr(p, "fld", None) or []):
                    if getattr(fld, "t", None):
                        texts.append(fld.t)
            return "".join(texts) if texts else None
    except Exception:
        pass
    return None


def _cols_in_ref(ref) -> set:
    """Return the set of column letters referenced in a chart range string,
    e.g. "'Visualization'!$G$28:$G$38" -> {"G"}."""
    if not ref:
        return set()
    body = str(ref).split("!")[-1]  # drop sheet prefix
    return {m.group(1).upper() for m in re.finditer(r'\$?([A-Za-z]{1,3})\$?\d+', body)}


def _check_data_range(series) -> Tuple[bool, bool, str, str]:
    """
    Check if chart series uses correct data ranges.
    
    Returns:
        Tuple of (values_ok, categories_ok, values_ref, categories_ref)
    """
    values_ref = None
    categories_ref = None
    values_ok = False
    categories_ok = False
    
    try:
        # Get values reference (should be Frequency column G)
        if hasattr(series, 'val') and series.val:
            if hasattr(series.val, 'numRef') and series.val.numRef:
                values_ref = series.val.numRef.f
        
        # Get categories reference (should be Title of Bin column F)
        if hasattr(series, 'cat') and series.cat:
            if hasattr(series.cat, 'numRef') and series.cat.numRef:
                categories_ref = series.cat.numRef.f
            elif hasattr(series.cat, 'strRef') and series.cat.strRef:
                categories_ref = series.cat.strRef.f
    except Exception:
        pass
    
    # Values may reference the Frequency column (G) OR the Relative Frequency
    # column (H) — a relative-frequency histogram is equally valid.
    values_cols = _cols_in_ref(values_ref)
    if values_cols & {"G", "H"}:
        values_ok = True

    # Category labels should reference the Title of Bin column (F).
    if "F" in _cols_in_ref(categories_ref):
        categories_ok = True
    
    return values_ok, categories_ok, values_ref or "", categories_ref or ""


def check_histogram(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check histogram/bar chart on Visualization tab.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    score = 0.0
    
    # Check if any charts exist
    charts = sheet._charts
    
    if not charts or len(charts) == 0:
        feedback.append(("HIST_MISSING", {}))
        return 0.0, feedback
    
    # Find the bar chart
    bar_chart = None
    for chart in charts:
        if isinstance(chart, BarChart):
            bar_chart = chart
            break
        # Also check chart type attribute
        if hasattr(chart, 'type') and chart.type in ['col', 'bar']:
            bar_chart = chart
            break
    
    if bar_chart is None:
        # Found chart but not bar type
        feedback.append(("HIST_WRONG_TYPE", {}))
        return 0.0, feedback
    
    # ---- (1) A bar/column chart exists — 1.0 -------------------------------
    score += 1.0
    feedback.append(("HIST_FOUND", {}))

    # ---- (2) Values = Frequency (G) 2.0  /  (3) Categories = Bin titles (F) 1.0
    values_ok = categories_ok = False
    if hasattr(bar_chart, 'series') and bar_chart.series:
        series = bar_chart.series[0]
        values_ok, categories_ok, values_ref, categories_ref = _check_data_range(series)

        if values_ok:
            score += 2.0
            feedback.append(("HIST_DATA_OK", {}))
        else:
            feedback.append(("HIST_DATA_WRONG", {}) if values_ref else ("HIST_DATA_MISSING", {}))

        if categories_ok:
            score += 1.0
            feedback.append(("HIST_LABELS_OK", {}))
        else:
            feedback.append(("HIST_LABELS_WRONG", {}) if categories_ref else ("HIST_LABELS_MISSING", {}))
    else:
        feedback.append(("HIST_DATA_MISSING", {}))
        feedback.append(("HIST_LABELS_MISSING", {}))

    # ---- (4) Gap width = 0% (histogram, not a gapped bar chart) — 0.5 -------
    # openpyxl exposes the bar spacing as gapWidth (Excel default 150). A true
    # histogram has touching bars, i.e. gapWidth == 0.
    gap_width = getattr(bar_chart, "gapWidth", None)
    if gap_width == 0:
        score += 0.5
        feedback.append(("HIST_GAP_OK", {}))
    else:
        feedback.append(("HIST_GAP_WRONG", {"gap": gap_width if gap_width is not None else "not 0%"}))

    # ---- (5) Chart title present and not a placeholder — 0.5 ---------------
    chart_title = _extract_title_text(bar_chart.title, sheet)
    if _is_placeholder_title(chart_title):
        if chart_title and chart_title.strip():
            feedback.append(("HIST_TITLE_PLACEHOLDER", {"title": chart_title}))
        else:
            feedback.append(("HIST_TITLE_MISSING", {}))
    else:
        score += 0.5
        feedback.append(("HIST_TITLE_OK", {"title": chart_title}))

    # ---- (6) X-axis (valid, not placeholder / not "Frequency") + Y-axis — 0.5 each
    x_title = _extract_title_text(bar_chart.x_axis.title, sheet) if getattr(bar_chart, 'x_axis', None) else None
    y_title = _extract_title_text(bar_chart.y_axis.title, sheet) if getattr(bar_chart, 'y_axis', None) else None

    if not x_title or not x_title.strip():
        feedback.append(("HIST_XAXIS_MISSING", {}))
    elif "frequency" in x_title.strip().lower():
        # "Frequency" belongs on the Y-axis (swapped-axes mistake).
        feedback.append(("HIST_XAXIS_WRONG", {
            "title": x_title, "reason": "The X-axis should show the bin labels, not 'Frequency'."}))
    elif _is_placeholder_title(x_title):
        feedback.append(("HIST_XAXIS_WRONG", {
            "title": x_title, "reason": "This is a placeholder label — name the data, e.g. 'Change in Scores'."}))
    else:
        score += 0.5
        feedback.append(("HIST_XAXIS_OK", {"title": x_title}))

    if y_title and y_title.strip():
        score += 0.5
        feedback.append(("HIST_YAXIS_OK", {"title": y_title}))
    else:
        feedback.append(("HIST_YAXIS_MISSING", {}))

    # ---- Gate: a chart that doesn't plot the Frequency data can't be a correct
    # histogram, so cap the total at 2.0 no matter how well it's labeled. --------
    core_data_ok = values_ok
    score = round(score, 2)
    if not core_data_ok and score > 2.0:
        score = 2.0
        feedback.append(("HIST_CAPPED", {}))

    # Summary
    if score == 6.0:
        feedback = [("HIST_ALL_CORRECT", {})]
    else:
        feedback.insert(0, ("HIST_PARTIAL", {"correct": round(score, 2)}))

    return score, feedback
