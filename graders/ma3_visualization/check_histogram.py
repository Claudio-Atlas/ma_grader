"""
check_histogram.py — Validates histogram/bar chart on Visualization tab

Grading: 6 points total
    - 1 pt: Chart exists and is bar chart type
    - 2 pts: Chart uses correct data (Frequency column G)
    - 1 pt: Chart uses correct labels (Title of Bin column F)
    - 1 pt: Chart has title
    - 1 pt: Chart has X and Y axis titles (0.5 each)
"""

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


def _extract_title_text(title_obj) -> Optional[str]:
    """Extract readable text from chart title object."""
    if title_obj is None:
        return None
    
    try:
        if hasattr(title_obj, 'tx') and title_obj.tx:
            if hasattr(title_obj.tx, 'rich') and title_obj.tx.rich:
                texts = []
                for p in title_obj.tx.rich.p:
                    if hasattr(p, 'r'):
                        for r in p.r:
                            if hasattr(r, 't') and r.t:
                                texts.append(r.t)
                return ''.join(texts) if texts else None
    except Exception:
        pass
    
    return str(title_obj) if title_obj else None


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
    
    # Check if values reference column G (Frequency)
    if values_ref:
        values_ref_upper = values_ref.upper()
        # Should reference column G, rows around 28-38
        if "$G$" in values_ref_upper or "!G" in values_ref_upper or "'G" in values_ref_upper:
            if "28" in values_ref or "38" in values_ref:
                values_ok = True
        # Also accept without sheet prefix
        if values_ref_upper.startswith("G") or "!$G" in values_ref_upper:
            values_ok = True
    
    # Check if categories reference column F (Title of Bin)
    if categories_ref:
        categories_ref_upper = categories_ref.upper()
        if "$F$" in categories_ref_upper or "!F" in categories_ref_upper or "'F" in categories_ref_upper:
            if "28" in categories_ref or "38" in categories_ref:
                categories_ok = True
        if categories_ref_upper.startswith("F") or "!$F" in categories_ref_upper:
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
    chart_title = _extract_title_text(bar_chart.title)
    if _is_placeholder_title(chart_title):
        if chart_title and chart_title.strip():
            feedback.append(("HIST_TITLE_PLACEHOLDER", {"title": chart_title}))
        else:
            feedback.append(("HIST_TITLE_MISSING", {}))
    else:
        score += 0.5
        feedback.append(("HIST_TITLE_OK", {"title": chart_title}))

    # ---- (6) X-axis (valid, not placeholder / not "Frequency") + Y-axis — 0.5 each
    x_title = _extract_title_text(bar_chart.x_axis.title) if getattr(bar_chart, 'x_axis', None) else None
    y_title = _extract_title_text(bar_chart.y_axis.title) if getattr(bar_chart, 'y_axis', None) else None

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
