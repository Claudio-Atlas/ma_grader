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
    
    # Chart exists and is bar type - 1 point
    score += 1.0
    feedback.append(("HIST_FOUND", {}))
    
    # Check data ranges
    if hasattr(bar_chart, 'series') and bar_chart.series:
        series = bar_chart.series[0]
        values_ok, categories_ok, values_ref, categories_ref = _check_data_range(series)
        
        # Values (Frequency) - 2 points
        if values_ok:
            score += 2.0
            feedback.append(("HIST_DATA_OK", {}))
        else:
            if values_ref:
                feedback.append(("HIST_DATA_WRONG", {}))
            else:
                feedback.append(("HIST_DATA_MISSING", {}))
        
        # Categories (Title of Bin) - 1 point
        if categories_ok:
            score += 1.0
            feedback.append(("HIST_LABELS_OK", {}))
        else:
            if categories_ref:
                feedback.append(("HIST_LABELS_WRONG", {}))
            else:
                feedback.append(("HIST_LABELS_MISSING", {}))
    else:
        feedback.append(("HIST_DATA_MISSING", {}))
        feedback.append(("HIST_LABELS_MISSING", {}))
    
    # Check chart title - 1 point
    chart_title = _extract_title_text(bar_chart.title)
    if chart_title and chart_title.strip():
        score += 1.0
        feedback.append(("HIST_TITLE_OK", {"title": chart_title}))
    else:
        feedback.append(("HIST_TITLE_MISSING", {}))
    
    # Check axis titles - 0.5 each
    x_title = None
    y_title = None
    
    if hasattr(bar_chart, 'x_axis') and bar_chart.x_axis:
        x_title = _extract_title_text(bar_chart.x_axis.title)
    
    if hasattr(bar_chart, 'y_axis') and bar_chart.y_axis:
        y_title = _extract_title_text(bar_chart.y_axis.title)
    
    # X-axis should be bins/categories, NOT "Frequency"
    # "Frequency" on X-axis is a common mistake (swapped axes)
    if x_title and x_title.strip():
        x_title_lower = x_title.strip().lower()
        if "frequency" in x_title_lower or "freq" == x_title_lower:
            # Wrong - "Frequency" should be on Y-axis, not X-axis
            feedback.append(("HIST_XAXIS_WRONG", {
                "title": x_title,
                "reason": "X-axis should show bin labels, not 'Frequency'"
            }))
        else:
            score += 0.5
            feedback.append(("HIST_XAXIS_OK", {"title": x_title}))
    else:
        feedback.append(("HIST_XAXIS_MISSING", {}))
    
    # Y-axis should be "Frequency" or similar
    if y_title and y_title.strip():
        score += 0.5
        feedback.append(("HIST_YAXIS_OK", {"title": y_title}))
    else:
        feedback.append(("HIST_YAXIS_MISSING", {}))
    
    # Round score
    score = round(score, 2)
    
    # Add summary
    if score == 6.0:
        feedback = [("HIST_ALL_CORRECT", {})]
    else:
        criteria_met = int(score)
        feedback.insert(0, ("HIST_PARTIAL", {"correct": criteria_met}))
    
    return score, feedback
